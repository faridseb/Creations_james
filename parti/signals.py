from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import PartiUser, Carnet  # Utilisation de AssociationUser



@receiver(post_save, sender=PartiUser)  # Utilisation de AssociationUser au lieu de CustomUser
def create_user_carnet(sender, instance, created, **kwargs):
    if created:
        # Créez un carnet associé au nouvel utilisateur
        Carnet.objects.create(utilisateur=instance)  # Utilisez 'utilisateur' au lieu de 'user'

