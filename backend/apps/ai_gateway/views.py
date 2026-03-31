from rest_framework.views import APIView
from rest_framework.response import Response


class SentimentAnalysisAPIView(APIView):

    def post(self, request):
        text = request.data.get("text")
        return Response({"message": "AI 분석 요청", "text": text})
