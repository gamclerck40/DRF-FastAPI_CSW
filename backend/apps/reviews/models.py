from django.db import models
from django.conf import settings

from apps.products.models import Product
from apps.core.models import SoftDeleteModel

# [추가] 공통 Soft Delete 추상 모델 import


User = settings.AUTH_USER_MODEL


class Review(SoftDeleteModel):  # [수정] models.Model → SoftDeleteModel 상속으로 변경
    """
    제품 리뷰 모델
    - 리뷰 본문, 평점, 공개 여부 저장
    - Soft Delete 적용 대상
    """

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,  # [수정] 사용자 삭제 시 리뷰까지 지우지 않고 user만 null 처리
        null=True,  # [추가] SET_NULL 사용을 위해 필요
        blank=True,  # [추가] 관리자/폼에서 비워둘 수 있게 허용
        related_name="reviews",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,  # [수정] 상품 삭제 시 리뷰가 있으면 삭제 막음
        related_name="reviews",
    )

    content = models.TextField()  # 리뷰 내용
    rating = models.IntegerField()  # 평점
    is_public = models.BooleanField(default=True)  # 공개 여부
    created_at = models.DateTimeField(auto_now_add=True)  # 생성 시각
    updated_at = models.DateTimeField(auto_now=True)  # 수정 시각

    class Meta:
        ordering = ["-created_at"]  # 최신 리뷰가 먼저 보이도록 정렬

    def __str__(self):
        # user가 삭제되어 null일 수도 있으므로 안전하게 처리
        username = self.user.username if self.user else "탈퇴한 사용자"
        return f"{self.product} - {username}"


class ReviewImage(models.Model):
    """
    리뷰 이미지 모델
    - 리뷰 1개에 여러 이미지가 연결될 수 있음
    """

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,  # 리뷰가 완전 삭제(hard delete)되면 이미지도 함께 삭제
        related_name="images",
    )
    image = models.ImageField(upload_to="reviews/")  # 업로드 이미지 파일
    created_at = models.DateTimeField(auto_now_add=True)  # 업로드 시각

    def __str__(self):
        return f"ReviewImage(review_id={self.review_id})"


class ReviewAI(models.Model):
    """
    리뷰 AI 분석 결과 모델
    - 리뷰 1개당 AI 결과 1개 저장
    """

    review = models.OneToOneField(
        Review,
        on_delete=models.CASCADE,  # 리뷰가 완전 삭제(hard delete)되면 AI 결과도 함께 삭제
        related_name="ai_result",
    )
    sentiment = models.CharField(max_length=50)  # 감정 분석 결과
    confidence = models.FloatField()  # 예측 신뢰도
    keywords = models.JSONField(blank=True, null=True)  # 핵심 키워드 목록
    created_at = models.DateTimeField(auto_now_add=True)  # 분석 생성 시각

    def __str__(self):
        return f"ReviewAI(review_id={self.review_id})"
