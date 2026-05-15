from django.contrib.auth.backends import ModelBackend
from .models import Association ,AssociationUser # Assure-toi que ce modèle est celui que tu utilises pour l'utilisateur
from django.contrib.auth.backends import BaseBackend
class NomBackend(ModelBackend):
    def authenticate(self, request, nom=None, password=None, **kwargs):
        if request and request.POST.get("app_name") != "association":
            return None
        try:
            # Chercher l'utilisateur par nom
            user = Association.objects.get(nom=nom)
        except Association.DoesNotExist:
            return None

        # Vérifier le mot de passe
        if user.check_password(password):
            return user

        return None


class IdentifiantBackend(BaseBackend):
    def authenticate(self, request, identifiant=None, password=None):
        try:
            # Récupérer l'utilisateur par `identifiant` au lieu de `username`
            user = AssociationUser.objects.get(identifiant=identifiant)

            # Vérifier le mot de passe
            if user.check_password(password):
                return user
        except AssociationUser.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return AssociationUser.objects.get(pk=user_id)
        except AssociationUser.DoesNotExist:
            return None