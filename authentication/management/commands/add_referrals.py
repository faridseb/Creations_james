from django.core.management.base import BaseCommand
from django.conf import settings
from authentication.models import CustomUser, Referral

class Command(BaseCommand):
    help = 'Ajouter les références manquantes à la table Referral'

    def handle(self, *args, **kwargs):
        users_with_referrer = CustomUser.objects.exclude(referrer__isnull=True)

        count = 0
        for user in users_with_referrer:
            referrer = user.referrer
            referred = user

            # Vérifier si une entrée existe déjà pour éviter les doublons
            if not Referral.objects.filter(referrer=referrer, referred=referred).exists():
                Referral.objects.create(
                    referrer=referrer,
                    referred=referred,
                    stage_completed=False,
                    referred_user=referred
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f'{count} entrées ajoutées à la table Referral'))
