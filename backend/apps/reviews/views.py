from django.shortcuts import get_object_or_404

from rest_framework import permissions, status, viewsets, generics
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Review, ReviewImage
from .serializers import (
    ReviewSerializer,
    ReviewImageSerializer,
    ReviewAISerializer,
)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    [유지]
    작성자만 수정/삭제 가능하게 하는 권한 클래스
    - GET, HEAD, OPTIONS 같은 읽기 요청은 모두 허용
    - PUT, PATCH, DELETE 같은 수정 요청은 작성자만 허용
    """

    def has_object_permission(self, request, view, obj):
        # [유지]
        # 읽기 요청은 누구나 허용
        if request.method in permissions.SAFE_METHODS:
            return True

        # [유지]
        # 수정/삭제는 작성자 본인만 허용
        return obj.user == request.user


class ReviewViewSet(viewsets.ModelViewSet):
    """
    [수정]
    리뷰 CRUD API
    - 목록 조회
    - 상세 조회
    - 생성
    - 수정
    - 삭제

    현재 삭제 정책 변경 중:
    - 예전: DELETE 시 DB에서 실제 삭제(물리 삭제)
    - 지금: DELETE 시 is_deleted=True 처리(논리 삭제, Soft Delete)
    """

    serializer_class = ReviewSerializer

    # [유지]
    # 리뷰 생성/수정 시 일반 폼 데이터 + 파일 업로드 둘 다 받을 수 있게 설정
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        """
        [유지]
        요청 종류(action)에 따라 권한을 다르게 적용
        - list, retrieve: 누구나 조회 가능
        - create, update, partial_update, destroy: 로그인 필요 + 작성자 권한 검사
        """
        if self.action in ["list", "retrieve"]:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        [수정]
        리뷰 조회용 기본 queryset

        Soft Delete 정책 변경 반영:
        - Review.objects 는 살아있는 데이터만 조회하는 기본 매니저
        - 따라서 삭제된 리뷰(is_deleted=True)는 자동으로 제외됨

        추가 기능:
        - user, product, ai_result는 JOIN 최적화
        - images, likes, bookmarks는 미리 조회해서 성능 개선
        - 공개 리뷰(is_public=True)만 노출
        - 최신순 정렬
        - product 쿼리파라미터가 있으면 상품별 필터링
        """
        queryset = (
            Review.objects.select_related(  # [수정] Soft Delete 기본 매니저 사용
                "user", "product", "ai_result"
            )
            .prefetch_related("images", "likes", "bookmarks")
            .filter(is_public=True)
            .order_by("-created_at")
        )

        # [유지]
        # /reviews/?product=1 형태로 들어오면 해당 상품 리뷰만 조회
        product_id = self.request.query_params.get("product")
        if product_id:
            queryset = queryset.filter(product_id=product_id)

        return queryset

    def get_serializer_context(self):
        """
        [유지]
        serializer 안에서 request를 사용할 수 있도록 context에 담아 전달
        - 이미지 절대 URL 생성
        - 현재 사용자 기준 좋아요/북마크 여부 계산
        """
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def perform_create(self, serializer):
        """
        [유지]
        리뷰 생성 시 자동으로 현재 로그인 사용자를 작성자로 저장
        - 프론트에서 user를 직접 보내지 않아도 됨
        - 기본 공개 상태(is_public=True)로 저장
        """
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user, is_public=True)
        else:
            raise ValidationError("리뷰 작성은 로그인 후 가능합니다.")

    def perform_update(self, serializer):
        """
        [유지]
        리뷰 수정 시 작성자 본인인지 한 번 더 확인
        - 권한 클래스가 있어도 안전하게 추가 검증
        """
        review = self.get_object()

        if review.user != self.request.user:
            raise PermissionDenied("본인 리뷰만 수정할 수 있습니다.")

        serializer.save()

    def destroy(self, request, *args, **kwargs):
        """
        [핵심 수정]
        삭제 정책 변경 부분

        예전 방식:
        - instance.delete() 가 물리 삭제였다면 DB에서 진짜 삭제됨

        지금 방식:
        - Review가 SoftDeleteModel을 상속받고
        - delete()가 논리 삭제로 바뀌었으므로
        - 여기서 instance.delete()를 호출하면
          실제 삭제가 아니라 is_deleted=True 로 변경됨
        """
        instance = self.get_object()

        # [유지]
        # 작성자 본인만 삭제 가능
        if instance.user != request.user:
            return Response(
                {"detail": "본인 리뷰만 삭제할 수 있습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # [수정]
        # 물리 삭제 대신 soft delete 수행
        instance.delete()

        # [수정]
        # 프론트가 soft delete 여부를 알 수 있도록 응답 명시
        return Response(
            {
                "message": "리뷰가 삭제되었습니다.",
                "soft_deleted": True,
            },
            status=status.HTTP_200_OK,
        )


class MyReviewListAPIView(generics.ListAPIView):
    """
    [유지 + Soft Delete 영향 있음]
    내 리뷰 목록 조회 API
    - 로그인한 사용자의 리뷰만 보여줌
    - Review.objects 를 쓰므로 soft delete 된 리뷰는 자동 제외됨
    """

    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        [수정 의미 있음]
        현재 로그인한 사용자의 리뷰만 조회
        - 삭제된 리뷰는 Soft Delete 기본 매니저 때문에 자동으로 빠짐
        """
        return (
            Review.objects.select_related(  # [수정 의미] soft delete 반영된 기본 매니저
                "user", "product", "ai_result"
            )
            .prefetch_related("images", "likes", "bookmarks")
            .filter(user=self.request.user)
            .order_by("-created_at")
        )

    def get_serializer_context(self):
        """
        [유지]
        serializer 내부에서 request 사용 가능하게 전달
        """
        return {"request": self.request}


class ReviewImageUploadAPIView(APIView):
    """
    [유지]
    리뷰 이미지 업로드 API
    - 로그인한 사용자만 가능
    - 본인 리뷰에만 이미지 추가 가능
    - 여러 장 업로드 가능
    """

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, review_id):
        """
        [유지 + Soft Delete 간접 반영]
        review_id에 해당하는 리뷰를 찾아 이미지 업로드

        Soft Delete 영향:
        - get_object_or_404(Review, id=review_id) 에서 Review.objects 사용
        - 따라서 삭제된 리뷰는 찾지 못함
        - 즉, 삭제된 리뷰에는 이미지 업로드가 자동 차단됨
        """
        review = get_object_or_404(Review, id=review_id)

        # [유지]
        # 본인 리뷰에만 이미지 업로드 가능
        if review.user != request.user:
            return Response(
                {"detail": "본인 리뷰에만 이미지를 추가할 수 있습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # [유지]
        # 프론트에서 uploaded_images 이름으로 여러 파일 받기
        files = request.FILES.getlist("uploaded_images")

        # [유지]
        # 파일이 없으면 예외 응답
        if not files:
            return Response(
                {"detail": "업로드할 이미지가 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # [유지]
        # 여러 파일을 순회하며 DB에 저장
        created_images = []
        for file in files:
            image = ReviewImage.objects.create(
                review=review,
                image=file,
            )
            created_images.append(image)

        # [유지]
        # 저장된 이미지 목록을 serializer로 변환 후 응답
        serializer = ReviewImageSerializer(
            created_images,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ReviewAIResultAPIView(APIView):
    """
    [유지 + Soft Delete 간접 반영]
    특정 리뷰의 AI 분석 결과 조회 API
    - 공개 조회 허용
    - 삭제된 리뷰는 기본 매니저 때문에 조회되지 않음
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, review_id):
        """
        [유지 + 수정 의미 있음]
        review_id에 해당하는 리뷰의 AI 결과를 반환

        Soft Delete 영향:
        - Review.objects.select_related("ai_result") 사용
        - 삭제된 리뷰는 자동 제외
        """
        review = get_object_or_404(
            Review.objects.select_related("ai_result"),
            id=review_id,
        )

        # [유지]
        # AI 결과가 아직 없으면 404 반환
        if not hasattr(review, "ai_result"):
            return Response(
                {"detail": "AI 분석 결과가 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # [유지]
        # AI 결과를 serializer로 변환해서 응답
        serializer = ReviewAISerializer(review.ai_result)
        return Response(serializer.data, status=status.HTTP_200_OK)
