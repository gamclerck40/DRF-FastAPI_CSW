from rest_framework import serializers

from .models import Review, ReviewImage


class ReviewImageSerializer(serializers.ModelSerializer):
    # [유지]
    # 업로드된 이미지의 실제 접근 URL을 응답에 추가하기 위한 가상 필드
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ReviewImage
        fields = [
            "id",  # 이미지 ID
            "image",  # 원본 이미지 파일 경로
            "image_url",  # [유지] 브라우저에서 바로 접근 가능한 전체 URL
            "created_at",  # 생성 시각
        ]

    def get_image_url(self, obj):
        # [유지]
        # serializer context에서 request를 꺼내 절대경로 URL 생성에 사용
        request = self.context.get("request")

        # [유지]
        # 이미지가 없으면 None 반환
        if not obj.image:
            return None

        try:
            # [유지]
            # 저장된 이미지의 상대 URL 추출
            image_url = obj.image.url
        except Exception:
            # [유지]
            # 파일이 없거나 접근 불가하면 안전하게 None 반환
            return None

        if request:
            # [유지]
            # request가 있으면 절대 URL로 변환
            # 예: http://127.0.0.1:8000/media/reviews/1.jpg
            return request.build_absolute_uri(image_url)

        # [유지]
        # request가 없으면 상대 경로 그대로 반환
        return image_url


class ReviewAISerializer(serializers.Serializer):
    """
    AI 분석 결과 응답용 serializer
    - [수정] ModelSerializer가 아니라 Serializer 사용
    - 이유: 현재 프로젝트 단계별로 AI 결과 필드명이 조금씩 다를 수 있어서
      유연하게 읽기 위해 직접 선언형으로 작성
    """

    sentiment = serializers.CharField(read_only=True)  # 감정 결과
    confidence = serializers.FloatField(read_only=True, required=False)  # [추가] 신뢰도
    score = serializers.FloatField(
        read_only=True, required=False
    )  # [추가] 다른 문서 호환용 점수
    summary = serializers.CharField(
        read_only=True, required=False
    )  # [추가] 다른 문서 호환용 요약
    keywords = serializers.ListField(
        child=serializers.CharField(),
        read_only=True,
        required=False,
    )  # [유지] 키워드 목록


class ReviewSerializer(serializers.ModelSerializer):
    # [추가]
    # user.username을 바로 노출하기 위해 가공 필드 추가
    username = serializers.SerializerMethodField()

    # [유지]
    # 리뷰 1개에 연결된 이미지 여러 개를 중첩 응답으로 포함
    images = ReviewImageSerializer(many=True, read_only=True)

    # [수정]
    # AI 결과를 안전하게 꺼내기 위해 직접 메서드 필드 사용
    ai_result = serializers.SerializerMethodField()

    # [추가]
    # 좋아요/북마크 관련 확장 응답 필드
    likes_count = serializers.SerializerMethodField()
    bookmarks_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            "id",  # 리뷰 ID
            "user",  # 작성자 ID
            "username",  # [추가] 작성자 이름
            "product",  # 상품 ID
            "content",  # 리뷰 본문
            "rating",  # 평점
            "is_public",  # 공개 여부
            "created_at",  # 생성 시각
            "updated_at",  # 수정 시각
            "images",  # [유지] 연결된 이미지 목록
            "ai_result",  # [수정] AI 분석 결과
            "likes_count",  # [추가] 좋아요 개수
            "bookmarks_count",  # [추가] 북마크 개수
            "is_liked",  # [추가] 현재 사용자의 좋아요 여부
            "is_bookmarked",  # [추가] 현재 사용자의 북마크 여부
        ]
        read_only_fields = [
            "id",
            "user",  # [유지] 작성자는 서버에서 넣음
            "username",  # [유지] 계산값
            "created_at",
            "updated_at",
            "images",  # [유지] 별도 업로드 API로 처리
            "ai_result",  # [유지] AI 결과는 직접 입력하지 않음
            "likes_count",  # [유지] 계산값
            "bookmarks_count",  # [유지] 계산값
            "is_liked",  # [유지] 계산값
            "is_bookmarked",  # [유지] 계산값
        ]

    def get_username(self, obj):
        # [수정]
        # Soft Delete 구조에서 user가 null일 수 있으므로 안전 처리
        if obj.user:
            return obj.user.username
        return "탈퇴한 사용자"

    def get_ai_result(self, obj):
        # [수정]
        # 리뷰에 연결된 ai_result가 없으면 None 반환
        if not hasattr(obj, "ai_result"):
            return None

        # [유지]
        # AI 결과가 있으면 전용 serializer로 감싸서 응답
        return ReviewAISerializer(obj.ai_result).data

    def get_likes_count(self, obj):
        # [추가]
        # 현재 리뷰에 연결된 좋아요 총 개수 반환
        return obj.likes.count()

    def get_bookmarks_count(self, obj):
        # [추가]
        # 현재 리뷰에 연결된 북마크 총 개수 반환
        return obj.bookmarks.count()

    def get_is_liked(self, obj):
        # [추가]
        # 로그인한 현재 사용자가 이 리뷰에 좋아요를 눌렀는지 확인
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            return False

        return obj.likes.filter(user=request.user).exists()

    def get_is_bookmarked(self, obj):
        # [추가]
        # 로그인한 현재 사용자가 이 리뷰를 북마크했는지 확인
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            return False

        return obj.bookmarks.filter(user=request.user).exists()
