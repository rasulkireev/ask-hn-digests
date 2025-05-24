from django.forms.utils import ErrorList

from ask_hn_digest.utils import get_ask_hn_digest_logger
from google import genai
from django.conf import settings

logger = get_ask_hn_digest_logger(__name__)

gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)


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
