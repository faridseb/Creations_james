# myapp/custom_middleware.py

from django.shortcuts import redirect
from django.urls import reverse

class CustomLoginRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Si l'utilisateur n'est pas authentifié
        if not request.user.is_authenticated:
            # Vérifier si la requête est pour une page de connexion
            if request.path in [
                reverse('association:association_login'),
                reverse('parti:login'),
                reverse('ecommerce:ecommerce_login'),
                reverse('authentication:user_login')
            ]:
                return self.get_response(request)  # Permettre l'accès à la page de connexion

            # Redirection vers la page de connexion appropriée
            if request.path.startswith('/association/'):
                return redirect(reverse('association:association_login'))
            elif request.path.startswith('/parti/'):
                return redirect(reverse('parti:login'))
            elif request.path.startswith('/ecommerce/'):
                return redirect(reverse('ecommerce:ecommerce_login'))
            else:
                return redirect(reverse('authentication:user_login'))

        # Continuer à traiter la requête normalement
        response = self.get_response(request)
        return response
