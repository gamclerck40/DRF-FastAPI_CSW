from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.crawling.models import CrawlTarget, CrawlJobLog
from apps.crawling.services.crawl_service import crawl_search_target


class Command(BaseCommand):
    help = "스케줄 크롤링 실행 (limit 기반 분산 수집)"

    def add_arguments(self, parser):
        # [추가] 한 번에 너무 많이 긁지 않도록 limit 옵션 추가
        parser.add_argument(
            "--limit",
            type=int,
            default=10,
            help="한 번 실행할 최대 target 개수",
        )

    def handle(self, *args, **options):
        limit = options["limit"]

        # [추가]
        # 아직 오래 안 돌린 것부터(limit만큼) 가져와서 분산 수집
        targets = CrawlTarget.objects.filter(
            is_active=True,
            target_type="search",
        ).order_by("last_crawled_at", "id")[:limit]

        total_targets = targets.count()
        success_count = 0
        fail_count = 0
        site_summary = {}

        # [추가] 실행 로그 생성
        log = CrawlJobLog.objects.create(
            site="all",
            command_name="scheduled_crawl",
            status="success",
            total_targets=total_targets,
            success_count=0,
            fail_count=0,
            message=f"scheduled_crawl 시작 (limit={limit})",
        )

        if total_targets == 0:
            self.stdout.write(self.style.WARNING("수집할 대상이 없습니다."))
            log.message = "수집할 대상이 없습니다."
            log.finished_at = timezone.now()
            log.save(update_fields=["message", "finished_at"])
            return

        self.stdout.write(
            self.style.SUCCESS(f"scheduled_crawl 시작 - 대상 {total_targets}건")
        )

        for target in targets:
            self.stdout.write(f"[START] {target.id} - {target.title}")

            try:
                result = crawl_search_target(target)
                success_count += 1

                site_summary[target.site] = site_summary.get(target.site, 0) + 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f"[OK] {target.id} "
                        f"title={result['page_title']} "
                        f"candidate_count={result['candidate_count']}"
                    )
                )

            except Exception as e:
                fail_count += 1
                self.stdout.write(self.style.ERROR(f"[FAIL] {target.id}: {e}"))

        final_status = "success" if fail_count == 0 else "failed"

        # [추가] 실행 결과 로그 갱신
        log.status = final_status
        log.success_count = success_count
        log.fail_count = fail_count
        log.message = f"사이트별 처리 수: {site_summary}"
        log.finished_at = timezone.now()
        log.save(
            update_fields=[
                "status",
                "success_count",
                "fail_count",
                "message",
                "finished_at",
            ]
        )

        self.stdout.write(self.style.SUCCESS("scheduled_crawl 종료"))
        self.stdout.write(
            self.style.SUCCESS(
                f"총 {total_targets}개 / 성공 {success_count} / 실패 {fail_count}"
            )
        )
