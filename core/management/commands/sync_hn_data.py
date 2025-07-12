import platform
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

import boto3
import requests
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.management.base import BaseCommand

from ask_hn_digest.utils import get_ask_hn_digest_logger

logger = get_ask_hn_digest_logger(__name__)

# How much of the end of the S3 file to download to get the last known ID.
# 10MB should be more than enough for the 1000-line trim overlap.
TAIL_SIZE_BYTES = 10 * 1024 * 1024
BULK_CHUNK_SIZE = 15_000
TEST_MODE_TOTAL_LIMIT = 20_000


class Command(BaseCommand):
    help = "Efficiently syncs Hacker News data to an S3 bucket using multipart upload."

    def add_arguments(self, parser):
        parser.add_argument(
            "--test",
            action="store_true",
            help=f"""
            Run in test mode.
            When used with --bulk, it processes {TEST_MODE_TOTAL_LIMIT} items in chunks.
            Otherwise, it syncs {TEST_MODE_TOTAL_LIMIT} items in one go.
            """,
        )
        parser.add_argument(
            "--bulk",
            action="store_true",
            help=f"""
            Run in bulk-sync mode, fetching and uploading in chunks of {BULK_CHUNK_SIZE} items.
            Ideal for initial sync.
            """,
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.s3_bucket = settings.STORAGES["default"]["OPTIONS"]["bucket_name"]
        self.s3_key = "full.json"
        self.temp_dir = None
        self.local_tail_file = None
        self.hn_tool_dir = Path("bin")
        self.hn_tool_path = self.hn_tool_dir / "hn"
        self.s3_client = self.get_s3_client()
        self.test_mode = False
        self.bulk_mode = False

    def handle(self, *args, **options):
        self.test_mode = options["test"]
        self.bulk_mode = options["bulk"]

        # This will be used to keep track of the number of items synced
        # in bulk mode.
        self._items_so_far_bulk_mode = 0

        self.temp_dir = Path(tempfile.mkdtemp())
        self.local_tail_file = self.temp_dir / "tail.json"

        if self.bulk_mode and self.test_mode:
            logger.warning(
                f"""
                Running in BULK TEST mode.
                Syncing {TEST_MODE_TOTAL_LIMIT} items in chunks of {BULK_CHUNK_SIZE}.
                """
            )
        elif self.bulk_mode:
            logger.warning(f"Running in BULK mode. Syncing in chunks of {BULK_CHUNK_SIZE}.")
        elif self.test_mode:
            logger.warning(f"Running in TEST mode. Will only sync {TEST_MODE_TOTAL_LIMIT} items.")

        logger.info("Starting efficient Hacker News data sync...")

        self.install_hn_tool()

        if self.bulk_mode:
            self.run_bulk_sync()
        else:
            original_s3_size, _ = self.download_s3_tail()

            if original_s3_size == 0:
                logger.info("S3 file is empty. Performing initial full sync.")
                # Pass test limit if specified
                self.sync_hn_data(limit=TEST_MODE_TOTAL_LIMIT if self.test_mode else None)
                self.upload_to_s3(self.local_tail_file)
            else:
                logger.info(f"Original S3 object size: {original_s3_size} bytes")
                self.sync_hn_data(limit=TEST_MODE_TOTAL_LIMIT if self.test_mode else None)
                self.perform_multipart_append(original_s3_size)

        self.cleanup()

        logger.info("Efficient sync complete!")

    def run_bulk_sync(self):
        logger.info("Starting bulk sync process...")
        chunk_size = BULK_CHUNK_SIZE
        test_mode_total_limit = TEST_MODE_TOTAL_LIMIT if self.test_mode else None

        # Get the initial state from S3.
        original_s3_size, self._items_so_far_bulk_mode = self.download_s3_tail()

        # In bulk mode, we always start by appending to what's already there.
        # If the S3 file was not empty, we perform a multipart append.
        # Otherwise, the first chunk will be a direct upload.
        is_initial_chunk = original_s3_size == 0

        while True:
            # 1. Determine the cumulative target for this run.
            cumulative_target = self._items_so_far_bulk_mode + chunk_size

            if test_mode_total_limit:
                if self._items_so_far_bulk_mode >= test_mode_total_limit:
                    logger.info("Test mode item limit reached.")
                    break
                # Cap the target at the total limit for the final chunk.
                if cumulative_target > test_mode_total_limit:
                    cumulative_target = test_mode_total_limit

            logger.info(
                f"""
                --- Starting new bulk chunk (aiming for total of {cumulative_target} items) ---
                """
            )

            # 2. Run the sync with the CUMULATIVE target.
            more_items_exist = self.sync_hn_data(limit=cumulative_target)

            # 3. Upload the result.
            if is_initial_chunk:
                self.upload_to_s3(self.local_tail_file)
                is_initial_chunk = False  # Subsequent uploads will be multipart appends
            else:
                # We need the S3 object size from *before* this chunk's additions.
                self.perform_multipart_append(original_s3_size)

            # 4. Update state for the next loop.
            # We must know the new S3 size and local item count for the next append.
            original_s3_size, self._items_so_far_bulk_mode = self.download_s3_tail()

            # 5. Check for exit conditions.
            if not more_items_exist:
                logger.info("hn tool reported no more items. Bulk sync is complete.")
                break

        logger.info("Bulk sync process finished.")

    def perform_multipart_append(self, original_size):
        """
        Appends the local tail file to the S3 object using a multipart
        upload and copy, avoiding a full download/upload.
        """
        logger.info("Performing multipart append on S3...")
        local_tail_path = Path(self.local_tail_file)
        # We need to re-check the local file size right before upload.
        if not local_tail_path.exists():
            logger.info("Local file is empty, skipping append.")
            return

        new_tail_size = local_tail_path.stat().st_size

        # The head is the original file minus the part we downloaded and will replace.
        head_size = original_size - TAIL_SIZE_BYTES
        if head_size < 0:
            head_size = 0  # This happens if the original was smaller than TAIL_SIZE_BYTES

        mpu = self.s3_client.create_multipart_upload(Bucket=self.s3_bucket, Key=self.s3_key)
        upload_id = mpu["UploadId"]
        parts = []

        try:
            # Part 1: Copy the head from the existing S3 object.
            if head_size > 5 * 1024 * 1024:  # S3 requires parts to be at least 5MB for copy
                logger.info(f"Copying head ({head_size} bytes) on S3...")
                copy_source = {"Bucket": self.s3_bucket, "Key": self.s3_key}
                copy_range = f"bytes=0-{head_size - 1}"
                part1 = self.s3_client.upload_part_copy(
                    Bucket=self.s3_bucket,
                    Key=self.s3_key,
                    PartNumber=1,
                    UploadId=upload_id,
                    CopySource=copy_source,
                    CopySourceRange=copy_range,
                )
                parts.append({"PartNumber": 1, "ETag": part1["CopyPartResult"]["ETag"]})
            else:  # If head is too small, just upload the whole thing
                self.upload_to_s3(self.local_tail_file)
                return

            # Part 2: Upload the new tail from our local machine.
            logger.info(f"Uploading new tail ({new_tail_size} bytes)...")
            with open(local_tail_path, "rb") as f:
                part2 = self.s3_client.upload_part(
                    Bucket=self.s3_bucket,
                    Key=self.s3_key,
                    PartNumber=2,
                    UploadId=upload_id,
                    Body=f,
                )
            parts.append({"PartNumber": 2, "ETag": part2["ETag"]})

            # Complete the multipart upload
            logger.info("Completing multipart upload...")
            self.s3_client.complete_multipart_upload(
                Bucket=self.s3_bucket,
                Key=self.s3_key,
                UploadId=upload_id,
                MultipartUpload={"Parts": parts},
            )

        except ClientError as e:
            logger.error(f"Multipart append failed: {e}", exc_info=True)
            self.s3_client.abort_multipart_upload(
                Bucket=self.s3_bucket, Key=self.s3_key, UploadId=upload_id
            )
            exit(1)

    def download_s3_tail(self) -> (int, int):
        """
        Downloads the last part of the S3 object.
        Returns a tuple of (total_size_in_bytes, number_of_lines).
        """
        try:
            meta = self.s3_client.head_object(Bucket=self.s3_bucket, Key=self.s3_key)
            total_size = meta["ContentLength"]

            if total_size == 0:
                Path(self.local_tail_file).touch()
                return 0, 0

            # Range header for the last N bytes
            range_header = f"bytes=-{TAIL_SIZE_BYTES}"
            logger.info(f"Downloading tail of S3 object (range: {range_header})...")
            response = self.s3_client.get_object(
                Bucket=self.s3_bucket, Key=self.s3_key, Range=range_header
            )

            with open(self.local_tail_file, "wb") as f:
                body = response["Body"].read()
                f.write(body)

            line_count = len(body.splitlines())

            # Now, for bulk sync, we need the *full* count.
            # We'll use a separate call to avoid slowing down the main path.
            # This is a bit inefficient but necessary for correct limit calculation.
            if self.bulk_mode:
                return total_size, self._get_total_line_count()
            else:
                return total_size, line_count

        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                logger.info("S3 object not found. Starting fresh.")
                Path(self.local_tail_file).touch()
                return 0, 0
            if e.response["Error"]["Code"] == "416":
                logger.info("File is smaller than tail size, downloading full file.")
                self.s3_client.download_file(self.s3_bucket, self.s3_key, str(self.local_tail_file))
                size = Path(self.local_tail_file).stat().st_size
                lines = len(Path(self.local_tail_file).read_text().splitlines())
                return size, lines
            else:
                logger.error(f"Failed to download from S3: {e}", exc_info=True)
                exit(1)
        return 0, 0

    def _get_total_line_count(self) -> int:
        """
        Efficiently counts the total number of lines in the S3 object.
        """
        logger.info("Calculating total line count from S3 object...")
        count = 0
        try:
            response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=self.s3_key)
            # Read in chunks to avoid loading the whole file into memory
            for _ in response["Body"].iter_lines():
                count += 1
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return 0  # File doesn't exist, so count is 0
            logger.error(f"Could not get line count from S3: {e}", exc_info=True)
            return 0  # Return 0 on error to be safe
        logger.info(f"Total line count is {count}")
        return count

    def get_s3_client(self):
        """Initializes and returns an S3 client."""
        return boto3.client(
            "s3",
            aws_access_key_id=settings.STORAGES["default"]["OPTIONS"]["access_key"],
            aws_secret_access_key=settings.STORAGES["default"]["OPTIONS"]["secret_key"],
            region_name=settings.STORAGES["default"]["OPTIONS"]["region_name"],
            endpoint_url=settings.STORAGES["default"]["OPTIONS"]["endpoint_url"],
        )

    def upload_to_s3(self, file_path):
        logger.info(f"Uploading updated data to s3://{self.s3_bucket}/{self.s3_key}...")
        try:
            self.s3_client.upload_file(str(file_path), self.s3_bucket, self.s3_key)
            logger.info("Upload complete.")
        except ClientError as e:
            logger.error(f"Failed to upload to S3: {e}", exc_info=True)
            exit(1)

    def cleanup(self):
        logger.info("Cleaning up local files...")
        try:
            if self.temp_dir and self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
            if self.hn_tool_dir.exists():
                shutil.rmtree(self.hn_tool_dir)
            logger.info("Cleanup complete.")
        except OSError as e:
            logger.error(f"Error during cleanup: {e}", exc_info=True)

    def trim_local_file(self):
        # This function is no longer needed as the resume logic is handled
        # by the cumulative limit and the -c- flag in the hn tool.
        pass

    def sync_hn_data(self, limit=None) -> bool:
        """
        Runs the hn scan command.
        Returns a boolean indicating if more items may exist.
        """
        logger.info(f"Syncing Hacker News data to {self.local_tail_file}...")
        try:
            tool_path = str(self.hn_tool_path.resolve())
            command = [
                tool_path,
                "scan",
                "--no-cache",
                "--asc",
                "-c-",
                "-o",
                str(self.local_tail_file),
            ]
            if limit:
                command.extend(["--limit", str(limit)])

            process = subprocess.Popen(
                command,
                stderr=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            no_new_items_found = False
            stderr_lines = []
            if process.stderr:
                for line in iter(process.stderr.readline, ""):
                    self.stdout.write(line)  # Show progress bar to user
                    stderr_lines.append(line)
                    if "no new items" in line.lower():
                        no_new_items_found = True

            process.wait()

            if no_new_items_found:
                logger.info("No new items to sync.")
                return False

            if process.returncode != 0:
                logger.error(
                    f"Error syncing HN data. Return Code: {process.returncode}",
                    extra={"stderr": "".join(stderr_lines)},
                )
                exit(1)

            return True

        except FileNotFoundError:
            logger.error(f"Error: The command '{tool_path}' was not found.", exc_info=True)
            exit(1)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error syncing HN data: {e.stderr}", exc_info=True)
            exit(1)

    def install_hn_tool(self):
        if self.hn_tool_path.exists():
            return

        logger.info("Installing hn tool...")
        self.hn_tool_dir.mkdir(parents=True, exist_ok=True)

        os_name = platform.system().lower()
        arch = platform.machine()
        if arch == "x86_64":
            arch = "amd64"
        elif arch in ("aarch64", "arm64"):
            arch = "arm64"

        url = f"https://github.com/jasonthorsness/unlurker/releases/latest/download/hn_{os_name}_{arch}.tar.gz"
        logger.info(f"Downloading from {url}")

        try:
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            with tarfile.open(fileobj=response.raw, mode="r:gz") as tar:
                tar.extractall(path=self.hn_tool_dir)
        except (OSError, requests.RequestException, tarfile.TarError) as e:
            logger.error(f"Failed to download or extract hn tool: {e}", exc_info=True)
            exit(1)

        if not self.hn_tool_path.exists():
            logger.error(f"Installation failed. Could not find hn binary at {self.hn_tool_path}")
            exit(1)

        logger.info("hn tool installed successfully.")
        self.hn_tool_path.chmod(0o755)
