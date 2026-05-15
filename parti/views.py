# parti/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from .forms import PartiSignupForm, PartiLoginForm
from .models import PartiUser,Payment,Carnet,LigneCotisation
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.urls import reverse
import urllib.parse
from django.conf import settings
import stripe
import uuid
from datetime import datetime
from django.utils import timezone

from time import sleep
from django.contrib.auth import logout
from datetime import date

stripe.api_key = settings.STRIPE_SECRET_KEY

def initiate_payment(request):
    # Récupérer les paramètres de paiement depuis la requête GET
    amount = request.GET.get("amount")  # Exemple : 5000
    currency = request.GET.get("currency", "XOF")
    payment_method = request.GET.get("payment_method", "stripe")
    return_url = request.GET.get("return_url", "/")  # Redirection après paiement

    # Créer une référence unique pour la transaction
    reference = uuid.uuid4().hex

    # Créer une entrée de paiement dans la base de données
    payment = Payment.objects.create(
        user=request.user if request.user.is_authenticated else None,
        amount=amount,
        currency=currency,
        payment_method=payment_method,
        reference=reference,
        return_url=return_url,
    )

    # Intégration Stripe
    if payment_method == "stripe":
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": currency.lower(),
                    "product_data": {"name": "Paiement"},
                    "unit_amount": int(float(amount)),  # Convertir en centimes
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=request.build_absolute_uri(
                reverse('parti:payment_success')
            ) + '?session_id={CHECKOUT_SESSION_ID}&type=confirmation&payment_method=' + payment_method,
            cancel_url=request.build_absolute_uri(reverse('parti:payment_failed')),
        )
        # Rediriger l'utilisateur vers Stripe
        return redirect(session.url)

    # Ajouter d'autres intégrations (PayPal, PayGate, etc.)
    elif payment_method == "paypal":
        # Logique pour PayPal (à compléter selon l'intégration spécifique)
        pass
    elif payment_method == "paygate":
        # Logique pour PayGate (à compléter selon l'intégration spécifique)
        pass

    # Si le moyen de paiement n'est pas pris en charge
    return render(request, "parti/error.html", {"message": "Moyen de paiement non pris en charge."})


def create_checkout_session(request):
    # Créez une session de paiement avec Stripe
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': 'Adhésion',
                },
                'unit_amount': 3000,  # Montant en cents
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=request.build_absolute_uri(
            reverse('parti:payment_success')
        ) + '?session_id={CHECKOUT_SESSION_ID}&type=confirmation&payment_method=' + payment_method,
        cancel_url=request.build_absolute_uri(reverse('parti:payment_failed')),
    )

    return redirect(session.url, code=303)
def parti_signup(request):
    if request.method == 'POST':
        form = PartiSignupForm(request.POST)
        if form.is_valid():
            # Enregistrer les données utilisateur dans la session
            request.session['signup_data'] = {
                'email': form.cleaned_data['email'],
                'username': form.cleaned_data['username'],
                'password': form.cleaned_data['password'],  # Stocker temporairement
            }

            # Rediriger vers la page de paiement
            amount = 3000  # Montant de l'adhésion
            currency = "XOF"
            payment_method = "stripe"
            return_url = request.build_absolute_uri('/parti/payment_success')
            source_app = "authentication"

            return redirect(f"/parti/initiate?amount={amount}&currency={currency}&payment_method={payment_method}&return_url={return_url}")

    else:
        form = PartiSignupForm()

    return render(request, 'parti/parti_signup.html', {'form': form})
# Connexion
def parti_login(request):
    if request.method == 'POST':
        form = PartiLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Authentification via l'email
            user = authenticate(request, email=email, password=password)
            if user is not None and isinstance(user, PartiUser):  # Vérifie que l'utilisateur est une instance de PartiUser
                login(request, user)  # Connexion de l'utilisateur
                messages.success(request, "Connexion réussie !")
                return redirect('parti:parti_dashboard')  # Redirection après la connexion réussie
            else:
                messages.error(request, "Accès réservé aux utilisateurs du modèle PartiUser ou identifiants invalides.")
        else:
            messages.error(request, "Erreur dans le formulaire. Veuillez vérifier vos informations.")
    else:
        form = PartiLoginForm()

    return render(request, 'parti/login.html', {'form': form})
def politique(request):
    return render(request, 'parti/politique.html')
def payment_failed(request):
    return render(request, 'payment_failed.html')

def payment_success(request):
    # Récupérer les données utilisateur depuis la session
    signup_data = request.session.get('signup_data')

    if not signup_data:
        messages.error(request, "Erreur lors de la création du compte. Veuillez réessayer.")
        return redirect('parti:signup')  # Rediriger vers l'inscription si données manquantes

    # Créer l'utilisateur dans la base de données
    email = signup_data['email']
    username = signup_data['username']
    password = signup_data['password']

    user = PartiUser(
        email=email,
        username=username,
    )
    user.set_password(password)  # Hacher le mot de passe
    user.save()  # Enregistrer dans la base de données

    # Nettoyer les données de la session après le succès
    del request.session['signup_data']

    # Rediriger vers la page de connexion avec un message de succès
    messages.success(request, "Paiement validé et compte créé avec succès. Vous pouvez maintenant vous connecter.")
    return redirect('parti:login')
def get_current_semester():
    month = timezone.now().month
    if month <= 6:
        return 1  # Premier semestre
    else:
        return 2  # Deuxième semestre

def get_infos_du_mois(carnets, annee, mois):
    cotisation = 0
    penalite = 0
    sanction = 0

    for carnet in carnets:
        lignes_du_mois = carnet.lignes.filter(date__year=annee, date__month=mois)

        for ligne in lignes_du_mois:
            cotisation += ligne.cotisation or 0
            penalite += ligne.penalite or 0
            # Pour les sanctions, on considère juste le nombre ou autre ? On suppose ici un texte = 1 sanction
            if ligne.sanctions:
                sanction += 1

    return {
        'cotisation': cotisation,
        'penalite': penalite,
        'sanction': sanction,
        'mois': mois,
    }

def parti_dashboard(request):
    utilisateur_connecte = None
    membre = None
    cotisations = []
    carnets = []
    annee_courante = datetime.now().year
    try:
        if request.user.is_authenticated:
            utilisateur_connecte = PartiUser.objects.get(email=request.user.email)
            carnets = Carnet.objects.filter(utilisateur=utilisateur_connecte)
        else:
            messages.warning(request, "Vous devez être connecté pour accéder à votre tableau de bord.")
    except (PartiUser.DoesNotExist):
        messages.error(request, "Erreur lors de la récupération des informations de l'utilisateur ou du membre.")

    mois_total = 6  # Le nombre total de mois à afficher
    for carnet in carnets:
        lignes_total = mois_total + carnet.lignes.count()
        lignes_vides = 6 - lignes_total if lignes_total < 6 else 0
        carnet.lignes_vides = range(lignes_vides) if lignes_vides > 0 else []

    annee_fin = annee_courante + 5
    if carnets.exists():
        annees = list(range(carnets.earliest('annee').annee, annee_fin + 1))
    else:
        annees = list(range(annee_courante, annee_fin + 1))

    semestres = [1, 2]  # Deux semestres par an
    mois_semestre = {
        1: [1, 2, 3, 4, 5, 6],
        2: [7, 8, 9, 10, 11, 12]
    }

    informations_par_annee_semestre = []
    for annee in annees:
        for semestre in semestres:
            semestre_infos = {
                'annee': annee,
                'semestre': semestre,
                'mois_infos': [],
                'totaux': {
                    'total_cotisation': 0,
                    'total_penalite': 0,
                    'total_sanction': 0,
                },
            }
            for mois in mois_semestre[semestre]:
                if annee <= annee_courante:
                    infos_du_mois = get_infos_du_mois(carnets, annee, mois)
                else:
                    infos_du_mois = {'cotisation': 0, 'penalite': 0, 'sanction': 0, 'mois': mois}
                infos_du_mois['mois'] = mois
                semestre_infos['mois_infos'].append(infos_du_mois)
                semestre_infos['totaux']['total_cotisation'] += infos_du_mois['cotisation']
                semestre_infos['totaux']['total_penalite'] += infos_du_mois['penalite']
                semestre_infos['totaux']['total_sanction'] += infos_du_mois['sanction']
            informations_par_annee_semestre.append(semestre_infos)

    for carnet in carnets:
        lignes_total = carnet.lignes.count()
        lignes_vides = max(0, 6 - lignes_total)
        carnet.lignes_vides = range(lignes_vides)

    context = {

        'partiuser': utilisateur_connecte,
        'carnets': carnets,
        'annees': annees,
        'semestres': semestres,
        'informations_par_annee_semestre': informations_par_annee_semestre
    }

    return render(request, 'parti/parti_dashboard.html', context)