from django.core.management.base import BaseCommand
from authentication.models import Wallet, Transaction, Stage, Referral


class Command(BaseCommand):
    help = 'Met à jour les transactions à partir des récompenses existantes dans le portefeuille'

    def handle(self, *args, **kwargs):
        wallets = Wallet.objects.all()

        for wallet in wallets:
            user = wallet.user

            # Récupérer les étapes pour l'utilisateur
            stages = Stage.objects.all()
            for stage in stages:
                # Vérifiez si le stage est complété
                referrals = Referral.objects.filter(referrer=user, stage_completed=True)
                filled_slots = referrals.count()  # Nombre de références complètes

                if filled_slots >= stage.required_referrals:
                    # Montant de la récompense
                    reward_amount = stage.reward

                    # Raison de la transaction
                    reason = f"Récompense pour la fin du stade {stage.stage_number} suite à la confirmation d'inscription de {filled_slots} filleuls."

                    # Vérifiez si une transaction a déjà été enregistrée
                    if not Transaction.objects.filter(user=user, amount=reward_amount, reason=reason).exists():
                        # Créer une nouvelle transaction
                        Transaction.objects.create(
                            user=user,
                            amount=reward_amount,
                            reason=reason
                        )
                        self.stdout.write(self.style.SUCCESS(
                            f"Transaction enregistrée pour {user.username}: {reward_amount} CFA pour le stade {stage.stage_number}."))
                    else:
                        self.stdout.write(self.style.WARNING(
                            f"Transaction déjà enregistrée pour {user.username}: {reward_amount} CFA pour le stade {stage.stage_number}."))
