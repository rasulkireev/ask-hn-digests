import re

import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models, transaction
from django.db.models import Count
from django.urls import reverse
from django.utils.text import slugify

from ask_hn_digest.utils import get_ask_hn_digest_logger
from core.base_models import BaseModel
from core.choices import BlogPostStatus
from core.model_utils import generate_random_key

logger = get_ask_hn_digest_logger(__name__)


TAG_NAME_MAX_LENGTH = 80
TAG_SLUG_MAX_LENGTH = 96
TAG_SPLIT_RE = re.compile(r"[,;\n]+")
TAG_WHITESPACE_RE = re.compile(r"\s+")


class TopicLane(models.TextChoices):
    AI_ML = "ai_ml", "AI & Machine Learning"
    PROGRAMMING = "programming", "Programming"
    DEVTOOLS_INFRA = "devtools_infra", "Dev Tools & Infrastructure"
    STARTUPS_BUSINESS = "startups_business", "Startups & Business"
    CAREERS_WORK = "careers_work", "Careers & Work"
    SECURITY_PRIVACY = "security_privacy", "Security & Privacy"
    PRODUCT_DESIGN = "product_design", "Product & Design"
    HARDWARE_SCIENCE = "hardware_science", "Hardware & Science"
    CULTURE_SOCIETY = "culture_society", "Culture & Society"
    OTHER = "other", "Other"


CANONICAL_TAG_ALIASES = {
    "AI": ("artificial intelligence", "a i", "ai tools", "gen ai", "genai", "generative ai"),
    "AI Agents": ("agents", "agentic ai", "ai agent", "ai agents"),
    "APIs": ("api", "application programming interfaces"),
    "AR/VR": ("ar", "vr", "augmented reality", "virtual reality", "mixed reality", "xr"),
    "AWS": ("amazon web services",),
    "Business": ("business model", "business models"),
    "C": ("c programming", "ansi c"),
    "C++": ("cpp", "cplusplus", "c plus plus"),
    "CI/CD": ("ci cd", "cicd", "continuous integration", "continuous delivery"),
    "CSS": ("cascading style sheets",),
    "Databases": ("database", "db", "dbs"),
    "DevOps": ("dev ops", "developer operations"),
    "Developer Tools": ("dev tools", "devtools", "development tools"),
    "Docker": ("containers", "containerization"),
    "GPT": ("chatgpt", "gpt models", "gpts"),
    "Go": ("golang",),
    "HTML": ("hypertext markup language",),
    "JavaScript": ("js", "ecmascript"),
    "LLMs": ("llm", "large language model", "large language models"),
    "Machine Learning": ("ml", "machine-learning"),
    "Node.js": ("node", "nodejs"),
    "PostgreSQL": ("postgres", "postgresql", "psql"),
    "React": ("react.js", "reactjs"),
    "Ruby on Rails": ("rails", "ror"),
    "SaaS": ("software as a service",),
    "SQLite": ("sqlite3",),
    "TypeScript": ("ts",),
    "UI": ("user interface", "interfaces"),
    "UX": ("user experience",),
}

TAG_DISPLAY_OVERRIDES = {
    "ai": "AI",
    "api": "API",
    "apis": "APIs",
    "ar": "AR",
    "aws": "AWS",
    "cli": "CLI",
    "cpu": "CPU",
    "css": "CSS",
    "devops": "DevOps",
    "dns": "DNS",
    "gpu": "GPU",
    "gpt": "GPT",
    "html": "HTML",
    "ios": "iOS",
    "ip": "IP",
    "llm": "LLM",
    "llms": "LLMs",
    "macos": "macOS",
    "ml": "ML",
    "mysql": "MySQL",
    "nosql": "NoSQL",
    "postgresql": "PostgreSQL",
    "saas": "SaaS",
    "seo": "SEO",
    "sql": "SQL",
    "ui": "UI",
    "ux": "UX",
    "vr": "VR",
}

TAG_SLUG_OVERRIDES = {
    "C++": "c-plus-plus",
}

NOISY_TAG_SLUGS = {
    "ask-hn",
    "hacker-news",
    "hn",
    "news-ycombinator",
    "y-combinator-news",
}

LANE_KEYWORD_SLUGS = {
    TopicLane.AI_ML: (
        "ai",
        "ai-agents",
        "chatgpt",
        "computer-vision",
        "embeddings",
        "generative-ai",
        "gpt",
        "llm",
        "llms",
        "machine-learning",
        "neural-network",
        "neural-networks",
        "nlp",
        "openai",
    ),
    TopicLane.PROGRAMMING: (
        "algorithms",
        "c",
        "c-plus-plus",
        "coding",
        "compilers",
        "django",
        "go",
        "java",
        "javascript",
        "nodejs",
        "programming",
        "python",
        "rails",
        "react",
        "ruby",
        "ruby-on-rails",
        "rust",
        "software-engineering",
        "typescript",
        "web-development",
    ),
    TopicLane.DEVTOOLS_INFRA: (
        "api",
        "apis",
        "aws",
        "cicd",
        "cloud",
        "databases",
        "deployment",
        "developer-tools",
        "devops",
        "docker",
        "git",
        "infrastructure",
        "kubernetes",
        "linux",
        "monitoring",
        "observability",
        "postgresql",
        "sqlite",
    ),
    TopicLane.STARTUPS_BUSINESS: (
        "bootstrapping",
        "business",
        "fundraising",
        "marketing",
        "pricing",
        "sales",
        "saas",
        "startup",
        "startups",
    ),
    TopicLane.CAREERS_WORK: (
        "career",
        "careers",
        "hiring",
        "interviewing",
        "management",
        "productivity",
        "remote-work",
        "work",
    ),
    TopicLane.SECURITY_PRIVACY: (
        "cryptography",
        "privacy",
        "security",
        "surveillance",
    ),
    TopicLane.PRODUCT_DESIGN: (
        "design",
        "product",
        "product-management",
        "ui",
        "ux",
    ),
    TopicLane.HARDWARE_SCIENCE: (
        "biology",
        "energy",
        "gpu",
        "hardware",
        "math",
        "physics",
        "science",
    ),
    TopicLane.CULTURE_SOCIETY: (
        "culture",
        "education",
        "ethics",
        "law",
        "policy",
        "society",
        "writing",
    ),
}


def _alias_lookup() -> dict[str, str]:
    lookup = {}

    for canonical_name in CANONICAL_TAG_ALIASES:
        alias_slug = slugify(canonical_name)
        if alias_slug:
            lookup.setdefault(alias_slug, canonical_name)

    for canonical_name, aliases in CANONICAL_TAG_ALIASES.items():
        for alias in aliases:
            alias_slug = slugify(alias)
            if alias_slug:
                lookup.setdefault(alias_slug, canonical_name)
    return lookup


CANONICAL_TAG_BY_ALIAS_SLUG = _alias_lookup()


def clean_raw_tag_name(raw_tag) -> str:
    if raw_tag is None:
        return ""

    tag_name = str(raw_tag).strip().strip("\"'")
    tag_name = tag_name.removeprefix("#").strip()
    tag_name = tag_name.replace("_", " ")
    tag_name = TAG_WHITESPACE_RE.sub(" ", tag_name).strip(" .")
    return tag_name[:TAG_NAME_MAX_LENGTH].strip()


def display_tag_name(raw_name: str) -> str:
    words = []
    for word in raw_name.split(" "):
        word_slug = slugify(word)
        if word_slug in TAG_DISPLAY_OVERRIDES:
            words.append(TAG_DISPLAY_OVERRIDES[word_slug])
        elif word.isupper() and len(word) <= 5:
            words.append(word)
        else:
            words.append(word.capitalize())
    return " ".join(words).strip()


def normalize_tag_name(raw_tag) -> str:
    cleaned_name = clean_raw_tag_name(raw_tag)
    if not cleaned_name:
        return ""

    cleaned_slug = slugify(cleaned_name)
    if not cleaned_slug or cleaned_slug in NOISY_TAG_SLUGS:
        return ""

    for canonical_name in CANONICAL_TAG_ALIASES:
        if cleaned_name.casefold() == canonical_name.casefold():
            return canonical_name

    canonical_name = CANONICAL_TAG_BY_ALIAS_SLUG.get(cleaned_slug)
    if canonical_name:
        return canonical_name

    return display_tag_name(cleaned_name)


def canonical_tag_slug(tag_name: str) -> str:
    return TAG_SLUG_OVERRIDES.get(tag_name, slugify(tag_name))[:TAG_SLUG_MAX_LENGTH]


def is_exact_canonical_tag_name(tag_name: str) -> bool:
    return any(tag_name.casefold() == canonical_name.casefold() for canonical_name in CANONICAL_TAG_ALIASES)


def split_raw_tags(raw_tags) -> list[str]:
    if not raw_tags:
        return []

    candidates = TAG_SPLIT_RE.split(raw_tags) if isinstance(raw_tags, str) else raw_tags
    tag_names = []
    seen_slugs = set()

    for candidate in candidates:
        tag_name = normalize_tag_name(candidate)
        tag_slug = canonical_tag_slug(tag_name)
        if not tag_name or tag_slug in seen_slugs:
            continue
        seen_slugs.add(tag_slug)
        tag_names.append(tag_name)

    return tag_names


def infer_topic_lane(tag_name: str) -> str:
    tag_slug = slugify(tag_name)
    for lane, keyword_slugs in LANE_KEYWORD_SLUGS.items():
        for keyword_slug in keyword_slugs:
            if tag_slug == keyword_slug or tag_slug.startswith(f"{keyword_slug}-"):
                return lane
    return TopicLane.OTHER


class Profile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    key = models.CharField(max_length=10, unique=True, default=generate_random_key)


class NewsletterSubscriber(BaseModel):
    email = models.EmailField(unique=True)
    added_to_buttondown = models.BooleanField(default=False)

    def __str__(self):
        return self.email

    def add_newsletter_subscriber_to_buttondown(self, tags: list[str] = None, ip_address: str = None):
        url = "https://api.buttondown.com/v1/subscribers"
        headers = {"Authorization": f"Token {settings.BUTTONDOWN_API_KEY}"}
        data = {
            "email_address": self.email,
            "type": "unactivated",
        }

        if tags:
            data["tags"] = tags

        if ip_address:
            data["ip_address"] = ip_address

        response = requests.request("POST", url, headers=headers, json=data)

        logger.info(
            "Newsletter subscription response",
            response_json=response.json(),
            response_text=response.text,
            status_code=response.status_code,
            email=self.email,
            tags=tags,
            ip_address=ip_address,
        )

        if response.status_code == 201:
            self.added_to_buttondown = True
            self.save()

            return True

        return False


class BlogPost(BaseModel):
    title = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    slug = models.SlugField(max_length=250)
    tags = models.TextField()
    content = models.TextField()
    icon = models.ImageField(upload_to="blog_post_icons/", blank=True)
    image = models.ImageField(upload_to="blog_post_images/", blank=True)
    status = models.CharField(
        max_length=10,
        choices=BlogPostStatus.choices,
        default=BlogPostStatus.DRAFT,
    )

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("blog_post", kwargs={"slug": self.slug})


class Feedback(BaseModel):
    profile = models.ForeignKey(
        Profile,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="feedback",
        help_text="The user who submitted the feedback",
    )
    feedback = models.TextField(
        help_text="The feedback text",
    )
    page = models.CharField(
        max_length=255,
        help_text="The page where the feedback was submitted",
    )

    def __str__(self):
        return f"{self.profile.user.email}: {self.feedback}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)

        if is_new:
            from django.conf import settings
            from django.core.mail import send_mail

            subject = "New Feedback Submitted"
            message = f"""
                New feedback was submitted:\n\n
                User: {self.profile.user.email if self.profile else "Anonymous"}
                Feedback: {self.feedback}
                Page: {self.page}
            """
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [settings.DEFAULT_FROM_EMAIL]

            send_mail(subject, message, from_email, recipient_list, fail_silently=True)


class TagQuerySet(models.QuerySet):
    def with_summary_counts(self):
        return self.annotate(summary_count=Count("summaries", distinct=True))

    def visible(self):
        return self.with_summary_counts().filter(summary_count__gt=0)


class Tag(BaseModel):
    name = models.CharField(max_length=TAG_NAME_MAX_LENGTH)
    slug = models.SlugField(max_length=TAG_SLUG_MAX_LENGTH, unique=True)
    topic_lane = models.CharField(
        max_length=32,
        choices=TopicLane.choices,
        default=TopicLane.OTHER,
        db_index=True,
    )

    objects = TagQuerySet.as_manager()

    class Meta:
        ordering = ["topic_lane", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        update_fields = kwargs.get("update_fields")
        update_fields_set = set(update_fields) if update_fields is not None else None

        if not self.slug:
            self.slug = canonical_tag_slug(self.name)
            if update_fields_set is not None:
                update_fields_set.add("slug")

        inferred_lane = infer_topic_lane(self.name)
        if (not self.topic_lane or self.topic_lane == TopicLane.OTHER) and inferred_lane != TopicLane.OTHER:
            self.topic_lane = inferred_lane
            if update_fields_set is not None:
                update_fields_set.add("topic_lane")

        if update_fields_set is not None:
            kwargs["update_fields"] = update_fields_set
        super().save(*args, **kwargs)

    @classmethod
    def get_or_create_from_raw_name(cls, raw_name):
        cleaned_name = clean_raw_tag_name(raw_name)
        canonical_name = normalize_tag_name(cleaned_name)
        if not canonical_name:
            return None

        raw_slug = slugify(cleaned_name)
        is_exact_canonical = is_exact_canonical_tag_name(cleaned_name)
        if raw_slug and not is_exact_canonical:
            alias = TagAlias.objects.select_related("tag").filter(slug=raw_slug).first()
            if alias:
                return alias.tag

        tag_slug = canonical_tag_slug(canonical_name)
        tag, _created = cls.objects.get_or_create(
            slug=tag_slug,
            defaults={
                "name": canonical_name,
                "topic_lane": infer_topic_lane(canonical_name),
            },
        )

        if tag.name != canonical_name or tag.topic_lane == TopicLane.OTHER:
            updates = []
            if tag.name != canonical_name:
                tag.name = canonical_name
                updates.append("name")
            inferred_lane = infer_topic_lane(canonical_name)
            if tag.topic_lane == TopicLane.OTHER and inferred_lane != TopicLane.OTHER:
                tag.topic_lane = inferred_lane
                updates.append("topic_lane")
            if updates:
                tag.save(update_fields=updates)

        if raw_slug and not is_exact_canonical and raw_slug != tag.slug:
            TagAlias.objects.get_or_create(
                slug=raw_slug[:TAG_SLUG_MAX_LENGTH],
                defaults={"tag": tag, "name": cleaned_name[:TAG_NAME_MAX_LENGTH]},
            )

        return tag

    @classmethod
    def objects_from_raw_tags(cls, raw_tags):
        tags = []
        seen_tag_ids = set()
        candidates = TAG_SPLIT_RE.split(raw_tags) if isinstance(raw_tags, str) else raw_tags or []

        for candidate in candidates:
            tag = cls.get_or_create_from_raw_name(candidate)
            if not tag or tag.id in seen_tag_ids:
                continue
            seen_tag_ids.add(tag.id)
            tags.append(tag)

        return tags

    @classmethod
    def resolve_slug(cls, tag_slug: str):
        normalized_slug = slugify(tag_slug)
        if not normalized_slug:
            return None

        tag = cls.objects.filter(slug=normalized_slug).first()
        if tag:
            return tag

        alias = TagAlias.objects.select_related("tag").filter(slug=normalized_slug).first()
        if alias:
            return alias.tag

        return None


class TagAlias(BaseModel):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name="aliases")
    name = models.CharField(max_length=TAG_NAME_MAX_LENGTH)
    slug = models.SlugField(max_length=TAG_SLUG_MAX_LENGTH, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "tag aliases"

    def __str__(self):
        return f"{self.name} -> {self.tag.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:TAG_SLUG_MAX_LENGTH]
        super().save(*args, **kwargs)


class HNDiscussionSummary(BaseModel):
    discussion_id = models.BigIntegerField(unique=True, help_text="Hacker News discussion ID")
    discussion_title = models.CharField(max_length=500, help_text="Title of the discussion")
    comment_ids = models.JSONField(help_text="List of all comment IDs for this discussion")
    date_analyzed = models.DateTimeField(auto_now_add=True, help_text="Date and time when the discussion was analyzed")

    # for email
    short_summary = models.TextField(help_text="Short summary of the discussion")

    # for post
    slug = models.SlugField(max_length=250, unique=True, help_text="Slug for the blog post")
    title = models.CharField(max_length=250, help_text="Title of the blog post")
    description = models.TextField(blank=True, help_text="Description of the blog post")
    legacy_tags = models.TextField(blank=True, help_text="Original comma-separated tags for this post")
    tags = models.ManyToManyField(Tag, blank=True, related_name="summaries")
    long_summary = models.TextField(help_text="Long summary of the discussion")

    # for twitter
    twitter_thread = models.TextField(blank=True)
    single_tweet = models.TextField(blank=True)

    # reddit
    subreddits = models.TextField(blank=True, help_text="Subreddits to post to")
    reddit_post = models.TextField(blank=True)

    def __str__(self):
        return f"ID: {self.discussion_id} - Title: {self.discussion_title}"

    def get_absolute_url(self):
        return reverse("blog_post", kwargs={"slug": self.slug})

    def get_tags_list(self):
        """Return a list of tags for this summary"""
        if self.pk:
            tag_names = sorted(tag.name for tag in self.tags.all())
            if tag_names:
                return tag_names
        return split_raw_tags(self.legacy_tags)

    @property
    def tag_keywords(self):
        return ", ".join(self.get_tags_list())

    def set_tags_from_text(self, tags_text, *, save_legacy=True):
        with transaction.atomic():
            tags = Tag.objects_from_raw_tags(tags_text)

            if save_legacy:
                self.legacy_tags = tags_text or ""
                self.save(update_fields=["legacy_tags"])

            self.tags.set(tags)

    @classmethod
    def get_all_tags_with_counts(cls):
        """Get all tags with their counts"""
        return Tag.objects.visible().order_by("-summary_count", "name")

    @classmethod
    def get_summaries_by_tag(cls, tag):
        """Get all summaries that have the specified tag"""
        if isinstance(tag, Tag):
            tag_obj = tag
        else:
            tag_obj = Tag.resolve_slug(tag) or Tag.objects.filter(name__iexact=tag).first()

        if not tag_obj:
            return cls.objects.none()

        return cls.objects.filter(tags=tag_obj).prefetch_related("tags").order_by("-date_analyzed")

    @staticmethod
    def get_latest_summaries_ids(count: int = 7):
        return list(
            HNDiscussionSummary.objects.order_by("-date_analyzed")[:count].values_list("discussion_id", flat=True)
        )
