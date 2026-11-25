from django.db import models
from django.utils import timezone


class TenantPortal(models.Model):
    class SourceType(models.TextChoices):
        NEWSPAPER_API = "NEWSPAPER_API", "Newspaper Platform API"
        WORDPRESS_API = "WORDPRESS_API", "WordPress REST API"

    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    domain = models.CharField(max_length=255, unique=True)
    logo_url = models.URLField(max_length=500, blank=True, default="")
    source_type = models.CharField(
        max_length=20,
        choices=SourceType.choices,
        default=SourceType.NEWSPAPER_API,
    )
    api_base_url = models.URLField(
        max_length=500,
        blank=True,
        default="",
        help_text="Optional custom API base URL. Blank uses NEWSPAPER_API_BASE_URL or https://{domain}.",
    )
    article_url_template = models.CharField(
        max_length=255,
        default="https://{domain}/news/{slug}",
        help_text="Public article URL template for NEWSPAPER_API portals.",
    )
    is_active = models.BooleanField(default=True, db_index=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return f"{self.name} ({self.slug})"


class TenantArticle(models.Model):
    class Topic(models.TextChoices):
        NATIONAL = "National", "National"
        ECONOMY = "Economy", "Economy"
        SPORTS = "Sports", "Sports"
        TECH = "Tech", "Tech"
        JOBS = "Jobs", "Jobs"
        WORLD = "World", "World"

    portal = models.ForeignKey(
        TenantPortal,
        on_delete=models.CASCADE,
        related_name="articles",
    )
    external_id = models.CharField(max_length=160)
    title = models.CharField(max_length=300)
    summary = models.TextField(blank=True, default="")
    topic = models.CharField(
        max_length=20,
        choices=Topic.choices,
        default=Topic.NATIONAL,
        db_index=True,
    )
    article_url = models.URLField(max_length=1000)
    image_url = models.URLField(max_length=1000, blank=True, default="")
    is_breaking = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    published_at = models.DateTimeField(default=timezone.now, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-published_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("portal", "external_id"),
                name="unique_portal_external_article",
            )
        ]

    def __str__(self):
        return f"[{self.portal.name}] {self.title[:60]}"


class DailyPoll(models.Model):
    question = models.CharField(max_length=300)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.question


class PollOption(models.Model):
    poll = models.ForeignKey(
        DailyPoll,
        on_delete=models.CASCADE,
        related_name="options",
    )
    label = models.CharField(max_length=180)
    votes = models.PositiveIntegerField(default=0)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "id")

    def __str__(self):
        return f"{self.label} ({self.votes})"
