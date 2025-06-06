from ninja import Schema
from typing import Optional
from pydantic import EmailStr


from core.choices import BlogPostStatus



class SubmitFeedbackIn(Schema):
    feedback: str
    page: str

class SubmitFeedbackOut(Schema):
    success: bool
    message: str


class BlogPostIn(Schema):
    title: str
    description: str = ""
    slug: str
    tags: str = ""
    content: str
    icon: Optional[str] = None  # URL or base64 string
    image: Optional[str] = None  # URL or base64 string
    status: BlogPostStatus = BlogPostStatus.DRAFT


class BlogPostOut(Schema):
    status: str  # API response status: 'success' or 'failure'
    message: str


class NewsletterSubscribeIn(Schema):
    email: EmailStr

class NewsletterSubscribeOut(Schema):
    status: str
    message: str
