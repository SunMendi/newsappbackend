from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import Newspaper


class CreateNewspaperSerializer(serializers.Serializer):
    slug = serializers.SlugField(
        max_length=120,
        validators=[UniqueValidator(queryset=Newspaper.objects.all())],
    )
    name = serializers.CharField(max_length=150)
    bangla_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    url = serializers.URLField(
        max_length=500,
        validators=[UniqueValidator(queryset=Newspaper.objects.all())],
    )
    category = serializers.ChoiceField(choices=Newspaper.Category.choices)
    accent_color = serializers.CharField(max_length=16, required=False, allow_blank=True, default="#0D9488")
    tagline = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    logo_url = serializers.URLField(max_length=500, required=False, allow_blank=True, default="")
    sort_order = serializers.IntegerField(min_value=0, required=False, default=100)


class NewspaperResponseSerializer(serializers.Serializer):
    id = serializers.CharField(source="slug", read_only=True)
    name = serializers.CharField(read_only=True)
    banglaName = serializers.SerializerMethodField()
    url = serializers.URLField(read_only=True)
    category = serializers.CharField(read_only=True)
    accentColor = serializers.CharField(source="accent_color", read_only=True)
    tagline = serializers.SerializerMethodField()
    logoUrl = serializers.SerializerMethodField()

    def get_banglaName(self, obj):
        return obj.bangla_name or None

    def get_tagline(self, obj):
        return obj.tagline or None

    def get_logoUrl(self, obj):
        return obj.logo_url or None
