from celery import shared_task
from django.utils import timezone
from requests import RequestException

from apps.reviews.models import Review
from .models import ReviewSimilarityResult, AIAnalysisTask
from .services import FastAPIClient

import redis
import json

import logging  # ✅ [추가] 로깅 사용

# ✅ [추가] logger 생성 (파일 상단에 1번만)
logger = logging.getLogger(__name__)


def get_similarity_label(score: float) -> str:
    if score > 0.7:
        return "매우 비슷"
    if score > 0.5:
        return "비슷"
    if score > 0.3:
        return "약간 비슷"
    return "관련 있음"


@shared_task(
    bind=True,
    autoretry_for=(RequestException,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def analyze_review_similarity_task(
    self, review_id: int, requested_by_id: int | None = None
):
    """
    기준 리뷰 1개를 기준으로 같은 상품 내 다른 리뷰들과 유사도 분석 후
    ReviewSimilarityResult에 저장하는 Celery task

    추가 기능:
    - 작업 완료 후 Redis publish
    - FastAPI WebSocket 서버가 이 신호를 받아 클라이언트에 전달
    """
    MODEL_NAME = "upskyy/e5-small-korean"
    SIMILARITY_THRESHOLD = 0.45

    # ✅ [추가] task 시작 로그
    logger.info(f"[START] Task 시작 | task_id={self.request.id} review_id={review_id}")

    # Redis 연결 객체 생성
    # Docker Compose에서 서비스명이 redis 라면 host='redis' 사용
    redis_client = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)

    # task_id 기준으로 상태 레코드 조회
    task_status = AIAnalysisTask.objects.get(task_id=self.request.id)
    task_status.status = AIAnalysisTask.STATUS_STARTED
    task_status.started_at = timezone.now()
    task_status.error_message = ""
    task_status.save(update_fields=["status", "started_at", "error_message"])

    try:
        source_review = Review.objects.select_related("user", "product").get(
            id=review_id,
            is_public=True,
        )

        # ✅ [추가] source 리뷰 로그
        logger.info(f"[SOURCE] 기준 리뷰 조회 완료 | review_id={source_review.id}")

        if not source_review.content.strip():
            raise ValueError("분석할 리뷰 내용이 없습니다.")

        candidate_reviews = (
            Review.objects.select_related("user")
            .filter(
                product=source_review.product,
                is_public=True,
            )
            .exclude(id=source_review.id)
            .order_by("-created_at")[:20]
        )

        # ✅ [추가] 후보 개수 로그
        logger.info(f"[CANDIDATES] 후보 리뷰 개수={candidate_reviews.count()}")

        task_status.candidate_count = candidate_reviews.count()
        task_status.save(update_fields=["candidate_count"])

        results = []

        for candidate in candidate_reviews:
            if not candidate.content.strip():
                continue

            # ✅ [추가] 각 리뷰 비교 시작 로그
            logger.debug(f"[COMPARE] 비교 시작 | candidate_id={candidate.id}")

            similarity_result = FastAPIClient.get_similarity(
                source_review.content,
                candidate.content,
            )

            score = round(similarity_result["similarity"], 4)

            # ✅ [추가] score 로그
            logger.debug(f"[SCORE] candidate_id={candidate.id} score={score}")

            if score < SIMILARITY_THRESHOLD:
                continue

            similarity_label = get_similarity_label(score)

            saved_result, _ = ReviewSimilarityResult.objects.update_or_create(
                source_review=source_review,
                compared_review=candidate,
                model_name=MODEL_NAME,
                defaults={
                    "product": source_review.product,
                    "requested_by_id": requested_by_id,
                    "similarity_score": score,
                    "similarity_label": similarity_label,
                    "similarity_threshold": SIMILARITY_THRESHOLD,
                    "source_review_snapshot": source_review.content,
                    "compared_review_snapshot": candidate.content,
                    "compared_username_snapshot": candidate.user.username,
                },
            )

            # ✅ [추가] DB 저장 로그
            logger.info(
                f"[SAVE] 유사도 저장 | candidate_id={candidate.id} score={score}"
            )

            results.append(
                {
                    "analysis_id": saved_result.id,
                    "review_id": candidate.id,
                    "username": candidate.user.username,
                    "content": candidate.content,
                    "score": score,
                    "label": similarity_label,
                    "created_at": candidate.created_at.strftime("%Y-%m-%d %H:%M"),
                }
            )

        results.sort(key=lambda x: x["score"], reverse=True)
        top_results = results[:3]

        task_status.status = AIAnalysisTask.STATUS_SUCCESS
        task_status.result_count = len(top_results)
        task_status.finished_at = timezone.now()
        task_status.save(update_fields=["status", "result_count", "finished_at"])

        # ✅ [추가] 완료 로그
        logger.info(
            f"[SUCCESS] Task 완료 | 결과 수={len(top_results)} task_id={self.request.id}"
        )

        response_data = {
            "source_review": {
                "review_id": source_review.id,
                "username": source_review.user.username,
                "content": source_review.content,
            },
            "similar_reviews": top_results,
            "candidate_count": candidate_reviews.count(),
            "similarity_threshold": SIMILARITY_THRESHOLD,
            "model_name": MODEL_NAME,
            "task_id": self.request.id,
            "status": "SUCCESS",
        }

        # ✅ [추가] Redis publish 로그
        logger.info(f"[REDIS] 결과 publish | channel=task_result_{self.request.id}")

        # 분석 완료 신호를 Redis publish
        redis_client.publish(
            f"task_result_{self.request.id}",
            json.dumps(response_data, ensure_ascii=False),
        )

        return response_data

    except Exception as e:

        # ✅ [추가] 에러 로그 (stack trace 포함)
        logger.exception(
            f"[ERROR] Task 실패 | task_id={self.request.id} error={str(e)}"
        )

        task_status.status = AIAnalysisTask.STATUS_FAILURE
        task_status.error_message = str(e)
        task_status.finished_at = timezone.now()
        task_status.save(update_fields=["status", "error_message", "finished_at"])

        error_data = {
            "task_id": self.request.id,
            "status": "FAILURE",
            "error": str(e),
        }

        # 실패 신호도 Redis publish
        redis_client.publish(
            f"task_result_{self.request.id}",
            json.dumps(error_data, ensure_ascii=False),
        )

        raise
