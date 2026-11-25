from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import DailyPoll, PollOption, TenantArticle, TenantPortal
from .services import sync_portal_articles


class TenantFeedAPITest(APITestCase):
    def setUp(self):
        self.active_portal = TenantPortal.objects.create(
            name="Canvas Media 24",
            slug="canvasmedia24",
            domain="canvasmedia24.com",
            source_type=TenantPortal.SourceType.NEWSPAPER_API,
            is_active=True,
        )
        self.inactive_portal = TenantPortal.objects.create(
            name="Paused Portal",
            slug="pausedportal",
            domain="pausedportal.com",
            is_active=False,
        )
        self.article = TenantArticle.objects.create(
            portal=self.active_portal,
            external_id="101",
            title="Breaking Dhaka Metro Update",
            summary="New trains start next week.",
            topic=TenantArticle.Topic.NATIONAL,
            article_url="https://canvasmedia24.com/news/dhaka-metro",
            image_url="https://res.cloudinary.com/demo/image/upload/sample.jpg",
            is_breaking=True,
        )
        TenantArticle.objects.create(
            portal=self.inactive_portal,
            external_id="202",
            title="Hidden Inactive Portal Story",
            summary="Should not show.",
            topic=TenantArticle.Topic.NATIONAL,
            article_url="https://pausedportal.com/news/hidden",
        )
        self.poll = DailyPoll.objects.create(question="Top topic today?", is_active=True)
        self.opt1 = PollOption.objects.create(poll=self.poll, label="National", votes=5)
        self.opt2 = PollOption.objects.create(poll=self.poll, label="Economy", votes=3)

    def test_trending_returns_only_active_tenant_articles(self):
        response = self.client.get(reverse("trending-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["items"][0]["headline"], "Breaking Dhaka Metro Update")
        self.assertEqual(response.data["items"][0]["sourceName"], "Canvas Media 24")

    def test_feed_returns_stories_and_active_poll(self):
        response = self.client.get(reverse("feed-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["stories"]), 1)
        self.assertEqual(response.data["stories"][0]["imageUrl"], self.article.image_url)
        self.assertEqual(response.data["poll"]["totalVotes"], 8)

    def test_poll_vote_increments_vote_count(self):
        url = reverse("poll-vote", kwargs={"poll_id": self.poll.id})
        response = self.client.post(url, {"optionId": self.opt1.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.opt1.refresh_from_db()
        self.assertEqual(self.opt1.votes, 6)
        self.assertEqual(response.data["poll"]["totalVotes"], 9)

    @patch("feed.services.fetch_json_url")
    def test_sync_portal_articles_skips_internal_and_creates_published(self, mock_fetch):
        mock_fetch.return_value = [
            {
                "id": 9001,
                "title": "Tenant Published Story",
                "slug": "tenant-published-story",
                "status": "PUBLISHED",
                "is_internal": False,
                "is_breaking": True,
                "ai_summary": "Short tenant summary.",
                "category": {"name": "Economy"},
                "featured_image_url": "https://cdn.example.com/img.jpg",
                "published_at": "2026-11-25T10:00:00Z",
            },
            {
                "id": 9002,
                "title": "Internal Story",
                "slug": "internal-story",
                "status": "PUBLISHED",
                "is_internal": True,
            },
        ]

        result = sync_portal_articles(self.active_portal)
        self.assertEqual(result["created"], 1)
        saved = TenantArticle.objects.get(portal=self.active_portal, external_id="9001")
        self.assertEqual(saved.topic, TenantArticle.Topic.ECONOMY)
        self.assertEqual(saved.article_url, "https://canvasmedia24.com/news/tenant-published-story")

    def test_ingest_article_auto_creates_portal_and_respects_sync_key(self):
        payload = {
            "portal_slug": "banglaguardian",
            "portal_name": "Bangla Guardian",
            "portal_domain": "banglaguardian.com",
            "external_id": "555",
            "title": "New Education Update",
            "summary": "Board exam dates announced.",
            "topic": "Jobs",
            "article_url": "https://banglaguardian.com/article/new-education-update",
            "image_url": "https://cdn.example.com/edu.jpg",
            "is_breaking": True,
        }
        url = reverse("ingest-article")
        with self.settings(SYNC_API_KEY="secret-key"):
            denied = self.client.post(url, payload, format="json")
            self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

            ok = self.client.post(url, payload, format="json", HTTP_X_SYNC_KEY="secret-key")
            self.assertEqual(ok.status_code, status.HTTP_201_CREATED)
            self.assertTrue(TenantPortal.objects.filter(slug="banglaguardian").exists())
            self.assertEqual(ok.data["article"]["sourceName"], "Bangla Guardian")

    def test_trending_caps_each_portal_to_two_headlines(self):
        for i in range(4):
            TenantArticle.objects.create(
                portal=self.active_portal,
                external_id=f"extra-{i}",
                title=f"Canvas Story {i}",
                article_url=f"https://canvasmedia24.com/news/{i}",
            )
        second_portal = TenantPortal.objects.create(
            name="Desh Time",
            slug="deshtime",
            domain="deshtime.com",
            is_active=True,
        )
        TenantArticle.objects.create(
            portal=second_portal,
            external_id="dt-1",
            title="Desh Time Headline",
            article_url="https://deshtime.com/article/1",
        )

        response = self.client.get(reverse("trending-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sources = [item["sourceName"] for item in response.data["items"]]
        self.assertEqual(sources.count("Canvas Media 24"), 2)
        self.assertEqual(sources.count("Desh Time"), 1)
