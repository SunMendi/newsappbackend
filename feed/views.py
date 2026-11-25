from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    AutomatedStorySerializer,
    DailyPollSerializer,
    IngestArticleSerializer,
    PollVoteInputSerializer,
    TrendingItemSerializer,
)
from .services import (
    get_active_poll,
    ingest_tenant_article,
    list_feed_articles,
    list_trending_articles,
    record_poll_vote,
    sync_all_active_portals,
)


class TrendingListAPIView(APIView):
    def get(self, request):
        articles = list_trending_articles(limit=15)
        serializer = TrendingItemSerializer(articles, many=True)
        return Response({"items": serializer.data}, status=status.HTTP_200_OK)


class FeedAPIView(APIView):
    def get(self, request):
        topic = request.query_params.get("topic")
        stories = list_feed_articles(topic=topic, limit=30)
        poll = get_active_poll()
        return Response(
            {
                "stories": AutomatedStorySerializer(stories, many=True).data,
                "poll": DailyPollSerializer(poll).data if poll else None,
            },
            status=status.HTTP_200_OK,
        )


class PollVoteAPIView(APIView):
    def post(self, request, poll_id: int):
        serializer = PollVoteInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            poll = record_poll_vote(poll_id=poll_id, option_id=serializer.validated_data["optionId"])
            return Response(
                {
                    "message": "Vote recorded.",
                    "poll": DailyPollSerializer(poll).data,
                },
                status=status.HTTP_200_OK,
            )
        except ValidationError:
            raise
        except Exception as exc:
            return Response(
                {"message": "Failed to record vote.", "detail": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TenantSyncAPIView(APIView):
    def post(self, request):
        expected_key = settings.SYNC_API_KEY
        provided_key = request.headers.get("X-Sync-Key", "").strip()
        if expected_key and provided_key != expected_key:
            return Response({"detail": "Invalid sync key."}, status=status.HTTP_403_FORBIDDEN)

        summary = sync_all_active_portals()
        return Response(summary, status=status.HTTP_200_OK)


class IngestArticleAPIView(APIView):
    def post(self, request):
        expected_key = settings.SYNC_API_KEY
        provided_key = request.headers.get("X-Sync-Key", "").strip()
        if expected_key and provided_key != expected_key:
            return Response({"detail": "Invalid sync key."}, status=status.HTTP_403_FORBIDDEN)

        serializer = IngestArticleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            article, created = ingest_tenant_article(serializer.validated_data)
            return Response(
                {
                    "created": created,
                    "article": AutomatedStorySerializer(article).data,
                },
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
            )
        except ValidationError:
            raise
        except Exception as exc:
            return Response(
                {"message": "Failed to ingest article.", "detail": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
