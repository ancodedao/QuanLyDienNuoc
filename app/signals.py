from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserBillPermissions

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_bill_permissions(sender, instance, created, **kwargs):
    if created:
        UserBillPermissions.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_bill_permissions(sender, instance, **kwargs):
    instance.bill_permissions.save()
