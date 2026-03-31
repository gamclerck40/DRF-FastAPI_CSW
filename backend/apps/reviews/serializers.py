from rest_framework import serializers

from .models import Review, ReviewImage


class ReviewImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ReviewImage
        fields = [
            "id",
            "image",
            "image_url",
            "created_at",
        ]

    def get_image_url(self, obj):
        request = self.context.get("request")

        if not obj.image:
            return None

        try:
            image_url = obj.image.url
        except Exception:
            return None

        if request:
            return request.build_absolute_uri(image_url)

        return image_url


class ReviewAISerializer(serializers.Serializer):
    sentiment = serializers.CharField(read_only=True)
    score = serializers.FloatField(read_only=True)
    summary = serializers.CharField(read_only=True, required=False)
    keywords = serializers.ListField(
        child=serializers.CharField(), read_only=True, required=False
    )


class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    # =========================================================
    # [인터랙티브 추가]
    # 좋아요 개수 표시용 필드
    # =========================================================
    likes_count = serializers.SerializerMethodField()

    # =========================================================
    # [인터랙티브 추가]
    # 북마크 개수 표시용 필드
    # =========================================================
    bookmarks_count = serializers.SerializerMethodField()

    # =========================================================
    # [인터랙티브 추가]
    # 현재 로그인 사용자가 이 리뷰에 좋아요를 눌렀는지 여부
    # =========================================================
    is_liked = serializers.SerializerMethodField()

    # =========================================================
    # [인터랙티브 추가]
    # 현재 로그인 사용자가 이 리뷰를 북마크했는지 여부
    # =========================================================
    is_bookmarked = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            "id",
            "user",
            "username",
            "product",
            "content",
            "rating",
            "is_public",
            "created_at",
            # =================================================
            # [인터랙티브 추가]
            # 좋아요 수
            # =================================================
            "likes_count",
            # =================================================
            # [인터랙티브 추가]
            # 북마크 수
            # =================================================
            "bookmarks_count",
            # =================================================
            # [인터랙티브 추가]
            # 현재 유저 좋아요 여부
            # =================================================
            "is_liked",
            # =================================================
            # [인터랙티브 추가]
            # 현재 유저 북마크 여부
            # =================================================
            "is_bookmarked",
        ]
        read_only_fields = [
            "id",
            "user",
            "username",
            "created_at",
            # =================================================
            # [인터랙티브 추가]
            # 계산해서 보여주는 값이라 읽기 전용
            # =================================================
            "likes_count",
            "bookmarks_count",
            "is_liked",
            "is_bookmarked",
        ]

    # =========================================================
    # [인터랙티브 추가]
    # 해당 리뷰의 좋아요 개수 반환
    # related_name='likes' 기준
    # =========================================================
    def get_likes_count(self, obj):
        return obj.likes.count()

    # =========================================================
    # [인터랙티브 추가]
    # 해당 리뷰의 북마크 개수 반환
    # related_name='bookmarks' 기준
    # =========================================================
    def get_bookmarks_count(self, obj):
        return obj.bookmarks.count()

    # =========================================================
    # [인터랙티브 추가]
    # 현재 로그인한 사용자가 이 리뷰에 좋아요를 눌렀는지 확인
    # 비로그인 사용자는 False
    # =========================================================
    def get_is_liked(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.likes.filter(user=request.user).exists()

    # =========================================================
    # [인터랙티브 추가]
    # 현재 로그인한 사용자가 이 리뷰를 북마크했는지 확인
    # 비로그인 사용자는 False
    # =========================================================
    def get_is_bookmarked(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.bookmarks.filter(user=request.user).exists()
