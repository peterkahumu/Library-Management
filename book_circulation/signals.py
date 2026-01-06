from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Transaction


@receiver([post_save, post_delete], sender=Transaction)
def invalidate_transaction_cache(sender, instance, **kwargs):
    """
    Clear cache when a transaction is created, updated, or deleted.
    Affects:
    - Homepage stats (Available Books)
    - Admin KPIs (Issued Books, Overdue, etc)
    """
    from caching.services import LibraryCacheService

    if instance.status in ["ISSUED", "RETURNED", "DOWNLOADED", "RETURN_REQUESTED"]:
        LibraryCacheService.invalidate_available_books()

    # Invalidate Dashboards (always, as they show pending requests)
    LibraryCacheService.invalidate_admin_kpis()
    LibraryCacheService.invalidate_librarian_kpis()
