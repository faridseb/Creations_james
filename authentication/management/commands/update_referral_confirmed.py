# your_app/management/commands/update_all_confirmations.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from authentication.models import Referral, Transaction


class Command(BaseCommand):
    help = "Met à jour is_confirmed pour tous les utilisateurs ayant payé leur adhésion et dont le parrain a reçu la commission."

    def handle(self, *args, **kwargs):
        User = get_user_model()

        # Récupérer tous les utilisateurs
        users = User.objects.all()
        count_updated = 0

        # Remettre is_confirmed à False pour tous les utilisateurs et leurs références
        for user in users:
            user.is_confirmed = False
            user.save()

            referral = Referral.objects.filter(referred=user).first()
            if referral:
                referral.is_confirmed = False
                referral.save()

        # Vérifier le paiement et la commission, puis mettre à jour is_confirmed
        for user in users:
            referral = Referral.objects.filter(referred=user).first()
            if referral and not user.is_confirmed:
                # Logique pour vérifier si le paiement de l'utilisateur a été effectué
                if self.payment_successful(user):
                    # Vérifier si le parrain a reçu la commission
                    if self.sponsor_commission_paid(referral.referrer):
                        # Mettre à jour l'utilisateur
                        user.is_confirmed = True
                        user.save()

                        # Mettre à jour la référence
                        referral.is_confirmed = True
                        referral.save()

                        count_updated += 1
                        self.stdout.write(self.style.SUCCESS(f"Utilisateur {user.email} confirmé."))

        self.stdout.write(self.style.SUCCESS(f"{count_updated} utilisateurs mis à jour."))

    def payment_successful(self, user):
        # Logique pour vérifier si le paiement de l'utilisateur a été effectué.
        # Par exemple, vous pouvez vérifier un champ dans le modèle Referral ou Wallet.
        referral = Referral.objects.filter(referred=user).first()
        return referral.is_confirmed if referral else False

    def sponsor_commission_paid(self, sponsor):
        # Vérifier si le parrain a reçu la commission.
        # Vous devez définir la logique pour déterminer si la commission a été payée.
        # Par exemple, vérifier si une transaction a été enregistrée pour ce parrain.
        return Transaction.objects.filter(user=sponsor, amount=500).exists()
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from authentication.models import Referral


class Command(BaseCommand):
    help = "Met à jour is_confirmed pour tous les utilisateurs et leurs références."

    def handle(self, *args, **kwargs):
        User = get_user_model()
        count_updated = 0

        # Mettre à jour tous les utilisateurs
        users = User.objects.all()
        for user in users:
            if not user.is_confirmed:
                referral = Referral.objects.filter(referred=user).first()
                if referral and referral.is_confirmed:
                    user.is_confirmed = True
                    user.save()
                    count_updated += 1

        # Mettre à jour les références
        referrals = Referral.objects.all()
        for referral in referrals:
            if not referral.is_confirmed and referral.referred.is_confirmed:
                referral.is_confirmed = True
                referral.save()
                count_updated += 1

        self.stdout.write(self.style.SUCCESS(f"{count_updated} confirmations mises à jour."))
