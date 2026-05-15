from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from authentication.models import CustomUser, Referral


class Command(BaseCommand):
    help = 'Ajoute les utilisateurs manquants à CustomUser à partir de Referral'

    def handle(self, *args, **kwargs):
        # Récupérez tous les utilisateurs référés dans Referral
        referred_users_ids = Referral.objects.values_list('referred_id', flat=True)

        # Récupérez les utilisateurs qui existent dans Referral mais pas dans CustomUser
        missing_users_ids = [user_id for user_id in referred_users_ids if
                             not CustomUser.objects.filter(id=user_id).exists()]

        if missing_users_ids:
            for user_id in missing_users_ids:
                try:
                    # Récupérez les données du modèle Referral pour cet utilisateur
                    referral = Referral.objects.get(referred_id=user_id)

                    # Créez un utilisateur avec ces données (ajustez les champs si nécessaire)
                    CustomUser.objects.create(
                        id=user_id,  # Assurez-vous que cet ID est unique et approprié
                        email=referral.referred.email,
                        username=referral.referred.username,
                        # Ajoutez d'autres champs nécessaires
                        # Exemple :
                        # first_name=referral.referred.first_name,
                        # last_name=referral.referred.last_name,
                        # date_of_birth=referral.referred.date_of_birth
                    )
                    self.stdout.write(f"Utilisateur {user_id} ajouté à CustomUser.")
                except ObjectDoesNotExist:
                    self.stderr.write(f"Utilisateur référé {user_id} n'existe pas dans Referral.")
                except Exception as e:
                    self.stderr.write(f"Erreur lors de l'ajout de l'utilisateur {user_id}: {e}")
        else:
            self.stdout.write("Tous les utilisateurs référés existent déjà dans CustomUser.")
