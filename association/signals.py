from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import AssociationUser, Carnet  # Utilisation de AssociationUser



@receiver(post_save, sender=AssociationUser)  # Utilisation de AssociationUser au lieu de CustomUser
def create_user_carnet(sender, instance, created, **kwargs):
    if created:
        # Créez un carnet associé au nouvel utilisateur
        Carnet.objects.create(utilisateur=instance)  # Utilisez 'utilisateur' au lieu de 'user'

@receiver(pre_save, sender=AssociationUser)
def update_user_checkboxes(sender, instance, **kwargs):
    """
    Ce signal sera appelé avant la sauvegarde d'un utilisateur.
    Il mettra à jour l'état des cases (cochées/grisées) en fonction du type de cotisation et de l'option sélectionnée.
    """

    # Vérifier si l'utilisateur a sélectionné un type de cotisation spécifique
    if instance.montant_adhesion == 'tous_membres':
        instance.checked = True
        instance.disabled = True  # Grise la case
    elif instance.montant_adhesion == 'membres_sauf':
        instance.checked = True
        instance.disabled = False  # Ne grise pas la case, reste modifiable
    else:
        instance.checked = False  # Par défaut, décocher
        instance.disabled = False  # Rendre modifiable
