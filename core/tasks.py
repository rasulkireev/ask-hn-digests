from django.conf import settings
import requests
from google import genai
import json
from django.utils.text import slugify

from ask_hn_digest.utils import get_ask_hn_digest_logger
from core.models import HNDiscussionSummary

logger = get_ask_hn_digest_logger(__name__)

gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)


def summarize_hn_discussion(discussion_id):
    """
    Summarize a Hacker News discussion by retrieving all comments and using an LLM to generate summaries.

    Args:
        discussion_id (int): The ID of the Hacker News discussion to summarize

    Returns:
        dict: A dictionary containing short_summary and long_summary of the discussion
    """
    # Get the main discussion data
    discussion_resp = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{discussion_id}.json")
    discussion_data = discussion_resp.json()

    if not discussion_data or "kids" not in discussion_data:
        return {"error": "Invalid discussion ID or no comments found"}

    title = discussion_data.get("title", "Untitled Discussion")
    original_post_text = discussion_data.get("text", "")
    comment_ids = discussion_data.get("kids", [])

    if settings.DEBUG:
        comment_ids = comment_ids[:50]

    comments_text = []
    for comment_id in comment_ids:
        comment_resp = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{comment_id}.json")
        comment_data = comment_resp.json()
        if comment_data and "text" in comment_data and not comment_data.get("deleted", False):
            comments_text.append(comment_data["text"])

    all_comments = "\n\n".join(comments_text)
    prompt = f"""Analyze the following Hacker News discussion and its comments.

    ---
    Title of the discussion:
    {title}

    Original post description:
    {original_post_text}

    Discussion comments:
    {all_comments[:50000]}  # Limit text length to avoid token limits
    ---

    Provide your analysis as a JSON object with the following keys:
    - "short_summary" (This summary will be featured in an email newsletter that includes a total of 7 summaries. It needs to be concise enough to fit well within this format, yet detailed enough to offer a meaningful understanding of the discussion. Highlight any useful tips, tricks, or productive arguments shared. The primary goal is to provide immediate value to the newsletter reader.)
    - "long_summary" (This summary will be published as a blog post on a website. It should be a more comprehensive version of the short_summary. Elaborate on the key themes, useful tips and tricks, insightful points, and any productive arguments from the discussion. The aim is to deliver significant value to someone reading it as a standalone piece. Don't start with a header/subheader. Do a text intro first, then add headers/subheader as you see fit.)
    - "title" (A concise, SEO-friendly blog post title for this discussion. Do not use generic titles. Make it specific and engaging. Do not use HN or Hacker News in the title.)
    - "slug" (A URL-friendly version of the title, lowercase, words separated by hyphens, no special characters, on the shorter side.)
    - "description" (A 1-2 sentence summary of the discussion, suitable for meta description tags. Should entice a reader to click and read the post.)
    - "tags" (A comma-separated list of tags for the blog post. Use the tags from the discussion and the comments.)

    IMPORTANT: All summaries and fields should be in valid markdown format where appropriate.
    IMPORTANT: Only return the JSON object, nothing else.
    IMPORTANT: Return your analysis as a JSON object with the following format:
    {{
      "short_summary": "Brief markdown summary here",
      "long_summary": "Detailed markdown summary here",
      "title": "SEO-friendly blog post title here",
      "slug": "url-friendly-slug-here",
      "description": "Meta description here"
    }}
    """

    response = gemini_client.models.generate_content(
        model="gemini-2.5-pro-preview-05-06",
        contents=prompt
    )
    summary_response = getattr(response, 'text', None)

    try:
        summary_data = json.loads(summary_response)
    except json.JSONDecodeError as jde:
        # Try to extract JSON from the response if possible
        import re
        match = re.search(r'\{.*\}', summary_response, re.DOTALL)
        if match:
            try:
                summary_data = json.loads(match.group(0))
            except Exception as e2:
                logger.error(f"Gemini response not valid JSON after extraction: {str(e2)} | Raw: {summary_response}")
                return {"error": f"Gemini response not valid JSON: {str(e2)}"}
        else:
            raise

    HNDiscussionSummary.objects.create(
        discussion_id=discussion_id,
        discussion_title=title,
        comment_ids=comment_ids,
        short_summary=summary_data.get("short_summary", ""),
        long_summary=summary_data.get("long_summary", ""),
        title=summary_data.get("title", title),
        slug=summary_data.get("slug", slugify(title)),
        description=summary_data.get("description", summary_data.get("long_summary", "")[:200]),
        tags=summary_data.get("tags", "")
    )

    return "Success"


def send_buttondown_newsletter(ids: list[int]):
    """
    Sends a Buttondown newsletter with summaries of the given HNDiscussionSummary ids.

    Args:
        ids (list[int]): List of HNDiscussionSummary ids to include in the newsletter
        subject (str, optional): The subject line for the email. If None, generates a subject like 'Ask HN Digest - 2025 Week 5'.
    Returns:
        dict: API response from Buttondown
    """
    from core.models import HNDiscussionSummary
    from datetime import datetime

    # Generate subject if not provided
    now = datetime.now()
    year, week_num, _ = now.isocalendar()
    subject = f"Ask HN Digest - {year} Week {week_num}"

    summaries = HNDiscussionSummary.objects.filter(discussion_id__in=ids)
    if not summaries.exists():
        logger.error(f"No HNDiscussionSummary objects found for ids: {ids}")
        raise

    # Compose the body
    body_lines = ["Here is this week's digest:\n"]
    for summary in summaries:
        body_lines.append(f"**{summary.discussion_title}**\n")
        body_lines.append(f"{summary.short_summary}\n")
        full_url = f"https://askhndigests.com{summary.get_absolute_url()}"
        body_lines.append(f"[Read more]({full_url})\n")
    body = "\n".join(body_lines)

    url = "https://api.buttondown.com/v1/emails"
    headers = {
        "Authorization": f"Token {settings.BUTTONDOWN_API_KEY}"
    }
    data = {
        "subject": subject,
        "body": body
    }

    response = requests.post(url, headers=headers, json=data)
    logger.info(f"Buttondown API response: {response.status_code} {response.text}")
    return response.json()


def send_buttondown_draft(email_id: str):
    """
    Sends a draft email via Buttondown to specified subscribers and recipients.

    Args:
        email_id (str): The ID of the Buttondown email draft to send.
        subscribers (list[str]): List of subscriber UUIDs to send the draft to.
        recipients (list[str]): List of email addresses to send the draft to.
    Returns:
        dict: API response from Buttondown
    """
    url = f"https://api.buttondown.com/v1/emails/{email_id}/send-draft"
    headers = {
        "Authorization": f"Token {settings.BUTTONDOWN_API_KEY}"
    }
    data = {
        "recipients": ["kireevr1996@gmail.com"]
    }

    response = requests.post(url, headers=headers, json=data)
    logger.info(f"Buttondown send-draft API response: {response.status_code} {response.text}")
    return response.json()
