# apps/crawling/services/crawl_service.py

# [유지] 사이트별 collector import
from apps.crawling.collectors.danawa_collector import collect_danawa_search
from apps.crawling.collectors.hwahae_collector import collect_hwahae_search
from apps.crawling.collectors.glowpick_collector import collect_glowpick_search

# [유지] 저장 서비스 사용
from apps.crawling.services.save_service import save_search_result


def crawl_search_target(target) -> dict:
    """
    [유지]
    - site에 따라 collector 선택
    - 저장은 save_service에 맡기고
    - 여기서는 결과 요약만 반환
    """

    if target.site == "danawa":
        result = collect_danawa_search(target)

    elif target.site == "hwahae":
        result = collect_hwahae_search(target)

    elif target.site == "glowpick":
        result = collect_glowpick_search(target)

    else:
        raise ValueError(f"지원하지 않는 사이트입니다: {target.site}")

    save_result = save_search_result(target, result)

    return {
        "page_title": save_result["page_title"],
        "candidate_count": save_result["candidate_count"],
        "created_count": save_result["created_count"],
        "updated_count": save_result["updated_count"],
        # [추가] product target 생성 결과도 함께 반환
        "created_product_targets": save_result["created_product_targets"],
        "reactivated_product_targets": save_result["reactivated_product_targets"],
    }
