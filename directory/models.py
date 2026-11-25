from django.db import models


class Newspaper(models.Model):
    class Category(models.TextChoices):
        BANGLA = "BANGLA", "Bangla"
        ENGLISH = "ENGLISH", "English"
        INTERNATIONAL = "INTERNATIONAL", "International"
        TV_NEWS = "TV NEWS", "TV News"
        BUSINESS = "BUSINESS", "Business"
        ONLINE = "ONLINE", "Online"

    slug = models.SlugField(max_length=120, unique=True, db_index=True)
    name = models.CharField(max_length=150)
    bangla_name = models.CharField(max_length=150, blank=True, default="")
    url = models.URLField(max_length=500, unique=True)
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.BANGLA,
        db_index=True,
    )
    accent_color = models.CharField(max_length=16, blank=True, default="#0D9488")
    tagline = models.CharField(max_length=150, blank=True, default="")
    logo_url = models.URLField(max_length=500, blank=True, default="")
    sort_order = models.PositiveIntegerField(default=100, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("sort_order", "name")

    def __str__(self):
        return f"{self.name} ({self.category})"
