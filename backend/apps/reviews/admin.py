# apps/reviews/admin.py

from django.contrib import admin
from .models import Review, ReviewImage, ReviewAI


# [추가]
# 관리자에서 선택한 리뷰를 복구하는 액션
@admin.action(description="선택한 리뷰 복구")
def restore_reviews(modeladmin, request, queryset):
    for obj in queryset:
        obj.restore()  # Soft Delete 복구


# [추가]
# 관리자에서 선택한 리뷰를 진짜 DB에서 삭제하는 액션
@admin.action(description="선택한 리뷰 완전 삭제")
def hard_delete_reviews(modeladmin, request, queryset):
    for obj in queryset:
        obj.hard_delete()  # 물리 삭제


# [추가]
# 관리자에서 선택한 리뷰를 논리 삭제하는 액션
@admin.action(description="선택한 리뷰 삭제(논리 삭제)")
def soft_delete_reviews(modeladmin, request, queryset):
    for obj in queryset:
        obj.delete()  # Soft Delete 실행


class ReviewImageInline(admin.TabularInline):
    # [유지]
    # 리뷰 상세 화면에서 연결된 이미지들을 함께 보이게 함
    model = ReviewImage
    extra = 0


class ReviewAIInline(admin.StackedInline):
    # [유지]
    # 리뷰 상세 화면에서 AI 결과를 함께 보이게 함
    model = ReviewAI
    extra = 0
    can_delete = False  # [유지] 인라인에서 AI 결과 직접 삭제 방지


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    # [수정]
    # 목록에서 soft delete 관련 필드까지 보이도록 확장
    list_display = [
        "id",
        "product",
        "user",
        "rating",
        "is_public",
        "is_deleted",  # [추가] 삭제 여부 확인용
        "deleted_at",  # [추가] 삭제 시각 확인용
        "created_at",
    ]

    # [수정]
    # 삭제 여부로 필터링 가능하게 추가
    list_filter = [
        "is_public",
        "is_deleted",  # [추가]
        "created_at",
    ]

    # [유지]
    # 검색 필드
    search_fields = ["content", "product__name", "user__username"]

    # [추가]
    # 관리자 액션에 soft delete / restore / hard delete 추가
    actions = [soft_delete_reviews, restore_reviews, hard_delete_reviews]

    # [유지]
    # 리뷰 상세 화면에 이미지/AI 결과 함께 표시
    inlines = [ReviewImageInline, ReviewAIInline]

    def get_queryset(self, request):
        # [수정]
        # 기본 Review.objects 대신 Review.all_objects 사용
        # → 삭제된 리뷰도 관리자에서 보이게 함
        return Review.all_objects.select_related("user", "product").all()

    def delete_model(self, request, obj):
        # [수정]
        # 관리자 상세 화면에서 delete 시 물리 삭제가 아니라 soft delete 되도록 변경
        obj.delete()

    def delete_queryset(self, request, queryset):
        # [수정]
        # 관리자 목록에서 여러 개 삭제해도 물리 삭제가 아니라 soft delete 되도록 변경
        for obj in queryset:
            obj.delete()
