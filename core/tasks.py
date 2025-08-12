import json
from datetime import UTC, datetime, timedelta

import requests
from django.conf import settings
from django.utils.text import slugify
from django_q.tasks import async_task
from google import genai

from ask_hn_digest.utils import get_ask_hn_digest_logger
from core.hn_utils import HAS_ASYNCPG, AsyncHackerNewsFetcher, get_ask_hn_story_ids
from core.models import HNDiscussionSummary
from core.utils import (
    generate_buttondown_newsletter_subject,
    generate_subreddit_recommendations,
    get_post_comments,
    ping_healthchecks,
    send_to_typefully,
)

logger = get_ask_hn_digest_logger(__name__)

gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)


def summarize_hn_discussion(discussion_id):
    # TODO: Split AI request into separate parts

    # Get the main discussion data
    discussion_resp = requests.get(
        f"https://hacker-news.firebaseio.com/v0/item/{discussion_id}.json"
    )
    discussion_data = discussion_resp.json()

    if not discussion_data or "kids" not in discussion_data:
        logger.error(
            "Invalid discussion ID or no comments found",
            discussion_id=discussion_id,
            discussion_data=discussion_data,
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
    - "short_summary"
      - This summary will be featured in an email newsletter that includes a total of 7 summaries.
      - It needs to be concise enough to fit well within this format, yet detailed enough to offer a meaningful understanding of the discussion.
      - Highlight any useful tips, tricks, or productive arguments shared.
      - The primary goal is to provide immediate value to the newsletter reader.
      - Do not talk abour HN or Hacker News in the summary.

    - "long_summary"
      - This summary will be published as a blog post on a website.
      - It should be a more comprehensive version of the short_summary.
      - Elaborate on the key themes, useful tips and tricks, insightful points, and any productive arguments from the discussion.
      - The aim is to deliver significant value to someone reading it as a standalone piece.
      - Don't start with a header/subheader. Do a text intro first, then add headers/subheader as you see fit.
      - Do not talk abour HN or Hacker News in the summary.
      - Do not talk about the discussion in the summary. Write it as if you are writing a blog post with the discussion as a reference.

    - "title"
      - A concise, SEO-friendly blog post title for this discussion.
      - Do not use generic titles.
      - Make it specific and engaging.
      - Do not use HN or Hacker News in the title.

    - "slug"
      - A URL-friendly version of the title
      - Lowercase
      - Words separated by hyphens
      - No special characters
      - On the shorter side

    - "description"
      - A 1-2 sentence summary of the discussion
      - Suitable for meta description tags
      - Should entice a reader to click and read the post

    - "tags"
      - A comma-separated list of tags for the blog post
      - Use the tags from the discussion and the comments
      - Do not include HN or Hacker News in the tags

    ---

    - All summaries and fields should be in valid markdown format where appropriate.
    - For markdown lists make sure there is a blank line before and after the list.
    - IMPORTANT: Only return the JSON object, nothing else.

    ---

    IMPORTANT: Return your analysis as a JSON object with the following format:
    {{
      "short_summary": "Brief markdown summary here",
      "long_summary": "Detailed markdown summary here",
      "title": "SEO-friendly blog post title here",
      "slug": "url-friendly-slug-here",
      "description": "Meta description here"
    }}
    """  # noqa: E501

    response = gemini_client.models.generate_content(
        model="gemini-2.5-pro-preview-05-06", contents=prompt
    )
    summary_response = getattr(response, "text", None)

    try:
        summary_data = json.loads(summary_response)
    except json.JSONDecodeError:
        # Try to extract JSON from the response if possible
        import re

        match = re.search(r"\{.*\}", summary_response, re.DOTALL)
        if match:
            try:
                summary_data = json.loads(match.group(0))
            except Exception as e2:
                logger.error(
                    "Gemini response not valid JSON after extraction",
                    error=str(e2),
                    raw=summary_response,
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
        tags=summary_data.get("tags", ""),
    )

    async_task("core.tasks.generate_summary_tags", summary, group="Generate Summary Tags")

    return "Success"


def send_buttondown_newsletter(ids: list[int] | None = None):
    from core.models import HNDiscussionSummary

    ping_healthchecks("f68afc04-5bb7-446f-adf5-0b6c91b56a43", suffix="start")

    # Generate subject if not provided
    now = datetime.now(UTC)
    year, week_num, _ = now.isocalendar()

    # Calculate next 9am UTC
    nine_am_today = now.replace(hour=9, minute=0, second=0, microsecond=0)
    if now < nine_am_today:
        publish_date = nine_am_today
    else:
        publish_date = nine_am_today + timedelta(days=1)
    publish_date_str = publish_date.isoformat()

    if not ids:
        ids = get_ask_hn_story_ids(limit=5)

    summaries = HNDiscussionSummary.objects.filter(discussion_id__in=ids)
    if not summaries.exists():
        logger.error("No HNDiscussionSummary objects found for ids", ids=ids)
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
    headers = {"Authorization": f"Token {settings.BUTTONDOWN_API_KEY}"}
    data = {"subject": subject, "body": body, "publish_date": publish_date_str}

    response = requests.post(url, headers=headers, json=data)
    logger.info(
        "Sent Buttondown Newsletter",
        status_code=response.status_code,
        text=response.text,
        response=response.json(),
        subject=subject,
        body=body,
        ids=ids,
    )

    ping_healthchecks("f68afc04-5bb7-446f-adf5-0b6c91b56a43")

    return "Success"


def generate_twitter_thread(summary: HNDiscussionSummary):
    """
    Generates a Twitter thread for the given HNDiscussionSummary.
    """
    prompt = f"""
    Generate a Twitter thread for the following blog post:

    ---
    Title: {summary.title}
    Description: {summary.description}
    Long Summary: {summary.long_summary}
    ---

    Formatting rules:
    - Don't use hashtags.
    - Don't use emojis.
    - Don't use bold or italic text.
    - Don't use markdown, just plain text.
    - Don't use links.
    - Don't use images.
    - Don't use videos.
    - Don't mention Hacker News or HN in the thread.
    - Don't mention the discussion in the thread. Write as if you are coming up with a thread. Use discussion as a reference.
    - Separate each tweet with `---`.
    - Split each tweet such that each paragraph represents an idea. Here is an example:
    instead of this:
    ```
    So, what's the right way? There isn't one! Your strategy depends on your goal. Are you practicing good habits, trying to hack the model for better output, or optimizing for pure efficiency? What's your approach? 🤔
    ```

    do this:
    ```
    ---
    So, what's the right way?

    There isn't one!

    Your strategy depends on your goal.

    Are you practicing good habits, trying to hack the model for better output, or optimizing for pure efficiency?

    What's your approach?
    ---
    ```
    This doesn't mean that each sentence should be a paragraph., but each idea should be a paragraph.

    IMPORTANT: Only return the thread, nothing else.
    """  # noqa: E501

    response = gemini_client.models.generate_content(
        model="gemini-2.5-pro-preview-05-06", contents=prompt
    )
    thread = getattr(response, "text", None)

    if thread:
        summary.twitter_thread = thread
        summary.save(update_fields=["twitter_thread"])

        # send_to_typefully(thread)

        return "Success"
    else:
        logger.error("Failed to generate Twitter thread", summary=summary)
        return "Failed"


def generate_single_tweet(summary: HNDiscussionSummary):
    """
    Generates a single tweet for the given HNDiscussionSummary.
    """
    prompt = f"""
    Generate a single tweet for the following blog post:

    ---
    Title: {summary.title}
    Description: {summary.description}
    Long Summary: {summary.long_summary}
    ---

    Style of the tweet should be personal. Feel free to:
    - use first person
    - use casual language
    - use a conversational and friendly tone
    - use a tone that is engaging, helpful and informative
    - should be formatted as an opinion or a today-i-learned

    Formatting rules:
    - Don't use hashtags.
    - Don't use emojis.
    - Don't use bold or italic text.
    - Don't use markdown, just plain text.
    - Don't use links.
    - Don't use images.
    - Don't use videos.
    - Don't mention Hacker News or HN in the tweet.
    - Don't mention the discussion in the tweet. Write as if you are coming up with a tweet. Use discussion as a reference.
    - Keep it under 280 characters.
    - Make it engaging and informative.
    - Focus on the most interesting or valuable insight from the content.

    IMPORTANT: Only return the tweet text, nothing else.
    """  # noqa: E501

    response = gemini_client.models.generate_content(
        model="gemini-2.5-pro-preview-05-06", contents=prompt
    )
    tweet = getattr(response, "text", None)

    if tweet:
        # Clean up any potential extra whitespace or quotes
        tweet = tweet.strip().strip('"').strip("'")
        summary.single_tweet = tweet
        summary.save(update_fields=["single_tweet"])

        logger.info(
            "Successfully generated and saved single tweet",
            summary_id=summary.id,
            discussion_id=summary.discussion_id,
            tweet_length=len(tweet),
        )
        send_to_typefully(tweet, threadify=False)
        return "Success"
    else:
        logger.error("Failed to generate single tweet", summary=summary)
        return "Failed"


def generate_reddit_post(summary: HNDiscussionSummary):
    subreddits = generate_subreddit_recommendations(summary)

    prompt = f"""
        **Your Role:** You are an expert content strategist and Reddit community manager. Your skill is in taking a core idea or piece of content and reframing it into an authentic, original, and high-engagement Reddit post that feels like it was written by a real person for a specific community.

        **Your Task:** Take the provided content and transform it into a complete Reddit post. You will internally analyze the suggested subreddits to select the best one, then internally generate and select the most compelling title. Finally, you will rewrite the provided content into a post body that is tailored for the chosen community and presented as an original thought or observation.

        ---
        **Input Content:**
        Topic Title: {summary.title}
        Core Idea: {summary.description}
        Detailed Content: {summary.long_summary}
        Target Subreddits: {summary.subreddits}
        ---

        **Instructions for the AI:**

        **Step 1: Internal Analysis and Selection of Subreddit**
        Internally analyze the `[Target Subreddits]` list. Consider each subreddit's rules, tone, typical content, and relevance to the `[Topic Title]` and `[Detailed Content]`. Select the single best subreddit to post to. All subsequent steps must be tailored for this chosen subreddit.

        **Step 2: Internal Generation and Selection of Title**
        Internally generate 5 engaging title options based on the `[Detailed Content]`. The titles should be designed to spark curiosity and discussion within the chosen subreddit. From those 5, select the single most compelling and appropriate title. This will be the final title for the post.

        **Step 3: Rewrite Content into an Original Post Body**
        Write the full post body by adapting the `[Detailed Content]`. Follow this framework:

        *   **Framing:** Present the content as your own original thoughts, observations, or story. **DO NOT** mention that the content comes from another source, summary, or discussion.
        *   **Hook:** Start with a strong opening sentence that captures the core of the `[Core Idea]`.
        *   **The Breakdown:** Present the main arguments from the `[Detailed Content]` in a clear, digestible format. Use bullet points (`-`) or a numbered list to break down different viewpoints, pros/cons, or key takeaways.
        *   **Personal Touch (Optional but Recommended):** Add a brief personal reflection or opinion to make the post feel more authentic.
        *   **Call to Discussion:** End with one or two open-ended questions to spark a conversation. Examples: `"What's your take on this?", "Am I missing something here?", "Curious to hear what this community thinks."`

        ---

        **Critical Rules & Constraints (MUST FOLLOW):**

        *   🚫 **DO NOT MENTION THE SOURCE:** Under no circumstances should you mention 'Hacker News', 'HN', 'a discussion', 'a summary', or any other external source. The post must be presented as the user's original thoughts.
        *   ✍️ **ADOPT A PERSONAL VOICE:** Write in a first-person, conversational tone. The goal is to sound like a genuine community member sharing an insight, not a bot summarizing text.
        *   📜 **FOLLOW SUBREDDIT RULES:** Ensure the post format and content adhere to the specific rules of the chosen subreddit (e.g., rules against low-effort posts, requirements for post length, etc.).
        *   ✨ **SCANNABILITY IS KEY:** Use **bolding**, bullet points, and short paragraphs to make the post easy to read and digest quickly. Avoid walls of text.

        ---

        **Output Format:**
        Your entire response must be a single string with no extra text, commentary, or formatting. It must strictly follow this structure, with each part separated by two newlines:

        Post to: [Chosen Subreddit]

        Title: [Chosen Title]

        Content: [Post Body]
    """  # noqa: E501

    response = gemini_client.models.generate_content(
        model="gemini-2.5-pro-preview-05-06", contents=prompt
    )
    reddit_response = getattr(response, "text", None)

    if reddit_response:
        summary.reddit_post = reddit_response
        summary.save(update_fields=["reddit_post"])

        logger.info(
            "Successfully generated and saved Reddit post",
            summary_id=summary.id,
            discussion_id=summary.discussion_id,
            post_length=len(reddit_response),
            subreddits=subreddits,
        )
        return "Success"
    else:
        logger.error("Failed to generate Reddit post", summary=summary)
        return "Failed"


def generate_summary_tags(summary: HNDiscussionSummary):
    prompt = f"""
    Please analyze the following content from a Hacker News discussion summary and generate exactly 10 relevant tags.
    These tags should help categorize the core topics and themes of the discussion.

    ---
    Title:
    {summary.title}

    Short Summary:
    {summary.short_summary}

    Long Summary (excerpt):
    {summary.long_summary}
    ---

    Based on this information, provide a comma-separated string of 10 tags.

    Example output:
    tag1,tag2,tag3,tag4,tag5,tag6,tag7,tag8,tag9,tag10

    Only return the comma-separated string of tags.
    Do not include any other text, headers, or explanations.
    Do not include HN or Hacker News in the tags.
    """  # noqa: E501

    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-pro-preview-05-06",  # Using the same model as generate_twitter_thread
            contents=prompt,
        )
        generated_tags = getattr(response, "text", None)

        if generated_tags:
            # Basic cleaning: remove potential extra quotes or newlines
            generated_tags = generated_tags.strip().strip('"').strip("'")
            summary.tags = generated_tags
            summary.save(update_fields=["tags"])
            logger.info(
                "Successfully generated and saved summary tags",
                summary_id=summary.id,
                discussion_id=summary.discussion_id,
                generated_tags=generated_tags,
            )
            return "Success"
        else:
            logger.error(
                "Failed to generate summary tags: No text in Gemini response",
                summary_id=summary.id,
                discussion_id=summary.discussion_id,
            )
            return "Failed: No text in response"
    except Exception as e:
        logger.error(
            "Failed to generate summary tags due to an exception",
            summary_id=summary.id,
            discussion_id=summary.discussion_id,
            error=str(e),
            exc_info=True,
        )
        return f"Failed: {str(e)}"


def sync_hn_data_async():
    """
    Task to sync Hacker News data using the hn_utils AsyncHackerNewsFetcher.
    This replaces the old sync logic with the modern async approach.
    """
    import asyncio

    ping_healthchecks("4b2a8a85-5511-4258-83e4-3bee1a3e3032", suffix="start")

    async def _run_sync():
        logger.info("Starting HN data sync task")

        try:
            # Configure fetcher based on available libraries
            concurrent_requests = 500 if HAS_ASYNCPG else 20
            batch_size = 4000 if HAS_ASYNCPG else 500

            logger.info(
                "HN sync configuration",
                concurrent_requests=concurrent_requests,
                batch_size=batch_size,
                database_backend="AsyncPG" if HAS_ASYNCPG else "psycopg2",
            )

            # Create fetcher instance
            fetcher = AsyncHackerNewsFetcher(
                concurrent_requests=concurrent_requests, batch_size=batch_size
            )

            try:
                # Run the async fetch with defaults (auto-resume, auto-detect max)
                await fetcher.fetch_all_items()
                logger.info("HN data sync completed successfully")
                return "Success"
            finally:
                # Always clean up resources
                await fetcher.close()

        except Exception as e:
            logger.error("HN data sync failed", error=str(e), exc_info=True)
            return f"Failed: {str(e)}"

    try:
        asyncio.run(_run_sync())
        ping_healthchecks("4b2a8a85-5511-4258-83e4-3bee1a3e3032")
        return "Success"
    except Exception as e:
        logger.error("Failed to run HN data sync", error=str(e), exc_info=True)
        return f"Failed: {str(e)}"


def schedule_ask_hn_summaries():
    ping_healthchecks("d8da731d-a94e-4527-a8c7-15219c248e32", suffix="start")

    story_ids = get_ask_hn_story_ids()

    story_ids_to_analyze = [
        s for s in story_ids if not HNDiscussionSummary.objects.filter(discussion_id=s).exists()
    ]

    for story_id in story_ids_to_analyze:
        async_task(
            "core.tasks.summarize_hn_discussion",
            story_id,
            group="Analyze Discussion (Automated)",
            timeout=159,
        )

    ping_healthchecks("d8da731d-a94e-4527-a8c7-15219c248e32")

    return f"Scheduled {len(story_ids_to_analyze)} summaries"
