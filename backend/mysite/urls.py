from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path("admin/", admin.site.urls),
    # 🔥 [추가] Prometheus metrics 엔드포인트
    path("", include("django_prometheus.urls")),
    path("products/", include("apps.products.urls")),
    path("reviews/", include("apps.reviews.urls")),
    path("accounts/", include("apps.accounts.urls")),  # ✅ 추가
    path("api/products/", include("apps.products.urls")),  # ✅ 추가
    path("api/reviews/", include("apps.reviews.urls")),  # ✅ 추가
    path("ai/", include("apps.ai_gateway.urls")),  # ← 이게 빠진 것
    path("interactions/", include("apps.interactions.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
