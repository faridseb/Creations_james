from django.contrib.auth.backends import ModelBackend
from .models import CustomUser

class UsernameBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if request and request.POST.get("app_name") != "authentication":
            return None
        try:
            # Chercher l'utilisateur par username
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            return None

        # Vérifier le mot de passe
        if user.check_password(password):
            return user

        return None
