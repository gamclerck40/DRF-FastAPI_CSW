from django.db import models


class Product(models.Model):
    """
    제품 모델
    """

    name = models.CharField(max_length=255)

    description = models.TextField(blank=True, null=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)

    image = models.ImageField(upload_to="products/", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# ✅ 추가
class ProductAI(models.Model):
    """
    제품 AI 분석 결과
    """

    product = models.OneToOneField(
        Product, on_delete=models.CASCADE, related_name="ai_result"
    )

    sentiment = models.CharField(max_length=50)
    confidence = models.FloatField()
    keywords = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ProductAI(product_id={self.product.id}, sentiment={self.sentiment})"
