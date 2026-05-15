from django.contrib.auth.backends import ModelBackend
from .models import OeuvreSocialUser


class OeuvreBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        if request and request.POST.get("app_name") != "homepage":
            return None

        try:
            # Chercher l'utilisateur par email
            user = OeuvreSocialUser.objects.get(email=email)
            print(f"Utilisateur trouvé : {user}")  # Débogage
        except OeuvreSocialUser.DoesNotExist:
            print("Utilisateur non trouvé.")  # Débogage
            return None

        # Vérifier le mot de passe
        if user.check_password(password):
            print("Mot de passe correct.")  # Débogage
            return user
        else:
            print("Mot de passe incorrect.")  # Débogage

        return None
