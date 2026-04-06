from django.urls import path
from .views import (
    EmbeddingAPIView,
    SimilarityAPIView,
    ReviewAnalyzeAPIView,
    ReviewAnalyzeTaskStatusAPIView,
)

urlpatterns = [
    path("embed/", EmbeddingAPIView.as_view(), name="ai-embed"),
    path("similarity/", SimilarityAPIView.as_view(), name="ai-similarity"),
    path(
        "reviews/<int:review_id>/analyze/",
        ReviewAnalyzeAPIView.as_view(),
        name="ai-review-analyze",
    ),
    # [추가] Celery 작업 상태 조회
    path(
        "tasks/<str:task_id>/status/",
        ReviewAnalyzeTaskStatusAPIView.as_view(),
        name="ai-task-status",
    ),
]
