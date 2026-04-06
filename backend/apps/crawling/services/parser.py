from bs4 import BeautifulSoup
from urllib.parse import urljoin

"""
- 가져온 HTML(http.py)을 분석해서
    - 페이지 정보 추출
    - 상품 상세 링크 후보 추출
- 즉, 수집 데이터 가공/추출 역할입니다.

"""


# HTML 문자열을 '파싱' 가능한 객체로 변환 -> 트리 구조 객체로 변환
# 이 함수를 통해 가져온 객체를 아래 두 함수가 활용하는 방식.
def get_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


# 페이지 전체의 '메타 정보' 추출
def extract_page_info(html: str) -> dict:
    """
    "이 페이지가 크롤링할 가치가 있는 페이지인가?" 를 판단하는 '기초 정보'를 뽑는 함수

    """

    # 1. 'get_soup' 호출해서 BeautifulSoup '객체'를 생성
    soup = get_soup(html)

    """
    # 2. 생성한 객체의 HTML 태그를 '모두' 벗겨 '순수'한 텍스트를 추출.
        [" " > 태그 사이 공백을 넣어 단어가 붙지 않게 함]
        [strip = True > 태그 앞, 뒤 내부 공백 제거]
    """
    text = soup.get_text(" ", strip=True)

    # Dictionary 형태로 반환.
    return {
        # '<title>'태그의 텍스트를 가져오되, 없으면 빈 문자열 반환.
        "title": soup.title.get_text(strip=True) if soup.title else "",
        # 링크 태그 갯수를 셈 [많을 수록 검색 결과 페이지일 가능성 있음].
        "a_count": len(soup.select("a[href]")),
        # contains_ 두 개는 해당 '키워드'를 포함하면 True, 포함하지 않으민 False를 반환하는 bool 형식.
        "contains_review_word": "리뷰" in text,
        "contains_keyword": "수분크림" in text,
        "text_preview": text[:500],
    }


# extract_candidate_links() 함수는 공통 파서에서 제거하고 사이트별 collector로 이동한 것
# 링크 추출은 사이트별 규칙이므로 collector의 각각 파일로 이동합니다.
# # 상품 상세 링크 후보 추출. ※핵심※
# def extract_candidate_links(site: str, base_url: str, html: str) -> list[dict]:
#     '''
#     '검색 결과 페이지'의 HTML -> '상품 상세 페이지' HTML로 이어지는 '링크'만 골라내는 역할
#     [site > 어떤 사이트인지(danawa/hwahae/glowpick)]
#     [base_url > '상대경로'를 '절대경로'로 바꿀 때 기준이 되는 URL]
#     [html > 원본 HTML 문자열]
#     '''

#     # 가져온 URL로 트리구조의 객체 생성.
#     soup = get_soup(html)
#     candidates = []

#     '''
#     모든 링크 순회
#     <a href="..."> 태그를 전부 가져와 하나씩 순회.
#     '''
#     for a in soup.select("a[href]"):
#         # 가져온 <a href> 태그를 href에 저장.
#         href = (a.get("href") or "").strip()

#         # 가져온 <a href> 의 Text 부분을 저장. Ex) <a href="/goods/70006">싸이닉 병풀 수분크림 80ml</a> 에서 '싸이닉 병풀 수분크림' 부분만.
#         text = a.get_text(" ", strip=True)

#         if not href:
#             continue

#         '''
#         상대경로(href)를 '절대경로'로 변환
#         Ex) <a href="/goods/70006">싸이닉 병풀 수분크림 80ml</a> 에서
#         '/goods/70006/' > 'https://hwahae.co.kr/goods/70006/'로 변환.
#         urljoin(기준url, 상대경로) 함수는 기준 url의 '앞 부분'만 가져와서 상대경로와 합치는 역할.
#         '''
#         full_url = urljoin(base_url, href)

#         # False를 초깃값으로, 조건이 맞는 링크만 'keep = True'로 바꿈.
#         keep = False

#         '''
#         조건에 부합하는 '찾던' 사이트라면? keep = True
#         아래 보이는것 처럼 '사이트' 마다 잡을 기준이 각각 차이가 있다.
#         '''
#         if site == "danawa":
#             if "prod.danawa.com" in full_url:
#                 keep = True

#         elif site == "hwahae":
#             if "hwahae.co.kr" in full_url and (
#                 "/products/" in full_url
#                 or "/product/" in full_url
#                 or "/goods/" in full_url
#             ):
#                 keep = True

#         elif site == "glowpick":
#             if "glowpick.co.kr" in full_url and (
#                 "/product/" in full_url
#                 or "/products/" in full_url
#                 or "/ranking/" in full_url
#             ):
#                 keep = True

#         # keep = True인 링크들을 'candidates(후보들)'에 추가.
#         # text[:255] DB 필드의 최대 길이를 고려한 방어적 슬라이싱.
#         if keep:
#             candidates.append({
#                 "title": text[:255],
#                 "url": full_url,
#             })

#     unique_items = []

#     '''
#     List를 써도 결괏값은 같다. 그럼 왜 굳이 'set()'을 쓰느냐?
#     > set()과 list의 차이는 간단하다
#         1. list는 [0] 부터 끝까지 순차적으로 찾기에 경우에 따라 시간이 많이 걸릴 수 있다.
#         2. set()은 '해시 테이블' 구조로 저장돼 값 자체를 해시 함수에 넣어서 나온 숫자를 주소로 사용하기에 '즉시' 찾을 수 있다
#     결론은 set() 방식이 바로 찾을 수 있는 방식이라 사용된 것.
#     '''


#     seen = set()

#     for item in candidates:
#         if item["url"] not in seen:
#             seen.add(item["url"])
#             unique_items.append(item)

#     return unique_items
