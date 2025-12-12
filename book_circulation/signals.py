from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

from .models import Transaction


@receiver(post_save, sender=Transaction)
def invalidate_transaction_cache(sender, instance, **kwargs):
    if instance.status in ["ISSUED", "RETURNED"]:
        cache.delete(f"user_active_transactions:{instance.user.pk}")
        cache.delete("homepage_stats")


@receiver(post_delete, sender=Transaction)
def invalidate_transaction_cache_on_delete(sender, instance, **kwargs):
    cache.delete(f"user_active_transactions:{instance.user.pk}")
    cache.delete("homepage_stats")
