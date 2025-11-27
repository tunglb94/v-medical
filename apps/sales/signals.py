from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Order

@receiver(post_save, sender=Order)
def update_customer_ranking_on_save(sender, instance, created, **kwargs):
    if instance.customer:
        instance.customer.update_ranking()

@receiver(post_delete, sender=Order)
def update_customer_ranking_on_delete(sender, instance, **kwargs):
    if instance.customer:
        instance.customer.update_ranking()