import asyncio
import json
import time
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

import aiohttp
import psycopg2
from django.conf import settings

from ask_hn_digest.utils import get_ask_hn_digest_logger

logger = get_ask_hn_digest_logger(__name__)

try:
    import asyncpg

    HAS_ASYNCPG = True
except ImportError:
    import psycopg2
    import psycopg2.extras

    HAS_ASYNCPG = False
    logger.warning("asyncpg not available, falling back to psycopg2 (will be slower)")

if not HAS_ASYNCPG:
    import concurrent.futures
    from threading import Lock


class AsyncHackerNewsDB:
    """Hybrid async database operations - supports both asyncpg and psycopg2"""

    def __init__(self):
        """Initialize database connection"""
        self.DATABASE_URL = settings.HN_DB_URL
        self.pool = None
        self.sync_pool = None
        self.executor = None
        self.connection_lock = None

        if not HAS_ASYNCPG:
            self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)
            self.connection_lock = Lock()

    async def connect(self):
        """Establish database connection pool"""
        if HAS_ASYNCPG:
            await self._connect_asyncpg()
        else:
            await self._connect_psycopg2()

        await self.create_tables()

    async def _connect_asyncpg(self):
        """Connect using asyncpg"""
        parsed_url = urlparse(self.DATABASE_URL)

        try:
            # Use simpler connection settings to avoid compatibility issues
            self.pool = await asyncpg.create_pool(
                host=parsed_url.hostname,
                port=parsed_url.port or 5432,
                database=parsed_url.path[1:],
                user=parsed_url.username,
                password=parsed_url.password,
                min_size=5,
                max_size=20,
                command_timeout=30,
                server_settings={"application_name": "hn_fetcher"},
            )
            logger.info("✅ AsyncPG connection pool established!")

        except Exception as e:
            logger.info(f"❌ AsyncPG connection failed: {e}")
            logger.info("🔄 Falling back to psycopg2...")
            global HAS_ASYNCPG
            HAS_ASYNCPG = False
            import concurrent.futures
            from threading import Lock

            self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)
            self.connection_lock = Lock()
            await self._connect_psycopg2()

    async def _connect_psycopg2(self):
        """Connect using psycopg2 with thread pool"""

        def create_connection():
            parsed_url = urlparse(self.DATABASE_URL)
            return psycopg2.connect(
                host=parsed_url.hostname,
                port=parsed_url.port or 5432,
                database=parsed_url.path[1:],
                user=parsed_url.username,
                password=parsed_url.password,
            )

        # Test connection
        loop = asyncio.get_event_loop()
        test_conn = await loop.run_in_executor(self.executor, create_connection)
        test_conn.close()
        logger.info("✅ psycopg2 connection pool established!")

    async def create_tables(self):
        """Create tables if they don't exist"""
        create_sql = """
            CREATE TABLE IF NOT EXISTS hn_items (
                id BIGINT PRIMARY KEY,
                type VARCHAR(20),
                by_user VARCHAR(255),
                time_created TIMESTAMP,
                time_unix BIGINT,
                text TEXT,
                title TEXT,
                url TEXT,
                score INTEGER,
                parent_id BIGINT,
                poll_id BIGINT,
                descendants INTEGER,
                deleted BOOLEAN DEFAULT FALSE,
                dead BOOLEAN DEFAULT FALSE,
                kids INTEGER[],
                parts INTEGER[],
                raw_data JSONB,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """

        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_hn_items_type ON hn_items(type);",
            "CREATE INDEX IF NOT EXISTS idx_hn_items_by_user ON hn_items(by_user);",
            "CREATE INDEX IF NOT EXISTS idx_hn_items_time ON hn_items(time_created);",
            "CREATE INDEX IF NOT EXISTS idx_hn_items_parent ON hn_items(parent_id);",
            "CREATE INDEX IF NOT EXISTS idx_hn_items_fetched_at ON hn_items(fetched_at);",
        ]

        if HAS_ASYNCPG and self.pool:
            async with self.pool.acquire() as conn:
                await conn.execute(create_sql)
                for index_sql in indexes:
                    await conn.execute(index_sql)
        else:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self.executor, self._sync_create_tables, create_sql, indexes)

    def _sync_create_tables(self, create_sql: str, indexes: list[str]):
        """Synchronous table creation for psycopg2"""
        parsed_url = urlparse(self.DATABASE_URL)
        conn = psycopg2.connect(
            host=parsed_url.hostname,
            port=parsed_url.port or 5432,
            database=parsed_url.path[1:],
            user=parsed_url.username,
            password=parsed_url.password,
        )
        try:
            with conn.cursor() as cursor:
                cursor.execute(create_sql)
                for index_sql in indexes:
                    cursor.execute(index_sql)
                conn.commit()
        finally:
            conn.close()

    async def get_last_fetched_id(self) -> int:
        """Get the highest ID currently in database"""
        if HAS_ASYNCPG and self.pool:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval("SELECT MAX(id) FROM hn_items")
                return result if result else 0
        else:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(self.executor, self._sync_get_last_id)

    def _sync_get_last_id(self) -> int:
        """Synchronous version for psycopg2"""
        parsed_url = urlparse(self.DATABASE_URL)
        conn = psycopg2.connect(
            host=parsed_url.hostname,
            port=parsed_url.port or 5432,
            database=parsed_url.path[1:],
            user=parsed_url.username,
            password=parsed_url.password,
        )
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT MAX(id) FROM hn_items")
                result = cursor.fetchone()
                return result[0] if result and result[0] else 0
        finally:
            conn.close()

    async def batch_insert_items(self, items: list[dict[str, Any]]) -> int:
        """Insert multiple items at once for better performance"""
        if not items:
            return 0

        # Prepare data for batch insert
        records = []
        for item_data in items:
            if not item_data or "id" not in item_data:
                continue

            time_created = None
            time_unix = item_data.get("time")
            if time_unix:
                time_created = datetime.fromtimestamp(time_unix)

            record = (
                item_data["id"],
                item_data.get("type"),
                item_data.get("by"),
                time_created,
                time_unix,
                item_data.get("text"),
                item_data.get("title"),
                item_data.get("url"),
                item_data.get("score"),
                item_data.get("parent"),
                item_data.get("poll"),
                item_data.get("descendants"),
                item_data.get("deleted", False),
                item_data.get("dead", False),
                item_data.get("kids", []),
                item_data.get("parts", []),
                json.dumps(item_data),
            )
            records.append(record)

        if not records:
            return 0

        if HAS_ASYNCPG and self.pool:
            return await self._asyncpg_batch_insert(records)
        else:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(self.executor, self._psycopg2_batch_insert, records)

    async def _asyncpg_batch_insert(self, records: list[tuple]) -> int:
        """AsyncPG batch insert"""
        try:
            async with self.pool.acquire() as conn:
                await conn.copy_records_to_table(
                    "hn_items",
                    records=records,
                    columns=[
                        "id",
                        "type",
                        "by_user",
                        "time_created",
                        "time_unix",
                        "text",
                        "title",
                        "url",
                        "score",
                        "parent_id",
                        "poll_id",
                        "descendants",
                        "deleted",
                        "dead",
                        "kids",
                        "parts",
                        "raw_data",
                    ],
                    timeout=30,
                )
                return len(records)
        except Exception as e:
            logger.error(f"❌ Error with COPY, falling back to individual inserts: {e}")
            return await self._asyncpg_fallback_upsert(records)

    async def _asyncpg_fallback_upsert(self, records: list[tuple]) -> int:
        """AsyncPG fallback upsert"""
        success_count = 0
        async with self.pool.acquire() as conn:
            for record in records:
                try:
                    await conn.execute(
                        """
                        INSERT INTO hn_items (
                            id, type, by_user, time_created, time_unix, text, title, url,
                            score, parent_id, poll_id, descendants, deleted, dead,
                            kids, parts, raw_data, updated_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, CURRENT_TIMESTAMP)
                        ON CONFLICT (id) DO UPDATE SET
                            type = EXCLUDED.type,
                            by_user = EXCLUDED.by_user,
                            time_created = EXCLUDED.time_created,
                            time_unix = EXCLUDED.time_unix,
                            text = EXCLUDED.text,
                            title = EXCLUDED.title,
                            url = EXCLUDED.url,
                            score = EXCLUDED.score,
                            parent_id = EXCLUDED.parent_id,
                            poll_id = EXCLUDED.poll_id,
                            descendants = EXCLUDED.descendants,
                            deleted = EXCLUDED.deleted,
                            dead = EXCLUDED.dead,
                            kids = EXCLUDED.kids,
                            parts = EXCLUDED.parts,
                            raw_data = EXCLUDED.raw_data,
                            updated_at = CURRENT_TIMESTAMP
                    """,  # noqa: E501
                        *record,
                    )
                    success_count += 1
                except Exception as e:
                    logger.error(f"Error inserting item {record[0]}: {e}")
        return success_count

    def _psycopg2_batch_insert(self, records: list[tuple]) -> int:
        """psycopg2 batch insert using execute_values"""
        parsed_url = urlparse(self.DATABASE_URL)
        conn = psycopg2.connect(
            host=parsed_url.hostname,
            port=parsed_url.port or 5432,
            database=parsed_url.path[1:],
            user=parsed_url.username,
            password=parsed_url.password,
        )

        success_count = 0
        try:
            with conn.cursor() as cursor:
                # Use batch insert with psycopg2.extras.execute_values
                psycopg2.extras.execute_values(
                    cursor,
                    """
                    INSERT INTO hn_items (
                        id, type, by_user, time_created, time_unix, text, title, url,
                        score, parent_id, poll_id, descendants, deleted, dead,
                        kids, parts, raw_data, updated_at
                    ) VALUES %s
                    ON CONFLICT (id) DO UPDATE SET
                        type = EXCLUDED.type,
                        by_user = EXCLUDED.by_user,
                        time_created = EXCLUDED.time_created,
                        time_unix = EXCLUDED.time_unix,
                        text = EXCLUDED.text,
                        title = EXCLUDED.title,
                        url = EXCLUDED.url,
                        score = EXCLUDED.score,
                        parent_id = EXCLUDED.parent_id,
                        poll_id = EXCLUDED.poll_id,
                        descendants = EXCLUDED.descendants,
                        deleted = EXCLUDED.deleted,
                        dead = EXCLUDED.dead,
                        kids = EXCLUDED.kids,
                        parts = EXCLUDED.parts,
                        raw_data = EXCLUDED.raw_data,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    [record + (datetime.now(),) for record in records],
                    template=None,
                    page_size=1000,
                )
                conn.commit()
                success_count = len(records)
        except Exception as e:
            logger.error(f"❌ Error batch inserting with psycopg2: {e}")
            conn.rollback()
        finally:
            conn.close()

        return success_count

    async def close(self):
        """Close database connection pool"""
        if HAS_ASYNCPG and self.pool:
            await self.pool.close()
        elif self.executor:
            self.executor.shutdown(wait=True)


class AsyncHackerNewsClient:
    """Async client for fetching data from the Hacker News API"""

    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    def __init__(self, concurrent_requests: int = 100):
        """
        Initialize the async client

        Args:
            concurrent_requests: Number of concurrent requests to make
        """
        self.concurrent_requests = concurrent_requests
        self.semaphore = asyncio.Semaphore(concurrent_requests)

        # Configure session with connection pooling
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        connector = aiohttp.TCPConnector(
            limit=200,  # Total connection pool size
            limit_per_host=50,  # Max connections per host
            ttl_dns_cache=300,  # DNS cache TTL
            use_dns_cache=True,
        )

        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={"User-Agent": "HN-DB-Async-Fetcher/2.0 (High Performance)"},
        )

    async def get_max_item_id(self) -> int | None:
        """Get the current maximum item ID from HN API"""
        try:
            async with self.session.get(f"{self.BASE_URL}/maxitem.json") as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"❌ Error fetching max item ID: {e}")
            return None

    async def get_item(self, item_id: int) -> dict[str, Any] | None:
        """
        Get a single item by ID with rate limiting

        Args:
            item_id: The item ID to fetch

        Returns:
            Item data as dict, or None if item doesn't exist or error occurred
        """
        async with self.semaphore:  # Rate limiting
            try:
                async with self.session.get(f"{self.BASE_URL}/item/{item_id}.json") as response:
                    response.raise_for_status()
                    data = await response.json()
                    return data if data is not None else {}

            except Exception as e:
                logger.error(f"❌ Error fetching item {item_id}: {e}")
                return None

    async def get_items_batch(self, item_ids: list[int]) -> list[dict[str, Any]]:
        """
        Fetch multiple items concurrently

        Args:
            item_ids: List of item IDs to fetch

        Returns:
            List of item data dictionaries
        """
        tasks = [self.get_item(item_id) for item_id in item_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out None results and exceptions
        items = []
        for result in results:
            if isinstance(result, dict) and result:
                items.append(result)

        return items

    async def close(self):
        """Close the HTTP session"""
        await self.session.close()


class AsyncHackerNewsFetcher:
    """Main class to orchestrate the async fetching process"""

    def __init__(self, concurrent_requests: int = 100, batch_size: int = 1000):
        """
        Initialize the fetcher

        Args:
            concurrent_requests: Number of concurrent HTTP requests
            batch_size: Number of items to process in each batch
        """
        self.client = AsyncHackerNewsClient(concurrent_requests)
        self.db = AsyncHackerNewsDB()
        self.batch_size = batch_size
        self.concurrent_requests = concurrent_requests

    async def fetch_all_items(self, start_id: int | None = None, end_id: int | None = None):
        """
        Fetch all items from HN API and store in database using async processing

        Args:
            start_id: Item ID to start from (default: resume from last fetched)
            end_id: Item ID to end at (default: current max item ID)
        """
        logger.info("🚀 Starting async HackerNews data fetch...")

        # Initialize database connection
        try:
            await self.db.connect()
        except Exception as e:
            logger.info(f"❌ Failed to connect to database: {e}")
            return

        # Get max item ID from API
        if end_id is None:
            logger.info("🔍 Getting max item ID from HN API...")
            end_id = await self.client.get_max_item_id()
            if end_id is None:
                logger.info("❌ Could not get max item ID from API")
                return

        # Get starting point
        if start_id is None:
            logger.info("📍 Finding last fetched item...")
            try:
                last_fetched_id = await self.db.get_last_fetched_id()
                start_id = last_fetched_id + 1 if last_fetched_id else 1
                if last_fetched_id:
                    logger.info(
                        f"📌 Resuming from item {start_id:,} (last fetched: {last_fetched_id:,})"
                    )
                else:
                    logger.info("🆕 Starting fresh from item 1")
            except Exception as e:
                logger.info(f"⚠️  Could not get last fetched ID: {e}")
                start_id = 1

        logger.info(
            f"📊 Fetching items {start_id:,} to {end_id:,} ({end_id - start_id + 1:,} items)"
        )
        logger.info(
            f"⚡ Using {self.concurrent_requests} concurrent requests, batch size {self.batch_size}"
        )

        # Counters
        total_fetched = 0
        total_errors = 0
        total_batches = 0
        start_time = time.time()

        try:
            for batch_start in range(start_id, end_id + 1, self.batch_size):
                batch_end = min(batch_start + self.batch_size - 1, end_id)
                batch_ids = list(range(batch_start, batch_end + 1))
                total_batches += 1

                try:
                    # Fetch batch concurrently
                    batch_start_time = time.time()
                    items = await self.client.get_items_batch(batch_ids)
                    fetch_time = time.time() - batch_start_time

                    # Insert batch to database
                    db_start_time = time.time()
                    inserted_count = await self.db.batch_insert_items(items)
                    db_time = time.time() - db_start_time

                    total_fetched += inserted_count
                    total_errors += len(batch_ids) - len(items)

                    # Calculate performance metrics
                    ops_per_sec = len(batch_ids) / fetch_time if fetch_time > 0 else 0

                    logger.info(
                        f"🔍 Fetched {len(batch_ids)} items",
                        fetch_time=fetch_time,
                        inserted_count=inserted_count,
                        db_time=db_time,
                        ops_per_sec=ops_per_sec,
                    )

                except Exception as e:
                    logger.error(f"❌ Error processing batch {batch_start}-{batch_end}: {e}")
                    total_errors += len(batch_ids)
                    continue

        except KeyboardInterrupt:
            logger.info("\n⏸️  Fetch interrupted by user")

        finally:
            total_time = time.time() - start_time
            avg_ops_per_sec = total_fetched / total_time if total_time > 0 else 0
            logger.info("\n✅ Fetch completed!")
            logger.info(f"📈 Results: {total_fetched:,} items fetched, {total_errors:,} errors")
            logger.info(f"⚡ Average performance: {avg_ops_per_sec:.0f} items/second")
            logger.info(f"📦 Processed {total_batches} batches in {total_time:.1f}s")

    async def close(self):
        """Clean up resources"""
        await self.client.close()
        await self.db.close()


def get_ask_hn_story_ids(limit: int = 40) -> list[int]:
    """
    Get IDs of Ask HN stories from 7-14 days ago with good engagement (>5 comments)

    Args:
        limit: Maximum number of story IDs to return

    Returns:
        List of story IDs
    """
    try:
        parsed_url = urlparse(settings.HN_DB_URL)
        conn = psycopg2.connect(
            host=parsed_url.hostname,
            port=parsed_url.port or 5432,
            database=parsed_url.path[1:],
            user=parsed_url.username,
            password=parsed_url.password,
        )

        try:
            with conn.cursor() as cursor:
                query = """
                    SELECT id
                    FROM hn_items
                    WHERE
                        type = 'story'
                        AND title ILIKE 'Ask HN:%%'
                        AND descendants > 5
                        AND by_user NOT IN ('whoishiring', 'david927')
                        AND time_created >= CURRENT_DATE - INTERVAL '14 days'
                        AND time_created < CURRENT_DATE - INTERVAL '7 days'
                    ORDER BY descendants DESC
                    LIMIT %s;
                """

                cursor.execute(query, (limit,))
                rows = cursor.fetchall()
                story_ids = [row[0] for row in rows]

                return story_ids

        finally:
            conn.close()

    except Exception as e:
        logger.error("Error fetching Ask HN story IDs", error=str(e), limit=limit, exc_info=True)
        return []
