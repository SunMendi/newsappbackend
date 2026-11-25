from django.urls import path

from .views import FeedAPIView, IngestArticleAPIView, PollVoteAPIView, TenantSyncAPIView, TrendingListAPIView

urlpatterns = [
    path("trending/", TrendingListAPIView.as_view(), name="trending-list"),
    path("feed/", FeedAPIView.as_view(), name="feed-list"),
    path("polls/<int:poll_id>/vote/", PollVoteAPIView.as_view(), name="poll-vote"),
    path("sync/tenants/", TenantSyncAPIView.as_view(), name="tenant-sync"),
    path("ingest/article/", IngestArticleAPIView.as_view(), name="ingest-article"),
]
