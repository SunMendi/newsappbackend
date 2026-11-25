from django.utils import timezone
from rest_framework import serializers


def format_time_ago(dt) -> str:
    if not dt:
        return "Just now"
    delta = timezone.now() - dt
    seconds = max(0, int(delta.total_seconds()))
    if seconds < 60:
        return "Just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    return f"{days}d ago"


def estimate_read_time(summary: str) -> str:
    words = len((summary or "").split())
    seconds = max(20, min(90, int(words * 0.45)))
    return f"{seconds} sec brief"


class TrendingItemSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    headline = serializers.CharField(source="title", read_only=True)
    sourceName = serializers.CharField(source="portal.name", read_only=True)
    sourceUrl = serializers.URLField(source="article_url", read_only=True)
    category = serializers.CharField(source="topic", read_only=True)
    publishedAgo = serializers.SerializerMethodField()
    isBreaking = serializers.BooleanField(source="is_breaking", read_only=True)

    def get_id(self, obj):
        return f"tr-{obj.id}"

    def get_publishedAgo(self, obj):
        return format_time_ago(obj.published_at)


class AutomatedStorySerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    title = serializers.CharField(read_only=True)
    summary = serializers.CharField(read_only=True)
    topic = serializers.CharField(read_only=True)
    sourceName = serializers.CharField(source="portal.name", read_only=True)
    sourceUrl = serializers.URLField(source="article_url", read_only=True)
    imageUrl = serializers.SerializerMethodField()
    publishedAgo = serializers.SerializerMethodField()
    readTime = serializers.SerializerMethodField()

    def get_id(self, obj):
        return f"feed-{obj.id}"

    def get_imageUrl(self, obj):
        return obj.image_url or None

    def get_publishedAgo(self, obj):
        return format_time_ago(obj.published_at)

    def get_readTime(self, obj):
        return estimate_read_time(obj.summary)


class PollOptionSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    label = serializers.CharField(read_only=True)
    votes = serializers.IntegerField(read_only=True)

    def get_id(self, obj):
        return str(obj.id)


class DailyPollSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    question = serializers.CharField(read_only=True)
    totalVotes = serializers.SerializerMethodField()
    options = PollOptionSerializer(many=True, read_only=True)

    def get_id(self, obj):
        return str(obj.id)

    def get_totalVotes(self, obj):
        return sum(opt.votes for opt in obj.options.all())


class PollVoteInputSerializer(serializers.Serializer):
    optionId = serializers.IntegerField(min_value=1)


class IngestArticleSerializer(serializers.Serializer):
    portal_slug = serializers.SlugField(max_length=100)
    portal_name = serializers.CharField(max_length=150)
    portal_domain = serializers.CharField(max_length=255)
    portal_logo_url = serializers.URLField(max_length=500, required=False, allow_blank=True, default="")
    external_id = serializers.CharField(max_length=160)
    title = serializers.CharField(max_length=300)
    summary = serializers.CharField(required=False, allow_blank=True, default="")
    topic = serializers.CharField(max_length=60, required=False, allow_blank=True, default="National")
    article_url = serializers.URLField(max_length=1000)
    image_url = serializers.URLField(max_length=1000, required=False, allow_blank=True, default="")
    is_breaking = serializers.BooleanField(required=False, default=False)
    published_at = serializers.CharField(required=False, allow_blank=True, default="")
