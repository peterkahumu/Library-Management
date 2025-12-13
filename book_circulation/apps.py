from django.apps import AppConfig


class BookCirculationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "book_circulation"

    def ready(self):
        import book_circulation.signals  # noqa
