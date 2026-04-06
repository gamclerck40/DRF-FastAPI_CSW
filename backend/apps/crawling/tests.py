from django.test import TestCase

from apps.crawling.models import CrawlRawData, CrawlTarget
from apps.crawling.services.save_service import save_search_result


class SaveSearchResultTest(TestCase):
    def setUp(self):
        self.target = CrawlTarget.objects.create(
            site="glowpick",
            target_type="search",
            keyword="수분크림",
            title="글로우픽 수분크림 검색",
            url="https://glowpick.co.kr/ranking/search/%EC%88%98%EB%B6%84%ED%81%AC%EB%A6%BC",
        )

        self.result = {
            "site": "glowpick",
            "page_info": {
                "title": "테스트 페이지",
                "a_count": 10,
                "contains_review_word": True,
                "contains_keyword": True,
                "text_preview": "미리보기 텍스트",
            },
            "candidate_links": [
                {
                    "title": "상품 A",
                    "url": "https://glowpick.co.kr/products/111",
                },
                {
                    "title": "상품 B",
                    "url": "https://glowpick.co.kr/products/222",
                },
            ],
            "html": "<html><title>테스트 페이지</title></html>",
        }

    def test_save_search_result_creates_product_targets(self):
        summary = save_search_result(self.target, self.result)

        # [유지] raw data는 page_info 1 + candidate 2
        self.assertEqual(CrawlRawData.objects.count(), 3)

        # [추가] product target 2개 생성 확인
        self.assertEqual(
            CrawlTarget.objects.filter(site="glowpick", target_type="product").count(),
            2,
        )

        self.assertEqual(summary["created_product_targets"], 2)
