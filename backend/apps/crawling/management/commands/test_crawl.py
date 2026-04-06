from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.crawling.models import CrawlTarget, CrawlJobLog
from apps.crawling.services.crawl_service import crawl_search_target


class Command(BaseCommand):
    help = "크롤링 대상(search 페이지)에 대해 테스트 크롤링을 수행합니다."

    def handle(self, *args, **options):
        targets = CrawlTarget.objects.filter(is_active=True, target_type="search")

        total_targets = targets.count()
        success_count = 0
        fail_count = 0

        # [추가] 저장 수 집계
        total_created = 0
        total_updated = 0

        # [추가] product target 생성 집계
        total_created_product_targets = 0
        total_reactivated_product_targets = 0

        site_summary = {}

        log = CrawlJobLog.objects.create(
            site="all",
            command_name="test_crawl",
            status="success",
            total_targets=total_targets,
            success_count=0,
            fail_count=0,
            message="테스트 크롤링 시작",
        )

        self.stdout.write(self.style.SUCCESS("테스트 크롤링 시작"))

        for target in targets:
            self.stdout.write(f"\n[{target.site}] {target.url}")

            try:
                result = crawl_search_target(target)
                success_count += 1

                total_created += result["created_count"]
                total_updated += result["updated_count"]
                total_created_product_targets += result["created_product_targets"]
                total_reactivated_product_targets += result[
                    "reactivated_product_targets"
                ]

                site_summary[target.site] = {
                    "targets": site_summary.get(target.site, {}).get("targets", 0) + 1,
                    "created": site_summary.get(target.site, {}).get("created", 0)
                    + result["created_count"],
                    "updated": site_summary.get(target.site, {}).get("updated", 0)
                    + result["updated_count"],
                    "created_product_targets": (
                        site_summary.get(target.site, {}).get(
                            "created_product_targets", 0
                        )
                        + result["created_product_targets"]
                    ),
                    "reactivated_product_targets": (
                        site_summary.get(target.site, {}).get(
                            "reactivated_product_targets", 0
                        )
                        + result["reactivated_product_targets"]
                    ),
                }

                self.stdout.write(
                    self.style.SUCCESS(
                        (
                            f"성공 - title={result['page_title']} / "
                            f"candidate_count={result['candidate_count']} / "
                            f"created={result['created_count']} / "
                            f"updated={result['updated_count']} / "
                            f"created_product_targets={result['created_product_targets']} / "
                            f"reactivated_product_targets={result['reactivated_product_targets']}"
                        )
                    )
                )

            except Exception as e:
                fail_count += 1
                self.stdout.write(self.style.ERROR(f"실패 - {str(e)}"))

        final_status = "success" if fail_count == 0 else "failed"

        log.status = final_status
        log.success_count = success_count
        log.fail_count = fail_count
        log.message = (
            f"사이트별 처리 수: {site_summary} | "
            f"전체 created={total_created}, updated={total_updated}, "
            f"created_product_targets={total_created_product_targets}, "
            f"reactivated_product_targets={total_reactivated_product_targets}"
        )
        log.finished_at = timezone.now()
        log.save()

        self.stdout.write("\n테스트 크롤링 종료")
        self.stdout.write(
            self.style.SUCCESS(
                (
                    f"총 {total_targets}개 / 성공 {success_count} / 실패 {fail_count} / "
                    f"created {total_created} / updated {total_updated} / "
                    f"created_product_targets {total_created_product_targets} / "
                    f"reactivated_product_targets {total_reactivated_product_targets}"
                )
            )
        )
