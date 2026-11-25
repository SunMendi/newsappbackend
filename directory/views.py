from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import NewspaperResponseSerializer
from .services import list_active_newspapers


class NewspaperListAPIView(APIView):
    def get(self, request):
        category = request.query_params.get("category")
        newspapers = list_active_newspapers(category=category)
        serializer = NewspaperResponseSerializer(newspapers, many=True)
        return Response({"items": serializer.data}, status=status.HTTP_200_OK)
