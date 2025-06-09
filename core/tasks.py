from django.conf import settings
import requests
from google import genai
import json
from django.utils.text import slugify
from datetime import datetime, timedelta, timezone
from core.utils import generate_buttondown_newsletter_subject, get_post_comments
from django_q.tasks import async_task

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
        logger.error(
            "Invalid discussion ID or no comments found",
            discussion_id=discussion_id,
            discussion_data=discussion_data
        )
        raise

    title = discussion_data.get("title", "Untitled Discussion")
    original_post_text = discussion_data.get("text", "")

    comment_ids, comments_string = get_post_comments(discussion_id)
    prompt = f"""Analyze the following Hacker News discussion and its comments.

    ---
    Title of the discussion:
    {title}

    Original post description:
    {original_post_text}

    Discussion comments:
    {comments_string}  # Limit text length to avoid token limits
    ---

    Provide your analysis as a JSON object with the following keys:
    - "short_summary" (This summary will be featured in an email newsletter that includes a total of 7 summaries. It needs to be concise enough to fit well within this format, yet detailed enough to offer a meaningful understanding of the discussion. Highlight any useful tips, tricks, or productive arguments shared. The primary goal is to provide immediate value to the newsletter reader.)
    - "long_summary" (This summary will be published as a blog post on a website. It should be a more comprehensive version of the short_summary. Elaborate on the key themes, useful tips and tricks, insightful points, and any productive arguments from the discussion. The aim is to deliver significant value to someone reading it as a standalone piece. Don't start with a header/subheader. Do a text intro first, then add headers/subheader as you see fit.)
    - "title" (A concise, SEO-friendly blog post title for this discussion. Do not use generic titles. Make it specific and engaging. Do not use HN or Hacker News in the title.)
    - "slug" (A URL-friendly version of the title, lowercase, words separated by hyphens, no special characters, on the shorter side.)
    - "description" (A 1-2 sentence summary of the discussion, suitable for meta description tags. Should entice a reader to click and read the post.)
    - "tags" (A comma-separated list of tags for the blog post. Use the tags from the discussion and the comments.)

    All summaries and fields should be in valid markdown format where appropriate.
    For markdown lists make sure there is a blank line before and after the list.
    Only return the JSON object, nothing else.
    Return your analysis as a JSON object with the following format:
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
                logger.error(
                    "Gemini response not valid JSON after extraction",
                    error=str(e2),
                    raw=summary_response
                )
                raise
        else:
            raise

    summary = HNDiscussionSummary.objects.create(
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

    async_task('core.tasks.generate_twitter_thread', summary, group="Generate Twitter Thread")
    async_task('core.tasks.generate_summary_tags', summary, group="Generate Summary Tags")

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
    from datetime import datetime, timedelta, timezone

    # Generate subject if not provided
    now = datetime.now(timezone.utc)
    year, week_num, _ = now.isocalendar()

    # Calculate next 9am UTC
    nine_am_today = now.replace(hour=9, minute=0, second=0, microsecond=0)
    if now < nine_am_today:
        publish_date = nine_am_today
    else:
        publish_date = nine_am_today + timedelta(days=1)
    publish_date_str = publish_date.isoformat()

    summaries = HNDiscussionSummary.objects.filter(discussion_id__in=ids)
    if not summaries.exists():
        logger.error(
            "No HNDiscussionSummary objects found for ids",
            ids=ids
        )
        raise

    # Compose the body
    body_lines = ["Here is this week's digest:\n"]
    for summary in summaries:
        body_lines.append(f"**{summary.discussion_title}**\n")
        body_lines.append(f"{summary.short_summary}\n")
        full_url = f"https://askhndigests.com{summary.get_absolute_url()}"
        body_lines.append(f"[Read more]({full_url})\n")
    body = "\n".join(body_lines)

    subject = generate_buttondown_newsletter_subject(body)

    url = "https://api.buttondown.com/v1/emails"
    headers = {
        "Authorization": f"Token {settings.BUTTONDOWN_API_KEY}"
    }
    data = {
        "subject": subject,
        "body": body,
        "publish_date": publish_date_str
    }

    response = requests.post(url, headers=headers, json=data)
    logger.info(
        "Sent Buttondown Newsletter",
        status_code=response.status_code,
        text=response.text,
        response=response.json(),
        subject=subject,
        body=body,
        ids=ids
    )
    return response.json()


def generate_twitter_thread(summary: HNDiscussionSummary):
    """
    Generates a Twitter thread for the given HNDiscussionSummary.
    """
    prompt = f"""
    Generate a Twitter thread for the following blog post:
    Title: {summary.title}
    Description: {summary.description}
    Long Summary: {summary.long_summary}

    Don't use hashtags.
    Do use emojis.
    Don't use bold or italic text.
    Don't use markdown, just plain text.
    Don't use links.
    Don't use images.
    Don't use videos.

    Only return the thread, nothing else.
    Separate each tweet with `---`.
    """
    response = gemini_client.models.generate_content(
        model="gemini-2.5-pro-preview-05-06",
        contents=prompt
    )
    thread = getattr(response, 'text', None)

    if thread:
        summary.twitter_thread = thread
        summary.save(update_fields=["twitter_thread"])
        return "Success"
    else:
        logger.error(
            "Failed to generate Twitter thread",
            summary=summary
        )
        return "Failed"


def generate_summary_tags(summary: HNDiscussionSummary):
    """
    Generates 10 tags for the given HNDiscussionSummary object using Gemini.
    """
    prompt = f"""
    Please analyze the following content from a Hacker News discussion summary and generate exactly 10 relevant tags.
    These tags should help categorize the core topics and themes of the discussion.
    Title:
    {summary.title}
    Short Summary:
    {summary.short_summary}
    Long Summary (excerpt):
    {summary.long_summary} # Use an excerpt to stay within reasonable token limits
    Based on this information, provide a comma-separated string of 10 tags.
    Example output:
    tag1,tag2,tag3,tag4,tag5,tag6,tag7,tag8,tag9,tag10
    Only return the comma-separated string of tags. Do not include any other text, headers, or explanations.
    """

    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-pro-preview-05-06", # Using the same model as generate_twitter_thread
            contents=prompt
        )
        generated_tags = getattr(response, 'text', None)

        if generated_tags:
            # Basic cleaning: remove potential extra quotes or newlines
            generated_tags = generated_tags.strip().strip('"').strip("'")
            summary.tags = generated_tags
            summary.save(update_fields=["tags"])
            logger.info(
                "Successfully generated and saved summary tags",
                summary_id=summary.id,
                discussion_id=summary.discussion_id,
                generated_tags=generated_tags
            )
            return "Success"
        else:
            logger.error(
                "Failed to generate summary tags: No text in Gemini response",
                summary_id=summary.id,
                discussion_id=summary.discussion_id
            )
            return "Failed: No text in response"
    except Exception as e:
        logger.error(
            "Failed to generate summary tags due to an exception",
            summary_id=summary.id,
            discussion_id=summary.discussion_id,
            error=str(e),
            exc_info=True
        )
        return f"Failed: {str(e)}"
