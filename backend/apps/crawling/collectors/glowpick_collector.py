# [유지] urljoin 사용
from urllib.parse import urljoin, urlparse

# [유지] 공통 HTTP 요청 / 공통 파서 사용
from apps.crawling.services.http import fetch_page
from apps.crawling.services.parser import extract_page_info, get_soup


def collect_glowpick_search(target) -> dict:
    """
    글로우픽 검색/랭킹 페이지를 수집해서
    페이지 기본 정보와 상품 상세 링크 후보를 반환합니다.
    """

    # [유지] 페이지 요청
    response = fetch_page(target.url)
    html = response.text

    # [유지] 공통 페이지 정보 추출
    page_info = extract_page_info(html)
    soup = get_soup(html)

    candidates = []
    seen = set()

    for a in soup.select("a[href]"):
        href = (a.get("href") or "").strip()
        text = a.get_text(" ", strip=True)

        if not href:
            continue

        full_url = urljoin(target.url, href)
        parsed = urlparse(full_url)

        # [수정] glowpick 도메인만 허용
        if "glowpick" not in parsed.netloc:
            continue

        # [수정] 상품 상세 링크만 허용
        # 기존에는 /ranking/ 도 허용해서 랭킹 링크가 후보에 섞일 수 있었음
        if not (
            parsed.path.startswith("/product/") or parsed.path.startswith("/products/")
        ):
            continue

        if full_url in seen:
            continue

        seen.add(full_url)

        candidates.append(
            {
                "title": text[:255],
                "url": full_url,
            }
        )

    return {
        "site": "glowpick",
        "page_info": page_info,
        "candidate_links": candidates[:20],
        "html": html,
    }
