# management/commands/init_wallets.py
from django.core.management.base import BaseCommand
from authentication.models import Wallet, CustomUser

class Command(BaseCommand):
    help = 'Initialise les soldes des portefeuilles des utilisateurs.'

    def handle(self, *args, **kwargs):
        for user in CustomUser.objects.all():
            if not hasattr(user, 'wallet'):
                Wallet.objects.create(user=user, balance=user.wallet_balance)

            # Synchroniser les soldes
            user.wallet.balance = user.wallet_balance
            user.wallet.save()
            self.stdout.write(f'Successfully updated wallet for user {user.username}')
