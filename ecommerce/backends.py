from django.contrib.auth.backends import ModelBackend
from .models import EcommerceUser

class UsernameBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if request and request.POST.get("app_name") != "ecommerce":
            return None
        try:
            # Chercher l'utilisateur par email
            user = EcommerceUser.objects.get(username=username)
        except EcommerceUser.DoesNotExist:
            return None  # Aucun utilisateur trouvé

        # Vérifier si l'utilisateur est actif
        if not user.is_active:
            return None  # Utilisateur inactif, on ne permet pas la connexion

        # Vérifier le mot de passe
        if user.check_password(password):
            return user  # Authentification réussie

        return None  # Mot de passe incorrect
