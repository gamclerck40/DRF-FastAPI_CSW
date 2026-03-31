from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("products/", include("apps.products.urls")),
    path("reviews/", include("apps.reviews.urls")),
    path("accounts/", include("apps.accounts.urls")),  # ✅ 추가
    path("api/products/", include("apps.products.urls")),  # ✅ 추가
    path("api/reviews/", include("apps.reviews.urls")),  # ✅ 추가
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
