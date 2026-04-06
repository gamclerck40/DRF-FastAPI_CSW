from django.apps import AppConfig


# Crawling 앱의 '기본 설정'
class CrawlingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.crawling"
