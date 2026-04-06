# [유지] 해시 / transaction / timezone 사용
import hashlib

from django.db import transaction
from django.utils import timezone

# [추가] product target 생성을 위해 CrawlTarget import
from apps.crawling.models import CrawlTarget
from apps.crawling.services.repository import upsert_raw_data


def make_hash(value: str) -> str:
    """
    문자열을 SHA256 해시값(64자리 고정 길이)으로 변환합니다.
    """
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_page_info_unique_key(target) -> str:
    raw = f"{target.site}:page_info:{target.url}"
    return make_hash(raw)


def build_candidate_unique_key(target, item_url: str) -> str:
    raw = f"{target.site}:candidate_link:{item_url}"
    return make_hash(raw)


def build_page_info_defaults(target, result: dict) -> dict:
    """
    page_info 레코드 저장용 defaults 조립
    """
    page_info = result["page_info"]
    html = result["html"]

    return {
        "target": target,
        "source_url": target.url,
        "page_title": page_info["title"][:500],
        "item_title": "",
        "item_url": "",
        "raw_text": page_info["text_preview"],
        "raw_html": html[:5000],
        "record_type": "page_info",
        "extra_data": {
            "a_count": page_info["a_count"],
            "contains_review_word": page_info["contains_review_word"],
            "contains_keyword": page_info["contains_keyword"],
        },
    }


def build_candidate_defaults(target, page_title: str, item: dict) -> dict:
    """
    candidate_link 레코드 저장용 defaults 조립
    """
    return {
        "target": target,
        "source_url": target.url,
        "page_title": page_title[:500],
        "item_title": item["title"][:500],
        "item_url": item["url"],
        "raw_text": "",
        "raw_html": "",
        "record_type": "candidate_link",
        "extra_data": {},
    }


# [추가] candidate_link -> product target 생성 함수
def create_product_targets_from_candidates(target, candidate_links: list[dict]) -> dict:
    """
    search 결과의 candidate_link를 product CrawlTarget으로 승격합니다.
    """
    created_count = 0
    reactivated_count = 0

    for item in candidate_links:
        item_url = (item.get("url") or "").strip()
        item_title = (item.get("title") or "").strip()

        if not item_url:
            continue

        defaults = {
            "site": target.site,
            "target_type": "product",
            "keyword": target.keyword,
            "title": item_title[:255] if item_title else f"{target.site} 상품 상세",
            "is_active": True,
        }

        # [유지/호환] 5단계 필드가 이미 models.py에 있다면 함께 반영
        if hasattr(target, "crawl_interval_minutes"):
            defaults["crawl_interval_minutes"] = target.crawl_interval_minutes

        if hasattr(target, "priority"):
            defaults["priority"] = target.priority

        product_target, created = CrawlTarget.objects.get_or_create(
            url=item_url,
            defaults=defaults,
        )

        if created:
            created_count += 1
        else:
            # [추가] 기존 target이 비활성화 상태면 다시 켜기
            if not product_target.is_active:
                product_target.is_active = True
                product_target.save(update_fields=["is_active"])
                reactivated_count += 1

    return {
        "created_product_targets": created_count,
        "reactivated_product_targets": reactivated_count,
    }


@transaction.atomic
def save_search_result(target, result: dict) -> dict:
    """
    검색 결과를 DB에 저장하되,
    - page_info는 unique_key로 1건 유지
    - candidate_link는 item_url 기준으로 중복 저장 방지
    - [추가] candidate_link를 product target으로도 생성
    """
    created_count = 0
    updated_count = 0

    page_info = result["page_info"]
    candidate_links = result["candidate_links"]

    # 1. 페이지 정보 upsert
    page_info_key = build_page_info_unique_key(target)
    _, created = upsert_raw_data(
        unique_key=page_info_key,
        defaults={
            **build_page_info_defaults(target, result),
            "unique_key": page_info_key,
        },
    )
    if created:
        created_count += 1
    else:
        updated_count += 1

    # 2. 후보 링크 upsert
    for item in candidate_links:
        candidate_key = build_candidate_unique_key(target, item["url"])

        _, created = upsert_raw_data(
            unique_key=candidate_key,
            defaults={
                **build_candidate_defaults(target, page_info["title"], item),
                "unique_key": candidate_key,
            },
        )

        if created:
            created_count += 1
        else:
            updated_count += 1

    # 3. [추가] 후보 링크를 product target으로 생성
    product_target_summary = create_product_targets_from_candidates(
        target, candidate_links
    )

    # 4. [유지] 마지막 크롤링 시간 갱신
    target.last_crawled_at = timezone.now()
    target.save(update_fields=["last_crawled_at"])

    return {
        "page_title": page_info["title"],
        "candidate_count": len(candidate_links),
        "created_count": created_count,
        "updated_count": updated_count,
        # [추가] test_crawl에서 확인할 수 있도록 반환
        "created_product_targets": product_target_summary["created_product_targets"],
        "reactivated_product_targets": product_target_summary[
            "reactivated_product_targets"
        ],
    }
