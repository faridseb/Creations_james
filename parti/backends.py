from django.contrib.auth.backends import ModelBackend
from .models import PartiUser


class EmailBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        if request and request.POST.get("app_name") != "parti":
            return None
        try:
            # Chercher l'utilisateur par email
            user = PartiUser.objects.get(email=email)
        except PartiUser.DoesNotExist:
            return None

        # Vérifier le mot de passe
        if user.check_password(password):
            return user

        return None

    def get_user(self, user_id):
        try:
            return PartiUser.objects.get(pk=user_id)
        except PartiUser.DoesNotExist:
            return None