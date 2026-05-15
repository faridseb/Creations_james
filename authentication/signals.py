# authentication/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import CustomUser, Wallet, Referral, Stage,Transaction
from .utils import update_grand_parrain_reward, check_and_update_stage
from .tasks import send_reminder_email, delete_unconfirmed_account
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from django.utils.timezone import now
from django.db.models import Sum


User = get_user_model()

CONVERSION_RATE_TO_POINTS = Decimal('100.0')  # 1 FCFA = 100 points
CONVERSION_RATE_TO_BALANCE = Decimal('0.01')   # 1 point = 0.01 FCFA

@receiver(pre_save, sender=Wallet)
def update_wallet_points(sender, instance, **kwargs):
    """
    Met à jour automatiquement les points en fonction du solde en argent.
    """
    if instance.pk is not None:
        previous_instance = Wallet.objects.get(pk=instance.pk)
        if instance.balance != previous_instance.balance:
            # Mettre à jour les points en fonction du solde
            instance.points_balance = instance.balance * CONVERSION_RATE_TO_POINTS

@receiver(post_save, sender=Wallet)
def update_wallet_balance(sender, instance, created, **kwargs):
    """
    Met à jour le solde en argent en fonction des points après la sauvegarde.
    """
    if created:
        return  # Ne rien faire si c'est une nouvelle instance

    # Calculer le montant en FCFA à partir des points
    amount_in_fcfa = instance.points_balance * CONVERSION_RATE_TO_BALANCE

    # Mettre à jour le solde du portefeuille uniquement si nécessaire
    if instance.balance != amount_in_fcfa:
        instance.balance = amount_in_fcfa
        instance.save(update_fields=['balance'])

@receiver(post_save, sender=User)
def handle_user_save(sender, instance, created, **kwargs):
    """
    Gère la création d'un nouvel utilisateur et met à jour la récompense du grand parrain.
    """
    if created:
        update_grand_parrain_reward(instance)

@receiver(post_save, sender=CustomUser)
def create_referral(sender, instance, created, **kwargs):
    """
    Crée une entrée de parrainage si l'utilisateur a un parrain lors de sa création.
    """
    if created and instance.referrer:
        Referral.objects.create(
            referrer=instance.referrer,
            referred=instance,
            stage_completed=False,
            referred_user=instance
        )

@receiver(post_save, sender=CustomUser)
def create_wallet(sender, instance, created, **kwargs):
    """
    Crée un portefeuille pour un nouvel utilisateur.
    """
    if created:
        Wallet.objects.create(user=instance)

@receiver(post_save, sender=Wallet)
def update_custom_user_wallet_balance(sender, instance, created, **kwargs):
    """
    Met à jour le solde du CustomUser lorsque le Wallet est mis à jour.
    """
    instance.user.wallet_balance = instance.balance
    instance.user.save()

@receiver(post_save, sender=Wallet)
def update_user_wallet_balance(sender, instance, **kwargs):
    """
    Met à jour le champ wallet_balance de l'utilisateur en fonction du solde du portefeuille.
    """
    user = instance.user
    if user.wallet_balance != instance.balance:
        user.wallet_balance = instance.balance
        user.save()
@receiver(post_save, sender=Transaction)
def handle_membership_payment(sender, instance, created, **kwargs):
    if created and instance.is_successful:  # Vérifiez si la transaction a réussi
        # Trouver la référence associée à l'utilisateur qui a effectué le paiement
        referral = Referral.objects.filter(referrer=instance.user).first()  # ou une autre logique pour trouver la référence
        if referral:
            # Mettre à jour le statut de confirmation
            referral.is_confirm = True
            referral.save()
