from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework import permissions, status, viewsets, generics
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Review, ReviewImage
from .serializers import (
    ReviewSerializer,
    ReviewImageSerializer,
    ReviewAISerializer,
)


class ReviewViewSet(viewsets.ModelViewSet):
    """
    리뷰 CRUD API

    지원 기능
    - GET    /api/reviews/                : 리뷰 목록
    - GET    /api/reviews/?product=1      : 특정 상품 리뷰 목록
    - GET    /api/reviews/<id>/           : 리뷰 상세
    - POST   /api/reviews/                : 리뷰 생성
    - PATCH  /api/reviews/<id>/           : 리뷰 수정
    - DELETE /api/reviews/<id>/           : 리뷰 삭제
    """

    # =========================================================
    # [인터랙티브 관련]
    # ReviewSerializer 안에
    # likes_count, bookmarks_count, is_liked, is_bookmarked
    # 가 추가되어 있다면,
    # 이 ViewSet의 목록/상세 응답에도 그 값들이 함께 내려가게 됩니다.
    # 즉, View 코드 자체보다 serializer 확장의 영향이 반영되는 부분입니다.
    # =========================================================
    serializer_class = ReviewSerializer

    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        """
        조회는 누구나 가능,
        생성/수정/삭제는 로그인 사용자만 가능하게 설정
        """
        if self.action in ["list", "retrieve"]:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        기본적으로 공개 리뷰만 조회하고,
        product 쿼리파라미터가 있으면 해당 상품 리뷰만 필터링합니다.
        """
        queryset = (
            Review.objects.select_related("user", "product", "ai_result")
            .prefetch_related("images")
            .filter(is_public=True)
            .order_by("-created_at")
        )

        product_id = self.request.query_params.get("product")
        if product_id:
            queryset = queryset.filter(product_id=product_id)

        return queryset

    def perform_create(self, serializer):
        """
        로그인 사용자의 리뷰를 저장합니다.
        """
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user, is_public=True)
        else:
            raise ValidationError("리뷰 작성은 로그인 후 가능합니다.")

    def destroy(self, request, *args, **kwargs):
        """
        삭제 응답 메시지 커스텀
        """
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"message": "deleted"}, status=status.HTTP_200_OK)


# =============================================================
# [인터랙티브 관련]
# 사용자 본인이 작성한 리뷰만 따로 조회하는 기능
# 좋아요/북마크와 직접 토글하는 API는 아니지만,
# 인터랙션이 붙은 리뷰 데이터를 "내 리뷰" 기준으로 확인하는 흐름에서
# 함께 사용될 수 있는 확장 기능입니다.
# =============================================================
class MyReviewListAPIView(generics.ListAPIView):
    """
    내 리뷰 목록
    GET /api/reviews/my/
    """

    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Review.objects.select_related("user", "product", "ai_result")
            .prefetch_related("images")
            .filter(user=self.request.user)
            .order_by("-created_at")
        )


class ReviewImageUploadAPIView(APIView):
    """
    특정 리뷰에 이미지 추가 업로드
    POST /api/reviews/<review_id>/images/
    """

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, review_id):
        review = get_object_or_404(Review, id=review_id)

        # 본인 리뷰에만 이미지 추가 가능
        if review.user != request.user:
            return Response(
                {"detail": "본인 리뷰에만 이미지를 추가할 수 있습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        files = request.FILES.getlist("uploaded_images")

        if not files:
            return Response(
                {"detail": "업로드할 이미지가 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created_images = []
        for file in files:
            image = ReviewImage.objects.create(review=review, image=file)
            created_images.append(image)

        serializer = ReviewImageSerializer(created_images, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ReviewAIResultAPIView(APIView):
    """
    특정 리뷰의 AI 분석 결과 조회
    GET /api/reviews/<review_id>/ai/
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, review_id):
        review = get_object_or_404(
            Review.objects.select_related("ai_result"), id=review_id
        )

        if not hasattr(review, "ai_result"):
            return Response(
                {"detail": "AI 분석 결과가 없습니다."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = ReviewAISerializer(review.ai_result)
        return Response(serializer.data, status=status.HTTP_200_OK)
