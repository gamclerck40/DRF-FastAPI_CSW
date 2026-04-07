# backend/apps/crawling/services/crawl_service.py

from django.utils import timezone

from apps.crawling.models import CrawlRawData
from .http import fetch_page  # 페이지 요청 (robots + retry 포함)
from .parser import extract_page_info  # HTML 분석해서 정보 추출


def crawl_search_target(target):
    """
    검색 페이지 크롤링 함수

    전체 흐름:
    1. 페이지 요청
    2. HTML 파싱
    3. 페이지 정보 저장
    4. (있다면) 상품 링크 저장
    5. 마지막 크롤링 시간 업데이트
    """

    # 1️⃣ 페이지 요청
    # → 내부적으로 robots.txt 검사 + retry + delay 적용됨
    response = fetch_page(target.url)

    # HTML 문자열 추출
    html = response.text

    # 2️⃣ HTML 분석 (파싱)
    # → 제목, 텍스트, a 태그 개수 등 추출
    page_info = extract_page_info(html)

    # 3️⃣ 상품 링크 후보 리스트
    # ⚠ 현재는 구현 안되어 있어서 빈 리스트
    candidate_links = []

    # 4️⃣ 페이지 전체 정보 저장 (로그 성격)
    CrawlRawData.objects.create(
        target=target,  # 어떤 크롤링 대상인지
        source_url=target.url,  # 요청한 URL
        page_title=page_info["title"],  # 페이지 제목
        raw_text=page_info["text_preview"],  # 일부 텍스트
        raw_html=html[:5000],  # HTML 일부 저장 (너무 크니까 잘라서 저장)
        # 추가 정보(JSON)
        extra_data={
            "a_count": page_info["a_count"],  # 링크 개수
            "contains_review_word": page_info[
                "contains_review_word"
            ],  # 리뷰 관련 단어 포함 여부
            "contains_keyword": page_info["contains_keyword"],  # 키워드 포함 여부
            "type": "page_info",  # 데이터 타입 구분용
        },
    )

    # 5️⃣ 상품 링크 저장 (있다면)
    # → 현재는 candidate_links가 빈 리스트라 실행 안됨
    for item in candidate_links[:20]:

        CrawlRawData.objects.create(
            target=target,
            source_url=target.url,
            page_title=page_info["title"],
            # 상품 정보
            item_title=item["title"],  # 상품 이름
            item_url=item["url"],  # 상품 링크
            raw_text="",
            raw_html="",
            extra_data={
                "type": "candidate_link",  # 이 데이터는 링크 정보임
            },
        )

    # 6️⃣ 마지막 크롤링 시간 업데이트
    target.last_crawled_at = timezone.now()
    target.save(update_fields=["last_crawled_at"])

    # 7️⃣ 결과 반환 (로그/테스트용)
    return {
        "page_title": page_info["title"],  # 페이지 제목
        "candidate_count": len(candidate_links),  # 추출된 링크 개수
    }
