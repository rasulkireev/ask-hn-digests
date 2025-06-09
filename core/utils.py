from django.forms.utils import ErrorList
import requests
from datetime import datetime

from ask_hn_digest.utils import get_ask_hn_digest_logger
from google import genai
from django.conf import settings


logger = get_ask_hn_digest_logger(__name__)

HN_API_BASE_URL = "https://hacker-news.firebaseio.com/v0"

class DivErrorList(ErrorList):
    def __str__(self):
        return self.as_divs()

    def as_divs(self):
        if not self:
            return ""
        return f"""
            <div class="p-4 my-4 bg-red-50 rounded-md border border-red-600 border-solid">
              <div class="flex">
                <div class="flex-shrink-0">
                  <!-- Heroicon name: solid/x-circle -->
                  <svg class="w-5 h-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"> # noqa: E501
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" /> # noqa: E501
                  </svg>
                </div>
                <div class="ml-3 text-sm text-red-700">
                      {''.join([f'<p>{e}</p>' for e in self])}
                </div>
              </div>
            </div>
         """

def generate_buttondown_newsletter_subject(body: str):
    gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)

    """
    Generates a newsletter subject line using the Gemini API based on the email body.
    """
    prompt = f"""
    You are an expert copywriter specializing in email subject lines.
    Your task is to generate a killer subject line for a newsletter.

    The subject line must do two things:
    1. Hint at a benefit. For example, "How to get your first 10 sales (without a big list)" – clear benefit and it removes a mental obstacle.
    2. Create curiosity. For example, "THIS almost killed my launch" – What's "this"? What happened? Instant curiosity.

    Consider these 7 email subject line styles that consistently deliver higher open rates:
    1. Curiosity: "THIS changed everything for my business."
    2. Pain: "Still can't convert traffic into buyers?"
    3. Benefit: "How to 2X your leads in 30 days"
    4. Story: "I accidentally ordered d*ck cheese" (yes, deliverability took a hit. but replies went crazy.)
    5. Question: "Do you make these content mistakes?"
    6. Contrarian: "Why storytelling WON'T grow your brand (and what will)"
    7. Proof: "How I grew to 70,000 followers in one year"

    Use these to match your email type:
    - Sending a story? Use a story subject.
    - Giving advice? Use benefit or question.
    - Writing to sell? Use pain or proof.

    Mix them up. Shuffle them often. They never go stale.

    Here's what NOT to do:
    - Don't write "Newsletter #3" (instant death)
    - Don't ask boring yes/no questions that can be answered with a simple yes/no.
    - Don't try to be too clever (you are not Hemingway or ChatGPT).
    - Don't use bold or italic text.
    - Don't use markdown, just plain text.
    - Don't use links.
    - Don't use images.
    - Don't use videos.
    - Don't use hashtags.
    - Do use emojis where appropriate, but don't overdo it.

    The newsletter body is as follows:
    ---
    {body}
    ---

    Generate a single, compelling subject line based on the content and guidelines above.
    Only return the subject line, nothing else.
    """

    response = gemini_client.models.generate_content(
        model="gemini-2.5-pro-preview-05-06",  # Using model from user's example
        contents=prompt
    )
    subject = getattr(response, 'text', None)

    return subject.strip()

def get_item_data(item_id):
    """Fetches data for a given item ID from the Hacker News API."""
    try:
        response = requests.get(f"{HN_API_BASE_URL}/item/{item_id}.json")
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching item {item_id}: {e}")
        return None
    except ValueError as e: # Handles JSON decoding errors
        print(f"Error decoding JSON for item {item_id}: {e}")
        return None

def fetch_comments_recursive(comment_id, depth, all_ids_list, comment_texts_list):
    """
    Recursively fetches a comment and its children, including author and date.
    Appends comment IDs to all_ids_list and formatted text to comment_texts_list.
    """
    comment_data = get_item_data(comment_id)
    indentation = '    ' * depth

    if not comment_data:
        comment_texts_list.append(f"{indentation}[Error fetching comment {comment_id}]")
        return

    item_id_val = comment_data.get("id")
    if item_id_val is not None:
        all_ids_list.append(item_id_val)
    else:
        # This case should be rare for valid comment items from the API
        print(f"Warning: Fetched item (intended ID: {comment_id}) did not contain an 'id' field.")

    if comment_data.get("deleted"):
        comment_texts_list.append(f"{indentation}[comment deleted]")
        return
    if comment_data.get("dead"):
        comment_texts_list.append(f"{indentation}[comment dead]")
        return

    author = comment_data.get("by", "[unknown author]")
    unix_time = comment_data.get("time")
    readable_date = "[unknown date]"
    if unix_time:
        try:
            readable_date = datetime.fromtimestamp(unix_time).strftime('%Y-%m-%d %H:%M:%S')
        except TypeError:
            readable_date = "[invalid date format]"


    text = comment_data.get("text", "[No text for this comment]")
    # HTML entities will be preserved as they are from the API

    comment_texts_list.append(f"{indentation}{author} ({readable_date}): {text}")

    # Process child comments
    if "kids" in comment_data:
        for kid_id in comment_data["kids"]:
            fetch_comments_recursive(kid_id, depth + 1, all_ids_list, comment_texts_list)

def get_post_comments(post_id):
    """
    Retrieves all comment IDs and a formatted string of all comments (with author and date)
    for a given Hacker News post ID.

    Args:
        post_id (int): The ID of the Hacker News post.

    Returns:
        tuple: (list_of_comment_ids, formatted_comments_string)
               Returns ([], "Error or no comments message") on failure or no comments.
    """
    all_comment_ids = []
    formatted_comment_lines = []

    post_data = get_item_data(post_id)

    if not post_data:
        return [], f"Error: Could not fetch post {post_id} or post data is invalid."

    item_type = post_data.get("type")

    # A post (story, poll) has comments listed in its 'kids' attribute.
    if "kids" in post_data:
        for top_level_comment_id in post_data["kids"]:
            fetch_comments_recursive(top_level_comment_id, 0, all_comment_ids, formatted_comment_lines)
    elif item_type in ("story", "poll"): # These types should have 'descendants'
        descendants = post_data.get("descendants", 0)
        if descendants == 0:
             return [], "Post has no comments."
        else:
            # This case suggests an API inconsistency or an old item format
            # if 'descendants' > 0 but 'kids' is missing.
            return [], f"Post {post_id} (type: {item_type}) has {descendants} descendants but no 'kids' attribute in the top-level item data. Comments cannot be directly traversed."
    else:
        # For other item types (e.g., 'job', or a 'comment' ID passed as post_id without kids)
        return [], f"Post {post_id} (type: {item_type}) does not have comments listed under a 'kids' attribute or is not a type that typically has threaded comments in this manner."


    return all_comment_ids, "\n".join(formatted_comment_lines)
