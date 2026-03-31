from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from apps.products.models import Product


User = settings.AUTH_USER_MODEL


class Review(models.Model):
    """
    제품 리뷰
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reviews"
    )

    content = models.TextField()

    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    is_public = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product} - {self.user}"


class ReviewImage(models.Model):
    """
    리뷰 이미지
    """

    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="images")

    image = models.ImageField(upload_to="reviews/")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"ReviewImage(review_id={self.review.id}, id={self.id})"


class ReviewAI(models.Model):
    """
    리뷰 AI 분석 결과
    """

    review = models.OneToOneField(
        Review, on_delete=models.CASCADE, related_name="ai_result"
    )

    sentiment = models.CharField(max_length=50)

    confidence = models.FloatField()

    keywords = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"ReviewAI(review_id={self.review.id}, sentiment={self.sentiment})"
