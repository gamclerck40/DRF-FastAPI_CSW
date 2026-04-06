import requests


"""
- 웹페이지에 요청을 보내서 HTML을 가져오는 역할
- 즉, 저장 전 단계인 **수집 입력부**입니다.

1. 진입점(트리거)가 크롤링을 시작
2. http.py가 실행
    01 requests.get(url, headers=HEADERS, timeout=15) — 해당 URL로 HTTP GET 요청을 보냄
    02 서버가 HTML을 응답으로 돌려줌
    02 response.raise_for_status() — 상태코드가 4xx/5xx면 에러를 발생시키고, 200이면 통과
    04 return response — 응답 객체를 통째로 돌려줌
"""
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}


def fetch_page(url: str, timeout: int = 15) -> requests.Response:
    response = requests.get(url, headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    return response
