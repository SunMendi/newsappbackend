from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Newspaper
from .services import create_newspaper, seed_default_newspapers


class NewspaperAPITest(APITestCase):
    def test_list_returns_only_active_newspapers(self):
        create_newspaper(
            {
                "slug": "prothom-alo",
                "name": "Prothom Alo",
                "bangla_name": "প্রথম আলো",
                "url": "https://www.prothomalo.com",
                "category": Newspaper.Category.BANGLA,
                "sort_order": 1,
            }
        )
        Newspaper.objects.create(
            slug="hidden-paper",
            name="Hidden",
            url="https://hidden.example.com",
            category=Newspaper.Category.BANGLA,
            is_active=False,
        )

        url = reverse("newspaper-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["items"][0]["id"], "prothom-alo")
        self.assertEqual(response.data["items"][0]["banglaName"], "প্রথম আলো")

    def test_seed_default_newspapers_is_idempotent(self):
        first = seed_default_newspapers()
        second = seed_default_newspapers()
        self.assertGreater(first["created"], 40)
        self.assertEqual(second["created"], 0)
