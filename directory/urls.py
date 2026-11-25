from django.urls import path

from .views import NewspaperListAPIView

urlpatterns = [
    path("newspapers/", NewspaperListAPIView.as_view(), name="newspaper-list"),
]
