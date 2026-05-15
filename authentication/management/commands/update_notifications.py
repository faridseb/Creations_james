from django.core.management.base import BaseCommand
from authentication.models import Notification
from authentication.models import CustomUser  # Importer votre modèle d'utilisateur personnalisé


class Command(BaseCommand):
    help = 'Marque toutes les notifications comme lues pour tous les utilisateurs'

    def handle(self, *args, **kwargs):
        # Récupérer tous les utilisateurs personnalisés
        users = CustomUser.objects.all()  # Utiliser CustomUser au lieu de User

        # Initialiser un compteur pour suivre le nombre de notifications mises à jour
        updated_count = 0

        # Parcourir tous les utilisateurs
        for user in users:
            # Récupérer les notifications non lues pour chaque utilisateur
            notifications = Notification.objects.filter(user=user, is_read=False)

            # Mettre à jour le statut des notifications
            updated_count += notifications.update(is_read=True)

        # Afficher le résultat
        if updated_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'{updated_count} notifications marquées comme lues pour tous les utilisateurs.'))
        else:
            self.stdout.write(self.style.WARNING('Aucune notification non lue à marquer comme lue.'))
