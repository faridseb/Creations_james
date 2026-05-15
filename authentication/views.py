from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib import messages
from django.utils import timezone, translation
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.template.response import TemplateResponse
from django.core.files.storage import FileSystemStorage
from django.urls import reverse
from collections import deque
import os
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from .models import CashRegister
from django.db.models import Sum
from django.core.signing import Signer
from django.db import IntegrityError
from twilio.rest import Client
from services.sms import send_sms  # Assurez-vous que le chemin est correct
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.core.mail import send_mail
from phonenumber_field.phonenumber import PhoneNumber
from datetime import date
from django.contrib.auth.hashers import make_password
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.csrf import csrf_exempt
import hashlib
import hmac
import uuid
import requests
from services.sms import send_sms
from django.conf import settings
from django.db import transaction
from decimal import Decimal
from .models import Notification
from django.utils.timezone import now
from django.shortcuts import render, redirect
from .forms import (
    CustomUserAuthenticationForm, ReferralForm,ReferrallinkForm ,PaymentForm,
    AvatarForm, ProfileUpdateForm, ContentPreferencesForm,
    LanguageChangeForm, ThemeChangeForm, ProfilePictureForm,SupportForm
)
from django.db.models import F, Q
from .forms import PaymentForm
import stripe
import paypalrestsdk
from homepage.models import OeuvreSocialUser,Projet,Donation
from .utils import check_and_notify_user,generate_referral_tree,create_notification
from .models import Transaction, SecurityLog, Wallet, PaymentMethod,Referral,Retrait, CustomUser, Stage, ContentPreferences,SupportRequest
from .utils import process_payment, update_grand_parrain_reward, build_referral_tree
from django.db.models import Sum
User = get_user_model()

@login_required
def edit_profile_picture(request):
    user = request.user
    if request.method == 'POST':
        form = ProfilePictureForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('authentication:view_profile')
    else:
        form = ProfilePictureForm(instance=user)
    return render(request, 'authentication/edit_profile_picture.html', {'form': form})

class ParrainOnlyView(PermissionRequiredMixin, View):
    permission_required = 'authentication.permission_codename'


class UserLoginView(View):
    form_class = CustomUserAuthenticationForm
    template_name = 'authentication/user_login.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        users = CustomUser.objects.filter(is_superuser=False)  # Récupérer tous les utilisateurs avant connexion

        # Vérifier si l'utilisateur vient de s'inscrire
        if 'new_user' in request.session:
            new_user = request.session.pop('new_user')
            user = CustomUser.objects.get(username=new_user['username'])
            login(request, user)
            return redirect('authentication:user_dashboard')

        # Calcul des statistiques
        total_users = CustomUser.objects.filter(is_superuser=False).count()
        total_transactions = Transaction.objects.count()
        total_actions = total_users + total_transactions

        return render(request, self.template_name, {
            'form': form,
            'users': users,
            'total_users': total_users,
            'total_transactions': total_transactions,
            'total_actions': total_actions,
        })

    def post(self, request, *args, **kwargs):
        form = self.form_class(data=request.POST)
        show_password_reset_link = False
        users = CustomUser.objects.filter(is_superuser=False)  # Toujours récupérer les utilisateurs

        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            user = authenticate(request, username=username, password=password)

            if user is not None and isinstance(user, CustomUser):
                login(request, user)
                return redirect('admin:index') if user.is_superuser else redirect('authentication:user_dashboard')

            show_password_reset_link = True
            form.add_error(None, "Accès non autorisé ou identifiants invalides. Veuillez réessayer.")

        # Calcul des statistiques
        total_users = CustomUser.objects.filter(is_superuser=False).count()
        total_transactions = Transaction.objects.count()
        total_actions = total_users + total_transactions

        return render(request, self.template_name, {
            'form': form,
            'show_password_reset_link': True,
            'users': users,
            'total_users': total_users,
            'total_transactions': total_transactions,
            'total_actions': total_actions,
        })

@login_required
def user_logout(request):
    logout(request)
    return redirect('authentication:user_login')

def is_simple_user(user):
    return not user.is_superuser

@method_decorator(login_required, name='dispatch')
class UserDashboardView(LoginRequiredMixin, View):
    template_name = 'authentication/user_dashboard.html'

    def get(self, request, *args, **kwargs):
        user = request.user

        # Récupérer le portefeuille de l'utilisateur
        wallet = Wallet.objects.filter(user=user).first()

        # Récupération des transactions récentes
        transactions = Transaction.objects.filter(user=user).order_by('-created_at')[:10]

        # Récupérer les parrainages de l'utilisateur (parrainage non confirmé)
        referrals = Referral.objects.filter(referrer=user)

        # Récupérer le referral_uuid de l'utilisateur
        referral_uuid = user.referral_uuid

        # Calcul des slots remplis dans l'arbre de parrainage
        filled_slots = user.filled_slots
        total_slots = 20
        total_stage_slots=180
        slot_partage=user.slot_partage

        # Activité récente (parrainages récents)
        recent_activity = Referral.objects.filter(
            referrer=user, date_joined__lte=timezone.now()
        ).order_by('-date_joined')[:5]

        # Récupérer le nombre de notifications non lues pour l'utilisateur actuel
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

        # 🔥 Nouveau : Calcul du total des actions
        total_users = CustomUser.objects.count()
        total_transactions = Transaction.objects.count()
        total_actions = total_users + total_transactions  # Somme totale

        # Contexte pour le template
        context = {
            'user': user,
            'wallet_balance': wallet.balance if wallet else 0,
            'filled_slots': filled_slots,
            'total_slots': total_slots,
            'slot_partage': slot_partage,
            'total_stage_slots': total_stage_slots,
            'remaining_registrations': 25 - referrals.count(),
            'recent_activity': recent_activity,
            'transactions': transactions,
            'unread_count': unread_count,
            'referral_uuid': referral_uuid,
            'total_actions': total_actions,  # ✅ Ajout du total des actions
        }

        return render(request, self.template_name, context)

client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

def get_country_code(request):
    phone_number = request.GET.get('phone_number')
    if not phone_number:
        return JsonResponse({'error': 'Numéro de téléphone requis'}, status=400)

    try:
        # Effectuez la requête Lookup pour obtenir des informations sur le numéro
        number = client.lookups.phone_numbers(phone_number).fetch(type='carrier')
        country_code = number.country_code
        return JsonResponse({'country_code': country_code})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def register_referral(request):
    if request.method == 'POST':
        form = ReferralForm(request.POST)

        if form.is_valid():
            # Récupérer le parrain (l'utilisateur connecté)
            referrer = request.user
            referral_count = Referral.objects.filter(referrer=referrer).count()
            max_referrals = 25

            # Vérifier si le parrain a atteint le nombre maximal de filleuls
            if referral_count >= max_referrals:
                messages.error(request, f'Le parrain {referrer.username} a atteint le nombre maximum de {max_referrals} filleuls. Veuillez choisir un autre parrain.')
                return redirect('authentication:register_referral')

            form_data = form.cleaned_data
            password1 = form_data.pop('password1', None)
            password2 = form_data.pop('password2', None)

            if password1 and password1 == password2:
                hashed_password = make_password(password1)
                form_data['password'] = hashed_password
            else:
                messages.error(request, 'Les mots de passe ne correspondent pas.')
                return redirect('authentication:register_referral')

            # Ajouter le parrain (referrer) dans les données du formulaire
            form_data['referrer'] = referrer.id  # L'utilisateur connecté devient le parrain

            # Sérialiser les données pour les stocker dans la session
            for key, value in form_data.items():
                if isinstance(value, date):
                    form_data[key] = value.isoformat()
                elif isinstance(value, CustomUser):
                    form_data[key] = value.id
                elif isinstance(value, PhoneNumber):  # Si c'est un numéro de téléphone
                    form_data[key] = str(value)  # Convertir en chaîne de caractères

            # Sauvegarder les données dans la session
            request.session['referrer_username'] = referrer.username
            request.session['form_data'] = {key: value for key, value in form_data.items() if key != 'referrer'}

            return redirect('authentication:confirm_referral_payment')

        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')

    else:
        # Initialiser le formulaire, mais avec l'ID du parrain (l'utilisateur connecté)
        form = ReferralForm(initial={'referrer': request.user.id})

    return render(request, 'authentication/register_referral.html', {
        'form': form,

    })

class ConfirmReferralsView(LoginRequiredMixin, View):
    template_name = 'authentication/confirm_referrals.html'

    def get(self, request, *args, **kwargs):
        # Récupérer les parrainages non confirmés pour l'utilisateur connecté
        pending_referrals = Referral.objects.filter(
            referrer=request.user, is_confirmed=False, referred__is_confirmed=False
        )

        context = {
            'pending_referrals': pending_referrals
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        print(f"Request POST data: {request.POST}")  # Affiche tout le contenu de POST
        referral_uuid = request.POST.get('referral_uuid')

        if not referral_uuid:
            # En cas de problème, afficher un message d'erreur
            messages.error(request, "Impossible de confirmer : UUID du filleul manquant.")
            return redirect('authentication:confirm_referrals')

        try:
            # Vérifier que le filleul existe via son referral_uuid et appartient à l'utilisateur connecté
            referred_user = CustomUser.objects.get(referral_uuid=referral_uuid)
            referral = Referral.objects.get(
                referrer=request.user,
                referred=referred_user,
                is_confirmed=False,
                referred__is_confirmed=False
            )
        except CustomUser.DoesNotExist:
            messages.error(request, "Filleul introuvable avec cet UUID.")
            return redirect('authentication:confirm_referrals')
        except Referral.DoesNotExist:
            messages.error(request, "Parrainage invalide ou déjà confirmé.")
            return redirect('authentication:confirm_referrals')

        # Rediriger vers la page de paiement pour finaliser
        return redirect('authentication:confirm_referral_payment', referral_uuid=referral.referred.referral_uuid)
def confirm_referral_payment(request):
    # Récupérer le parrain à partir de la session
    referrer_username = request.session.get('referrer_username')

    if referrer_username:
        referrer = CustomUser.objects.get(username=referrer_username)
    else:
        # Gérer le cas où il n'y a pas de parrain dans la session
        messages.error(request, 'Aucun parrain trouvé.')
        return redirect('authentication:register_referral')

    # Si la méthode est POST, traiter le paiement
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'card')
        amount = 1000  # Montant fixe pour cet exemple

        try:
            # Vérification du mode de paiement
            if payment_method == 'card':
                card_number = request.POST.get('card_number')
                expiry_date = request.POST.get('expiry_date')
                cvv = request.POST.get('cvv')
                payment_method_types = ['card']
                # Vous pouvez ajouter ici des vérifications supplémentaires si nécessaire

            elif payment_method == 'google_pay':
                google_pay_email = request.POST.get('google_pay_email')
                payment_method_types = ['card', 'google_pay']
                # Ajoutez des vérifications supplémentaires ici si nécessaire

            elif payment_method == 'apple_pay':
                apple_pay_email = request.POST.get('apple_pay_email')
                payment_method_types = ['card', 'apple_pay']
                # Vérifications supplémentaires pour Apple Pay si nécessaire

            else:
                payment_method_types = ['card']

            # Création d'une session de paiement avec Stripe
            session = stripe.checkout.Session.create(
                payment_method_types=payment_method_types,
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': 'Produit',
                        },
                        'unit_amount': amount,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=request.build_absolute_uri(
                    reverse('authentication:stripe_payment_success')
                ) + '?session_id={CHECKOUT_SESSION_ID}&type=referral',
                cancel_url=request.build_absolute_uri(reverse('authentication:cancel')),
            )

            # Stocker les données nécessaires pour la vue success dans la session
            request.session['referral_data'] = {
                'referrer_username': referrer.username,
                'referrer_email': referrer.email,
            }

            # Rediriger l'utilisateur vers la page de paiement Stripe
            return redirect(session.url, code=303)

        except Exception as e:
            # Gérer les erreurs Stripe
            messages.error(request, f"Erreur Stripe : {str(e)}")
            return redirect('authentication:confirm_referral_payment')

    # Récupérer les données de référence (filleul, etc.)
    referral_data = {
        'referrer_username': referrer.username,
        'referrer_email': referrer.email,
        # Vous pouvez ajouter d'autres informations pertinentes ici
    }

    # Rendre la page de confirmation de paiement
    return render(request, 'authentication/confirm_referral_payment.html', {
        'referrer': referrer,
        'referral_data': referral_data,
    })


def user_signup(request):
    total_users = CustomUser.objects.filter(is_superuser=False).count()
    total_transactions = Transaction.objects.count()
    total_actions = total_users + total_transactions  # 🔥 Calcul du total des actions

    if request.method == 'POST':
        form = ReferralForm(request.POST)

        if form.is_valid():
            referrer = form.cleaned_data['referrer']
            referral_count = Referral.objects.filter(referrer=referrer).count()
            max_referrals = 25

            if referral_count >= max_referrals:
                messages.error(request, f'Le parrain {referrer.username} a atteint le nombre maximum de {max_referrals} filleuls. Veuillez choisir un autre parrain.')
                return redirect('authentication:user_signup')

            form_data = form.cleaned_data
            password1 = form_data.pop('password1', None)
            password2 = form_data.pop('password2', None)

            if password1 and password1 == password2:
                hashed_password = make_password(password1)
                form_data['password'] = hashed_password
            else:
                messages.error(request, 'Les mots de passe ne correspondent pas.')
                return redirect('authentication:user_signup')

            for key, value in form_data.items():
                if isinstance(value, date):
                    form_data[key] = value.isoformat()
                elif isinstance(value, CustomUser):
                    form_data[key] = value.id
                elif isinstance(value, PhoneNumber):  # Si c'est un numéro de téléphone
                    form_data[key] = str(value)

            request.session['referrer_username'] = referrer.username
            request.session['form_data'] = {key: value for key, value in form_data.items() if key != 'referrer'}

            return redirect('authentication:payment')

        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')

    else:
        form = ReferralForm()

    return render(request, 'authentication/user_signup.html', {
        'form': form,
        'total_actions': total_actions  # ✅ Ajout au contexte
    })

def userlink_signup(request):
    # Calcul des statistiques des utilisateurs et des transactions
    total_users = CustomUser.objects.filter(is_superuser=False).count()
    total_transactions = Transaction.objects.count()
    total_actions = total_users + total_transactions  # 🔥 Calcul du total des actions

    # Récupération du paramètre "referrer" dans l'URL
    referrer_username = request.GET.get('referrer')

    # Lever une erreur 404 si aucun referrer n'est fourni
    if not referrer_username:
        raise Http404("Aucun parrain spécifié.")

    # Tenter de récupérer le parrain, sinon lever une erreur 404
    referrer = get_object_or_404(CustomUser, username=referrer_username)

    # Traitement du formulaire
    if request.method == 'POST':
        form = ReferrallinkForm(request.POST)

        if form.is_valid():
            referrer = form.cleaned_data['referrer']
            referral_count = Referral.objects.filter(referrer=referrer).count()
            max_referrals = 25  # Limite de filleuls par parrain

            # Vérifier si le parrain a atteint sa limite de filleuls
            if referral_count >= max_referrals:
                messages.error(request, f'Le parrain {referrer.username} a atteint le maximum de {max_referrals} filleuls.')
                return redirect('authentication:user_signup')

            form_data = form.cleaned_data
            password1 = form_data.pop('password1', None)
            password2 = form_data.pop('password2', None)

            # Vérification des mots de passe
            if password1 and password1 == password2:
                form_data['password'] = make_password(password1)
            else:
                messages.error(request, 'Les mots de passe ne correspondent pas.')
                return redirect('authentication:userlink_signup')

            # Conversion des données spécifiques
            for key, value in form_data.items():
                if isinstance(value, date):
                    form_data[key] = value.isoformat()
                elif isinstance(value, CustomUser):
                    form_data[key] = value.id
                elif isinstance(value, PhoneNumber):
                    form_data[key] = str(value)

            # Stocker les informations dans la session
            request.session['referrer_username'] = referrer.username
            request.session['form_data'] = {key: value for key, value in form_data.items() if key != 'referrer'}

            return redirect('authentication:payment')

        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')

    else:
        # Pré-remplir le champ referrer
        form = ReferrallinkForm(initial={'referrer': referrer})

    return render(request, 'authentication/userlink_signup.html', {
        'form': form,
        'total_actions': total_actions
    })
def custom_page_not_found(request, exception=None):
    return render(request, 'errors/404.html', {}, status=404)
def confirm_payment_ref(request, referral_uuid):
    # Récupérer l'utilisateur connecté
    user = request.user

    # Afficher la valeur de is_confirmed
    print(f"Utilisateur : {user.username}, is_confirmed : {user.is_confirmed}, ID : {user.id}")

    # Récupérer l'utilisateur associé à l'UUID du referral
    user_from_uuid = get_object_or_404(CustomUser, referral_uuid=referral_uuid)

    # Vérifier que l'utilisateur connecté correspond bien à celui du referral_uuid
    if user != user_from_uuid:
        messages.error(request, "Vous ne pouvez confirmer que votre propre inscription.")
        return redirect('authentication:user_dashboard')  # Rediriger vers le tableau de bord

    # Vérifier si l'inscription de l'utilisateur est déjà confirmée
    if user.is_confirmed:
        messages.info(request, "Vous avez déjà confirmé votre inscription.")
        return redirect('authentication:user_dashboard')  # Rediriger vers le tableau de bord

    # Si non confirmé, rediriger vers la page de paiement
    messages.warning(request, "Veuillez confirmer votre inscription en effectuant le paiement.")
    return redirect('authentication:payment')

@login_required
def pending_referrals(request):
    user = request.user
    # Filtrer les filleuls de l'utilisateur connecté dont l'inscription n'est pas confirmée
    pending_referrals = Referral.objects.filter(
        referrer=user,
        is_confirmed=False  # On ne prend que ceux qui n'ont pas confirmé leur inscription
    )

    return render(request, 'authentication:confirm_referrals.html', {
        'pending_referrals': pending_referrals
    })
stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
def create_checkout_session(request):
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'card')
        amount = 1000  # Montant fixe pour cet exemple

        try:
            if payment_method == 'card':
                card_number = request.POST.get('card_number')
                expiry_date = request.POST.get('expiry_date')
                cvv = request.POST.get('cvv')
                payment_method_types = ['card']
                # Vous pouvez utiliser ces informations pour des vérifications supplémentaires si nécessaire

            elif payment_method == 'google_pay':
                google_pay_email = request.POST.get('google_pay_email')
                payment_method_types = ['card', 'google_pay']
                # Utilisez google_pay_email pour des vérifications supplémentaires si nécessaire

            elif payment_method == 'apple_pay':
                apple_pay_email = request.POST.get('apple_pay_email')
                payment_method_types = ['card', 'apple_pay']
                # Utilisez apple_pay_email pour des vérifications supplémentaires si nécessaire

            else:
                payment_method_types = ['card']

            session = stripe.checkout.Session.create(
                payment_method_types=payment_method_types,
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': 'Produit',
                        },
                        'unit_amount': amount,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=request.build_absolute_uri(
                    reverse('authentication:success')
                ) + '?session_id={CHECKOUT_SESSION_ID}&type=confirmation&payment_method=' + payment_method,
                cancel_url=request.build_absolute_uri(reverse('authentication:cancel')),
            )

            return redirect(session.url, code=303)
        except Exception as e:
            return redirect(reverse('authentication:error') + f'?payment_method=Stripe&error={str(e)}')

    return render(request, 'authentication/payment.html')
def cancel(request):
    return render(request, 'authentication/cancel.html')


def success(request):
    session_id = request.GET.get('session_id')
    payment_method = request.GET.get('payment_method')
    user = None

    try:
        session = stripe.checkout.Session.retrieve(session_id)

        if session.payment_status == 'paid':
            # Récupérer le form_data et tenter de récupérer le parrain depuis la session
            form_data = request.session.get('form_data')
            referrer_username = request.session.get('referrer_username')

            if not form_data:
                messages.error(request, "Données du formulaire manquantes.")
                return redirect('authentication:user_signup')

            # Si la donnée 'referrer_username' n'est pas présente dans la session,
            # on essaie de la récupérer depuis form_data (clé 'referrer')
            if not referrer_username:
                referrer_username = form_data.get('referrer')

            if not referrer_username:
                messages.error(request, "Le parrain n'est pas renseigné.")
                return redirect('authentication:user_signup')

            try:
                referrer = CustomUser.objects.get(username=referrer_username)
            except CustomUser.DoesNotExist:
                messages.error(request, "Le parrain spécifié n'existe pas.")
                return redirect('authentication:user_signup')

            # Convertir les objets PhoneNumber en chaînes de caractères
            for key, value in form_data.items():
                if isinstance(value, PhoneNumber):
                    form_data[key] = str(value)

            # Vérifier si le nom d'utilisateur existe déjà
            username = form_data.get('username')
            if CustomUser.objects.filter(username=username).exists():
                messages.error(request, f"Le nom d'utilisateur {username} est déjà pris. Veuillez en choisir un autre.")
                return redirect('authentication:user_signup')

            # Créer l'utilisateur avec le mot de passe haché
            hashed_password = form_data.pop('password')
            user = CustomUser(**form_data)
            user.password = hashed_password  # Le mot de passe est déjà haché
            user.referrer = referrer
            user.save()

            if user:
                referral_instance, created = Referral.objects.get_or_create(
                    referred_user=user,
                    defaults={
                        'referrer': referrer,
                        'referred': user,
                        'date_joined': timezone.now(),
                        'stage': 1,
                        'reward_amount': Decimal('0.00'),
                        'slot_partage': False,
                        'total_slots': 0,
                        'used_slots': 0,
                        'position': 0,
                        'filled_slots': 0,
                        'is_confirmed': False
                    }
                )
                # Marquer l'utilisateur et l'instance de parrainage comme confirmés
                user.is_confirmed = True
                user.is_donateur = True
                user.save()
                referral_instance.is_confirmed = True
                referral_instance.save()

                EXCHANGE_RATE = Decimal('600')

                # Calcul et ajout de la récompense pour le parrain
                amount_to_transfer = Decimal(session.amount_total) * Decimal('0.10')  # 10% du montant total en dollars
                amount_in_fcfa = amount_to_transfer * EXCHANGE_RATE  # Conversion en FCFA

                wallet, created_wallet = Wallet.objects.get_or_create(user=referrer)
                wallet.balance += amount_in_fcfa / Decimal('100')  # Si balance est en FCFA, retirer "/ Decimal('100')"
                wallet.save()

                transaction_record = Transaction(
                    user=user,
                    amount=Decimal(session.amount_total) / Decimal('100'),
                    reason=f"Paiement de comission de confirmation au parrain pour son filleul {user.username}",
                    is_successful=True
                )
                transaction_record.save()

                if referrer.contact:
                    message = (
                        f"Bonjour {referrer.username},\n"
                        f"Vous venez d'etre inscrit avec succes et Votre parrainage a été confirmé avec succès !\n"
                        f"Détails de la transaction :\n"
                        f"Montant : {Decimal(session.amount_total) / Decimal('100')} {session.currency.upper()}\n"
                        f"Transaction ID : {session.payment_intent}\n"
                        f"Merci de votre soutien."
                    )
                    send_sms(referrer.contact, message)
                message_for_referrer = (
                    f"Bonjour {referral.referrer.username},\n"
                    f"Votre filleul {user.username} vient de s'inscrire avec succès avec votre code de parrainage !"
                )

                # Message pour le filleul
                message_for_referred = (
                    f"Bonjour {user.username},\n"
                    f"Bienvenue sur notre plateforme ! Vous êtes inscrit avec succès.\n"
                    f"Votre parrain est {referral.referrer.username}."
                )

                # Créer les notifications
                create_notification(referral, message_for_referrer, message_for_referred)
                PaymentMethod.objects.create(
                    user=user,
                    amount=Decimal(session.amount_total) / Decimal('100'),
                    is_successful=True,
                )

            payment_details = {
                'payment_method': 'Stripe',
                'amount': Decimal(session.amount_total) / Decimal('100'),
                'currency': session.currency.upper(),
                'transaction_id': session.payment_intent,
                'email': user.email if user else '',
                'username': user.username if user else '',
                'status': session.payment_status,
            }

            return render(request, 'authentication/success.html', {'payment_details': payment_details})

    except stripe.error.StripeError as e:
        return render(request, 'authentication/error.html', {'error': str(e)})


def verify_wallet_payment(request):
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        amount = 5000  # Coût de l'inscription

        if payment_method != 'wallet':
            return redirect('authentication:payment')

        user = request.user  # le parrain ici
        if not user.is_authenticated:
            messages.error(request, "Vous devez être connecté pour inscrire un filleul.")
            return redirect('authentication:user_login')

        if user.wallet.balance >= amount:
            # On redirige vers la vue qui va effectuer l'inscription du filleul
            return redirect(reverse('authentication:wallet_payment_success') + f'?amount={amount}')
        else:
            messages.error(request, "Solde insuffisant dans votre portefeuille.")
            return redirect('authentication:confirm_referral_payment')

def wallet_payment_success(request):
    if not request.user.is_authenticated:
        messages.error(request, "Vous devez être connecté.")
        return redirect('authentication:user_login')

    parrain = request.user
    amount = 5000  # Coût de l'inscription
    commission_parrain = 500  # Récompense pour le parrain

    form_data = request.session.get('form_data')
    if not form_data:
        messages.error(request, "Données du filleul manquantes.")
        return render(request, 'authentication/confirm_referral_payment.html')

    try:
        # Déduction du montant (le solde a déjà été vérifié)
        parrain.wallet.balance -= amount
        parrain.wallet.save()

        # Créer le nouvel utilisateur (filleul)
        new_filleul = CustomUser.objects.create_user(
            username=form_data['username'],
            email=form_data['email'],
            password=form_data['password'],  # On prend ici le mot de passe validé
            first_name=form_data['nom'],
            last_name=form_data['prenom'],
            nompop=form_data['nompop'],
            nationalite=form_data['nationalite'],
            sexe=form_data['sexe'],
            profession=form_data['profession'],
            lieu_travail=form_data['lieu_travail'],
            country=form_data['country'],
            ville=form_data['ville'],
            quartier=form_data['quartier'],
            maison_non_loin_de=form_data['maison_non_loin_de'],
            contact=form_data['contact'],
            date_of_birth=form_data['date_of_birth'],
            referrer=parrain,
        )
        new_filleul.save()

        # Récupérer la relation de parrainage
        referral = Referral.objects.get(referrer=parrain, referred=new_filleul)

        # Mettre à jour le statut de confirmation
        referral.is_confirmed = True
        referral.save()

        # Confirmer également le filleul
        new_filleul.is_confirmed = True
        new_filleul.is_donateur = True
        new_filleul.save()

        # Récompense pour le parrain
        parrain.wallet.balance += commission_parrain
        parrain.wallet.save()

        # Enregistrement de la transaction
        Transaction.objects.create(
            user=parrain,
            amount=Decimal(amount)/ Decimal('100'),
            reason=f"Paiement de comission de confirmation au parrain pour son filleul {user.username}",
            is_successful=True
        )

        # Enregistrement de la méthode de paiement
        PaymentMethod.objects.create(
            user=parrain,
            amount=amount,
            is_successful=True,
        )

        # Création de la relation de parrainage
        Referral.objects.create(
            referrer=parrain,
            referred=new_filleul
        )

        # Optionnel : SMS au parrain
        if parrain.contact:
            send_sms(parrain.contact, f"Filleul {new_filleul.username} inscrit avec succès. Bonus reçu : {commission_parrain} FCFA.")

        messages.success(request, f"{new_filleul.username} inscrit avec succès !")
        return redirect('authentication:wallet_payment_success')

    except IntegrityError as e:
        messages.error(request, f"Erreur lors de l'inscription : {e}")
        return redirect('authentication:user_signup')

    # Dans le cas où le formulaire contient des erreurs, on le retourne à la vue
    form = RegisterReferralForm()
    return render(request, 'authentication/wallet_payment_success.html', {'form': form})

def error(request):
    payment_method = request.GET.get('payment_method', 'unknown')
    error_message = request.GET.get('error', 'Erreur inconnue')
    return render(request, 'authentication/error.html', {'payment_method': payment_method, 'error': error_message})
def stripe_payment_success(request):
    # Récupérer le session_id depuis les paramètres GET
    session_id = request.GET.get('session_id')
    referral_data = request.session.get('referral_data')

    if not session_id:
        messages.error(request, "ID de session Stripe manquant.")
        return render(request, 'authentication/confirm_referral_payment.html')

    if not referral_data:
        messages.error(request, "Données du parrain manquantes.")
        return render(request, 'authentication/confirm_referral_payment.html')

    # Récupérer le parrain depuis la session
    referrer_username = referral_data.get('referrer_username')
    referrer = CustomUser.objects.get(username=referrer_username)

    # Vérifier que les données du filleul existent dans la session
    form_data = request.session.get('form_data')
    if not form_data:
        messages.error(request, "Données du filleul manquantes.")
        return render(request, 'authentication/confirm_referral_payment.html')

    try:
        # Créer le nouvel utilisateur (filleul) sans avoir besoin de referral_uuid
        new_filleul = CustomUser.objects.create_user(
            username=form_data['username'],
            email=form_data['email'],
            password=form_data['password'],  # On prend ici le mot de passe validé
            first_name=form_data['nom'],
            last_name=form_data['prenom'],
            nompop=form_data['nompop'],
            nationalite=form_data['nationalite'],
            sexe=form_data['sexe'],
            profession=form_data['profession'],
            lieu_travail=form_data['lieu_travail'],
            country=form_data['country'],
            ville=form_data['ville'],
            quartier=form_data['quartier'],
            maison_non_loin_de=form_data['maison_non_loin_de'],
            contact=form_data['contact'],
            date_of_birth=form_data['date_of_birth'],
            referrer=referrer,
        )
        new_filleul.save()

        # Récupérer la relation de parrainage
        referral = Referral.objects.get(referrer=referrer, referred=new_filleul)

        # Mettre à jour le statut de confirmation
        referral.is_confirmed = True
        referral.save()

        # Confirmer également le filleul
        new_filleul.is_confirmed = True
        new_filleul.is_donateur = True
        new_filleul.save()

        # Effacer les données de session après création du filleul
        del request.session['referral_data']
        del request.session['form_data']

    except IntegrityError as e:
        messages.error(request, f"Erreur lors de la création du filleul: {str(e)}")
        return render(request, 'authentication/confirm_referral_payment.html')

    try:
        # Récupérer les détails de la session Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        amount_total = Decimal(session.amount_total) / Decimal('100')  # Montant total payé
        EXCHANGE_RATE = Decimal('600')

        # Calcul et ajout de la récompense pour le parrain
        amount_to_transfer = Decimal(session.amount_total) * Decimal('0.10')  # 10% du montant total en dollars
        amount_in_fcfa = amount_to_transfer * EXCHANGE_RATE  # Conversion en FCFA

        wallet, created_wallet = Wallet.objects.get_or_create(user=referrer)
        wallet.balance += amount_in_fcfa / Decimal('100')  # Si balance est en FCFA, retirer "/ Decimal('100')"
        wallet.save()
        # Ajouter la récompense au wallet du parrain
        if referrer:
            wallet, created = Wallet.objects.get_or_create(user=referrer)
            wallet.balance += amount_to_transfer
            wallet.save()

            # Enregistrer la transaction dans le wallet
            transaction_record = Transaction(
                user=referrer,
                amount=amount_to_transfer,
                reason=f"Récompense pour confirmation d'inscription du filleul {new_filleul.username}",
                is_successful=True
            )
            transaction_record.save()

            if referrer.contact:
                message_referrer = (
                    f"Bonjour {referrer.username},\n"
                    f"Vous avez confirmé avec succès le parainnage de votre fieul !\n"
                    f"Détails de la transaction :\n"
                    f"Montant : {Decimal(session.amount_total) / Decimal('100')} {session.currency.upper()}\n"
                    f"Transaction ID : {session.payment_intent}\n"
                    f"Merci de votre soutien."
                )
                send_sms(referrer.contact, message_referrer)

            if new_filleul.contact:
                message_new_filleul = (
                    f"Bonjour {new_filleul.username},\n"
                    f"Votre enregistrement a été confirmé avec succès par votre parrain {referrer.username} !\n"
                    f"Détails de la transaction :\n"
                    f"Montant payé : {Decimal(session.amount_total) / Decimal('100')} {session.currency.upper()}\n"
                    f"Transaction ID : {session.payment_intent}\n"
                    f"Merci d'avoir rejoint notre plateforme."
                )
                send_sms(new_filleul.contact, message_new_filleul)
            message_for_referrer = (
                f"Bonjour {referral.referrer.username},\n"
                f"Vous venez d'inscrire votre filleul {new_filleul.username}  avec succès !"
            )

            # Message pour le filleul
            message_for_referred = (
                f"Bonjour {user.username},\n"
                f"Bienvenue sur notre plateforme ! Vous êtes inscrit avec succès par votre parrain.\n"
                f"Votre parrain est {referral.referrer.username}."
            )

            # Créer les notifications
            create_notification(referral, message_for_referrer, message_for_referred)
            # Enregistrer la méthode de paiement
            PaymentMethod.objects.create(
                user=referrer,  # Utilisation de 'referrer' comme utilisateur
                amount=amount_total,
                is_successful= True,
            )

    except stripe.error.StripeError as e:
        messages.error(request, f"Erreur Stripe : {str(e)}")
        return render(request, 'authentication/confirm_referrals.html')

    # Préparer les informations de paiement pour affichage
    payment_details = {
        'session_id' : session_id,
        'referrer_email': referrer.email,
        'referred_email': new_filleul.email,
        'payment_method': 'Stripe',
        'amount_paid': amount_total,
        'reward_to_referrer': amount_to_transfer,
        'currency': session.currency.upper(),
        'transaction_id': session.payment_intent,
        'payment_status': session.payment_status,
    }

    # Rendre la page de succès
    return render(request, 'authentication/stripe_payment_success.html', {'payment_details': payment_details})

def paypal_payment(request):
    if request.method == 'POST':
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": request.build_absolute_uri(reverse('authentication:success')),
                "cancel_url": request.build_absolute_uri(reverse('authentication:cancel'))
            },
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": "Produit",
                        "sku": "001",
                        "price": "10.00",
                        "currency": "USD",
                        "quantity": 1
                    }]
                },
                "amount": {
                    "total": "10.00",
                    "currency": "USD"
                },
                "description": "Description du produit."
            }]
        })

        if payment.create():
            for link in payment.links:
                if link.rel == "approval_url":
                    return redirect(link.href)
        else:
            # Redirection avec les détails de l'erreur
            return redirect('authentication:error', {'payment_method': 'PayPal', 'error': payment.error})

    return render(request, 'authentication/payment.html')

def paypal_payment_success(request):
    # Vous pouvez traiter la réponse après la réussite de la transaction
    transaction_id = request.GET.get('paymentId')
    user = request.user  # Supposons que l'utilisateur est authentifié
    amount = 20.00  # Exemple de montant fixe ici
    currency = 'USD'

    # Logique pour vérifier que la transaction est valide
    # (Ajoutez ici le code pour vérifier le paiement auprès de PayPal, si nécessaire)

    # Enregistrer la transaction dans la base de données
    transaction = Transaction.objects.create(
        user=user,
        amount=amount,
        reason=f'Paiement réussi via PayPal (Transaction ID: {transaction_id})'
    )

    # Mettre à jour le solde du portefeuille de l'utilisateur, si applicable
    wallet, created = Wallet.objects.get_or_create(user=user)
    wallet.balance += amount  # Ajoutez le montant au solde
    wallet.save()

    # Créer une notification pour l'utilisateur
    create_notification(user, f'Votre paiement de {amount} {currency} a été confirmé avec succès.')

    messages.success(request, "Votre paiement a été traité avec succès.")
    return render(request, 'authentication/paypal_success.html', {
        'payment_method': 'PayPal',
        'amount': amount,
        'currency': currency,
        'transaction_id': transaction_id
    })
    return render(request, 'authentication/success.html', context)

def payment_error(request):
    context = {
        'payment_method': request.GET.get('payment_method', 'Inconnu'),
        'error': request.GET.get('error', 'Une erreur est survenue.')
    }
    return render(request, 'authentication/error.html', context)


def initiate_payment_cinet(request):
    if request.method == "POST":
        montant = 5000  # Récupérer le montant

        transaction_id = str(uuid.uuid4())  # ID unique de la transaction
        payment_channel = request.POST.get("payment_channel")  # Récupère le canal de paiement
        channels_map = {
            "tmoney": "MOBILE_MONEY",
            "flooz": "MOBILE_MONEY",  # À adapter selon le canal exact
            "mobile_money": "MOBILE_MONEY"
        }
        payload = {
            "apikey": settings.CINETPAY_API_KEY,
            "site_id": settings.CINETPAY_SITE_ID,
            "transaction_id": transaction_id,
            "amount": montant,
            "currency": "XOF",
            "description": "Paiement d'adhesion",
            "return_url": "http://127.0.0.1:8000/authentication/payment_success_cinet/",
            "notify_url": "http://127.0.0.1:8000/authentication/payment-notify/",
            "channels": channels_map.get(payment_channel, "MOBILE_MONEY"),
            "method": payment_channel,
            "customer_name": request.user.username,

        }
        headers = {"Content-Type": "application/json"}
        response = requests.post(settings.CINETPAY_BASE_URL, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print("Response data:", data)
            if data.get("code") == "201":
                return redirect(data["data"]["payment_url"])
            else:
                return render(request, "authentication/payment_error_cinet.html", {"error": data.get("message")})
        else:
            return render(request, "authentication/payment_error_cinet.html", {"error": "Erreur de communication avec CinetPay."})

    return render(request, "authentication/payment.html")
@csrf_exempt
def payment_notify(request):
    if request.method == "POST":
        data = request.POST  # Données envoyées par CinetPay
        transaction_id = data.get("transaction_id")
        status = data.get("status")
        signature = data.get("signature")  # Signature envoyée par CinetPay

        # Créer une signature à partir des données et de la clé secrète
        payload = f"{transaction_id}|{status}|{settings.CINETPAY_SECRET_KEY}"
        generated_signature = hmac.new(settings.CINETPAY_SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()

        if generated_signature == signature:
            # La notification est valide, effectuer les actions nécessaires
            # Exemple : marquer la commande comme payée
            # Votre logique pour gérer la réussite du paiement
            return HttpResponse("Notification validée", status=200)
        else:
            # Signature incorrecte, sécurité
            return HttpResponse("Erreur de validation", status=400)

    return HttpResponse("Méthode non autorisée", status=405)


@csrf_exempt
def payment_notify(request):
    if request.method == "POST":
        data = request.POST  # Données envoyées par CinetPay
        transaction_id = data.get("transaction_id")
        status = data.get("status")
        signature = data.get("signature")  # Signature envoyée par CinetPay

        # Créer une signature à partir des données et de la clé secrète
        payload = f"{transaction_id}|{status}|{settings.CINETPAY_SECRET_KEY}"
        generated_signature = hmac.new(settings.CINETPAY_SECRET_KEY.encode(), payload.encode(),
                                       hashlib.sha256).hexdigest()

        if generated_signature == signature:
            # La notification est valide, effectuer les actions nécessaires
            return HttpResponse("Notification validée", status=200)
        else:
            # Signature incorrecte, sécurité
            return HttpResponse("Erreur de validation", status=400)

    return HttpResponse("Méthode non autorisée", status=405)


import logging

logger = logging.getLogger(__name__)


def payment_success_cinet(request):
    transaction_id = request.GET.get("transaction_id")

    payload = {
        "apikey": settings.CINETPAY_API_KEY,
        "site_id": settings.CINETPAY_SITE_ID,
        "transaction_id": transaction_id,
    }

    try:
        response = requests.post(f"{settings.CINETPAY_BASE_URL}/check", json=payload)
        response.raise_for_status()  # Vérifie si la requête a réussi
        data = response.json()

        if data["data"]["status"] == "ACCEPTED":
            # Enregistrer le paiement dans la base de données
            PaymentMethod.objects.create(
                user=request.user,
                amount=data["data"]["amount"],
                method_name=data["data"]["payment_method"],
            )

            # Créer l'utilisateur dans la base de données
            form_data = request.session.get('form_data')
            logger.debug(f"Form data: {form_data}")
            if form_data:
                new_user = CustomUser.objects.create(**form_data)
                messages.success(request, "Compte créé avec succès !")

                # Récupérer le parrain et créditer son portefeuille
                referrer_username = request.session.get('referrer_username')
                logger.debug(f"Referrer username: {referrer_username}")
                if referrer_username:
                    referrer = CustomUser.objects.get(username=referrer_username)
                    referrer_wallet = referrer.wallet  # Assurez-vous que le modèle CustomUser a un champ wallet
                    referrer_wallet.balance += data["data"]["amount"] * 0.5
                    referrer_wallet.save()
                    messages.success(request,
                                     f"Le portefeuille du parrain {referrer.username} a été crédité de {data['data']['amount'] * 0.5} XOF.")

                    # Envoyer un SMS au parrain
                    if referrer.contact:
                        message_referrer = (
                            f"Bonjour {referrer.username},\n"
                            f"Vous avez confirmé avec succès le parrainage de votre filleul !\n"
                            f"Détails de la transaction :\n"
                            f"Montant : {Decimal(data['data']['amount'])} XOF\n"
                            f"Transaction ID : {transaction_id}\n"
                            f"Merci de votre soutien."
                        )
                        send_sms(referrer.contact, message_referrer)

                # Envoyer un SMS au nouvel utilisateur
                if new_user.contact:
                    message_new_user = (
                        f"Bonjour {new_user.username},\n"
                        f"Votre enregistrement a été confirmé avec succès par votre parrain !\n"
                        f"Détails de la transaction :\n"
                        f"Montant payé : {Decimal(data['data']['amount'])} XOF\n"
                        f"Transaction ID : {transaction_id}\n"
                        f"Merci d'avoir rejoint notre plateforme."
                    )
                    send_sms(new_user.contact, message_new_user)

                return render(request, "authentication/payment_success_cinet.html",
                              {"message": "Paiement réussi et compte créé !"})
            else:
                return render(request, "authentication/payment_error_cinet.html",
                              {"error": "Échec de la création du compte."})
        else:
            return render(request, "authentication/payment_error_cinet.html", {"error": "Échec du paiement."})
    except requests.RequestException as e:
        return render(request, "authentication/payment_error_cinet.html", {"error": str(e)})


def payment_error_cinet(request):
    error_message = request.GET.get("error", "Une erreur inconnue est survenue.")
    return render(request, "authentication/payment_error_cinet.html", {"error": error_message})

@login_required
def transaction_history(request):
    # Récupérer les transactions de l'utilisateur
    transactions = Transaction.objects.filter(user=request.user).order_by('-timestamp')

    # Envoyer une notification à l'utilisateur lors de l'accès à l'historique des transactions
    send_notification(request.user, 'Vous avez consulté votre historique des transactions.')

    return render(request, 'authentication/transaction_history.html', {'transactions': transactions})


@login_required
def edit_profile(request):
    user = CustomUser.objects.get(id=request.user.id)
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('authentication:view_profile')
    else:
        form = ProfileUpdateForm(instance=user)
    return render(request, 'authentication/edit_profile.html', {'form': form})


def update_user_stage_on_filled_slots_change(user, referral):
    """
    Met à jour le stage de l'utilisateur et accorde des récompenses à l'utilisateur,
    son parrain et son grand parrain après avoir terminé le stage précédent.
    """

    # Récupérer la somme totale des filled_slots
    total_filled_slots = Referral.objects.filter(referred=user).aggregate(total=Sum('filled_slots'))['total'] or 0

    # Calcul du stage (chaque tranche de 20 filled_slots = +1 stage)
    new_stage = min(10, max(1, (total_filled_slots // 20) + 1))

    # Vérifier si l'utilisateur a terminé un stage avant de passer au suivant
    if user.stage != new_stage:
        old_stage = user.stage
        user.stage = new_stage
        user.save()
        print(f"✅ Le stage de {user.username} a été mis à jour de {old_stage} à {new_stage}")

        # Récompenses pour l'utilisateur, son parrain et son grand parrain basées sur le stage précédent
        if old_stage == 1:
            reward_user(user, 8500)
            if referral.referrer:
                reward_user(referral.referrer, 1500, is_sponsor=True)
            if referral.referrer and referral.referrer.referrer:
                reward_user(referral.referrer.referrer, 750, is_sponsor=True)

        elif old_stage == 2:
            reward_user(user, 30000)
            if referral.referrer:
                reward_user(referral.referrer, 4500, is_sponsor=True)
            if referral.referrer and referral.referrer.referrer:
                reward_user(referral.referrer.referrer, 2225, is_sponsor=True)

        elif old_stage == 3:
            reward_user(user, 91800)
            if referral.referrer:
                reward_user(referral.referrer, 12300, is_sponsor=True)
            if referral.referrer and referral.referrer.referrer:
                reward_user(referral.referrer.referrer, 6000, is_sponsor=True)

        elif old_stage == 4:
            reward_user(user, 275400)
            if referral.referrer:
                reward_user(referral.referrer, 43900, is_sponsor=True)
            if referral.referrer and referral.referrer.referrer:
                reward_user(referral.referrer.referrer, 21950, is_sponsor=True)

        elif old_stage == 5:
            reward_user(user, 82630)
            if referral.referrer:
                reward_user(referral.referrer, 130700, is_sponsor=True)
            if referral.referrer and referral.referrer.referrer:
                reward_user(referral.referrer.referrer, 65350, is_sponsor=True)

        elif old_stage == 6:
            reward_user(user, 2478600)
            if referral.referrer:
                reward_user(referral.referrer, 313100, is_sponsor=True)
            if referral.referrer and referral.referrer.referrer:
                reward_user(referral.referrer.referrer, 156550, is_sponsor=True)

        elif old_stage == 7:
            reward_user(user, 7435000)
            if referral.referrer:
                reward_user(referral.referrer, 1209300, is_sponsor=True)
            if referral.referrer and referral.referrer.referrer:
                reward_user(referral.referrer.referrer, 604650, is_sponsor=True)

        elif old_stage == 8:
            reward_user(user, 22307400)
            if referral.referrer:
                reward_user(referral.referrer, 3517700, is_sponsor=True)
            if referral.referrer and referral.referrer.referrer:
                reward_user(referral.referrer.referrer, 1758850, is_sponsor=True)

        elif old_stage == 9:
            reward_user(user, 88922250)
            if referral.referrer:
                reward_user(referral.referrer, 11033700, is_sponsor=True)
            if referral.referrer and referral.referrer.referrer:
                reward_user(referral.referrer.referrer, 5516850, is_sponsor=True)

        elif old_stage == 10:
            reward_user(user, 102573800)
            if referral.referrer:
                reward_user(referral.referrer, 32461100, is_sponsor=True)
            if referral.referrer and referral.referrer.referrer:
                reward_user(referral.referrer.referrer, 16230550, is_sponsor=True)

    # Mise à jour du stage pour le parrain uniquement si nécessaire
    if referral.referred.stage != new_stage:
        referral.referred.stage = new_stage
        referral.referred.save()
        print(f"✅ Le stage de {referral.referred.username} a été mis à jour à : {new_stage}")

def reward_user(user, amount, is_sponsor=False):
    """
    Fonction pour accorder des récompenses à l'utilisateur ou au parrain/grand parrain.
    Si is_sponsor est True, cela signifie qu'il s'agit du parrain ou grand parrain.
    """
    if is_sponsor:
        print(f"✅ Récompense de {amount} CFA accordée au parrain/grand parrain {user.username}")
    else:
        print(f"✅ Récompense de {amount} CFA accordée à l'utilisateur {user.username}")

    # Logique pour l'attribution de la récompense
    # Exemple : ajout de la récompense au portefeuille de l'utilisateur
    user.wallet.balance += amount
    user.wallet.save()
    print(f"💰 Nouveau solde de {user.username}: {user.wallet.balance} CFA")
# Ajouter la récompense au registre de caisse
    cash_register = CashRegister.objects.first()  # Vous pouvez ajuster la logique si vous avez plusieurs registres
    if cash_register:
        cash_register.add_funds(amount)  # Ajouter le montant de la récompense
        print(f"💸 Montant de {amount} CFA ajouté au registre de caisse pour {user.username}")
    transaction_record = Transaction(
        user=user,
        amount=amount,
        reason=f"Récompense de stage {user.stage}" if not is_sponsor else "recompense de fin de stage",
        is_successful=True
    )
    transaction_record.save()
    print(f"💳 Transaction enregistrée pour {user.username} : {transaction_record.amount} CFA")

def update_filled_slots_and_check_promotion(user, filled_slots):
    """
    Met à jour le champ filled_slots dans Referral pour l'utilisateur référé,
    et met aussi à jour filled_slots dans CustomUser, en fonction du stage de l'utilisateur.
    Les slots sont cumulés en fonction du stage actuel.
    """
    try:
        # Récupérer le Referral où l'utilisateur est le referred
        referral = Referral.objects.get(referred=user)

        # Récupérer le stage de l'utilisateur à partir du modèle CustomUser
        current_stage = user.stage  # Stage actuel de l'utilisateur (dans CustomUser)

        # Nombre de slots requis par stage (ajuste ces valeurs selon tes règles)
        stage_slots = {
            1: 0,  # Stage 1 : 0 slots requis
            2: 20,  # Stage 2 : 20 slots requis
            3: 40,  # Stage 3 : 40 slots requis
            4: 60,  # Stage 4 : 60 slots requis
            5: 80,  # Stage 5 : 80 slots requis
            6: 100,  # Stage 6 : 100 slots requis
            7: 120,  # Stage 7 : 120 slots requis
            8: 140,  # Stage 8 : 140 slots requis
            9: 160,  # Stage 9 : 160 slots requis
            10: 180  # Stage 10 : 180 slots requis
        }
        required_slots_for_current_stage = stage_slots.get(current_stage, 0)
        # Récupérer les slots remplis cumulés précédemment (non basé sur referral)
        new_filled_slots = required_slots_for_current_stage # Utilise les slots actuels de l'utilisateur dans CustomUser

        # Ajouter les nouveaux slots remplis
        new_total_filled_slots = new_filled_slots + filled_slots

        # Vérifier si l'utilisateur a atteint le seuil du stage suivant
        if new_total_filled_slots >= required_slots_for_current_stage:
            # Mettre à jour les slots remplis dans le referral et dans l'utilisateur
            referral.filled_slots = new_total_filled_slots
            referral.total_slots = filled_slots
            referral.save()

            user.filled_slots = new_total_filled_slots
            user.slot_partage = filled_slots
            user.save()

        else:
            # Si l'utilisateur n'a pas encore rempli suffisamment de slots pour passer au stage suivant
            referral.filled_slots = new_total_filled_slots
            referral.total_slots = filled_slots
            referral.save()

            user.filled_slots = new_total_filled_slots
            user.slot_partage = filled_slots
            user.save()

    except Referral.DoesNotExist:
        # Si aucun Referral n'existe pour l'utilisateur, en créer un et mettre à jour CustomUser
        referral = Referral.objects.create(referred=user, filled_slots=new_filled_slots)
        user.filled_slots = new_filled_slots
        user.save()


    except Referral.MultipleObjectsReturned:
        # Si plusieurs Referral existent, mettre à jour tous et synchroniser avec CustomUser
        referrals = Referral.objects.filter(referred=user)
        referrals.update(filled_slots=new_filled_slots)

        # Prendre le premier pour synchroniser avec CustomUser
        referred_user = referrals.first().referred
        referred_user.filled_slots = new_filled_slots
        referred_user.save()


def calculate_slots(display_rows, user_position):
    filled_slots = 0
    empty_slots = 0

    for row in display_rows[1:]:  # Ignorer la première ligne (utilisateur)
        for slot in row:
            if slot is not None:
                filled_slots += 1
            else:
                empty_slots += 1

    return filled_slots, empty_slots


def view_referrals(request):
    user = request.user  # Utilisateur connecté
    try:
        # Récupérer le Referral où l'utilisateur est le referred
        referral = Referral.objects.get(referred=user)
        filled_slots = referral.filled_slots  # Nombre de slots remplis de l'utilisateur
    except Referral.DoesNotExist:
        filled_slots = 0
        # Tenter de convertir le stage stocké sur l'utilisateur
    try:
        stage = int(user.stage)
    except ValueError:
        stage = 1

    # S'assurer que le stage est entre 1 et 10
    if stage < 1 or stage > 10:
        stage = 1

    # Si l'utilisateur n'a pas de Referral, on considère que filled_slots est à 0

    # Déterminer le stage en fonction des slots remplis
    if filled_slots < 20:
        stage = 1  # Si moins de 20 slots remplis, l'utilisateur est encore au stage 1
        referral_tree = generate_referral_tree()  # Arbre pour le stage 1
    else:
        referral_tree = generate_referral_tree_stage_2_to_10(stage)  # Arbre pour les stages 2 à 10

    # Extraire la structure de l'arbre (la variable rows)
    if isinstance(referral_tree, dict) and 'rows' in referral_tree:
        rows = referral_tree['rows']
    elif isinstance(referral_tree, list):
        rows = referral_tree
    else:
        return render(request, 'authentication/view_referrals.html', {
            'message': "Erreur dans la structure de l'arbre des parrainages"
        })

    # Trouver la position de l'utilisateur dans l'arbre
    user_position = None
    for row in rows:
        if user in row:
            user_position = (rows.index(row), row.index(user))
            break

    if user_position is None:
        return render(request, 'authentication/view_referrals.html', {
            'message': "Utilisateur non trouvé dans l'arbre des parrainages"
        })

    user_row, user_col = user_position

    # Préparer les lignes d'affichage (3 niveaux : utilisateur, filleuls directs, filleuls des filleuls)
    display_rows = [
        [user],           # Ligne 1 : utilisateur connecté
        [None] * 10,      # Ligne 2 : filleuls directs
        [None] * 10, # Ligne 3 : filleuls des filleuls
    ]

    # Remplir la ligne des filleuls directs
    if user_row + 1 < len(rows):
        direct_referrals_row = rows[user_row + 1]
        for i in range(min(10, len(direct_referrals_row) - user_col)):
            display_rows[1][i] = direct_referrals_row[user_col + i]

    # Remplir la ligne des filleuls des filleuls
    if user_row + 2 < len(rows):
        grandchild_referrals_row = rows[user_row + 2]
        for i in range(min(10, len(grandchild_referrals_row) - user_col)):
            display_rows[2][i] = grandchild_referrals_row[user_col + i]

    # Calcul des slots pleins et vides
    filled_slots, empty_slots = calculate_slots(display_rows, user_position)

    # Mise à jour des slots et gestion de la promotion si filled_slots atteint 20 ou plus
    promotion_occurred = update_filled_slots_and_check_promotion(user, filled_slots)

    if filled_slots >= 20:
        # Mise à jour du stage de l'utilisateur (si non déjà fait)
        update_user_stage_on_filled_slots_change(user,referral)
        user.refresh_from_db()
        create_notification(
            referral=None,
            message_for_referrer="Félicitations ! Vous avez été promu au stage suivant.",
            message_for_referred=""
        )

    # Envoi d'une notification pour chaque filleul présent dans les lignes d'affichage
    for row in display_rows[1:]:
        for slot in row:
            if slot is not None and slot != user:
                try:
                    referral_uuid = slot.referral_uuid  # Accès au referral_uuid du CustomUser
                    create_notification(
                        referral=None,
                        message_for_referrer=f"Un slot a été rempli avec {slot.email} (ID: {referral_uuid}).",
                        message_for_referred=f"Vous avez été enregistré sous {user.email} (ID parrainage: {referral_uuid})."
                    )
                except AttributeError:
                    pass

    # Calcul du nombre d'inscriptions actuelles et des inscriptions restantes
    current_registrations = Referral.objects.filter(referrer=user).count()
    remaining_registrations = 25 - current_registrations

    context = {
        'user': user,
        'rows': display_rows,
        'filled_slots': filled_slots,
        'total_slots': 20,
        'total_allowed_registrations': 25,
        'current_registrations': current_registrations,
        'remaining_registrations': remaining_registrations,
    }
    return render(request, 'authentication/view_referrals.html', context)


def promote_user_to_next_stage_if_eligible(user):
    # Dictionnaire définissant le nombre de slots nécessaires pour chaque stade
    stage_thresholds = {
        1: 20,
        2: 40,
        3: 60,
        4: 80,
        5: 100,
        6: 120,
        7: 140,
        8: 160,
        9: 180,
    }

    # Assurer que l'utilisateur ne dépasse pas le stade 10
    if user.stage < 10:
        # Obtenir le nombre de slots requis pour le stade actuel
        threshold = stage_thresholds.get(user.stage, None)

        # Si l'utilisateur a atteint ou dépassé le nombre de slots nécessaires pour son stade actuel
        if threshold and user.filled_slots >= threshold:
            # Passer au stade suivant
            user.stage += 1
            user.save()
            print(f'Débogage: {user.username} est passé au stade {user.stage} avec {user.filled_slots} slots remplis.')

def generate_referral_tree():
    num_lignes = 10
    User = get_user_model()
    rows = []

    # Création dynamique des lignes avec le nombre de cases approprié
    for i in range(num_lignes):
        if i == 0:
            num_cases = 1  # 1 case pour le parrain principal
        else:
            num_cases = 10 + (i - 1) * 9  # 10 + (i - 1) * 9 pour les lignes suivantes
        rows.append([None] * num_cases)

    # Obtenir le premier utilisateur non-admin pour la première ligne
    first_user = User.objects.exclude(is_superuser=True).order_by('date_joined').first()
    if first_user:
        rows[0][0] = first_user

    # Obtenir tous les utilisateurs parrainés, triés par date d'inscription
    referrals = Referral.objects.all().order_by('date_joined')

    def find_referrer_index(referrer):
        for row_index, row in enumerate(rows):
            if referrer in row:
                return row_index, row.index(referrer)
        return None, None

    def get_referrer(user):
        try:
            referral = Referral.objects.get(referred=user)
            return referral.referrer
        except Referral.DoesNotExist:
            return None

    # Placer chaque utilisateur dans les lignes appropriées
    for referral in referrals:
        user = referral.referred
        referrer = get_referrer(user)

        # Obtenir l'index du parrain
        if referrer:
            referrer_row_index, referrer_index = find_referrer_index(referrer)
            if referrer_row_index is None or referrer_index is None:
                continue
        else:
            referrer_row_index, referrer_index = 0, 0  # Si pas de parrain, placer à la première ligne

        placed = False
        for row_index in range(referrer_row_index + 1, len(rows)):
            segment_start = referrer_index
            segment_end = min(segment_start + 10, len(rows[row_index]))

            # Placer l'utilisateur dans les cases disponibles
            for col_index in range(segment_start, segment_end):
                if rows[row_index][col_index] is None:
                    rows[row_index][col_index] = user
                    placed = True
                    break
            if placed:
                break

        if not placed:
            print(f"No empty slot found for {user}")

    return {'rows': rows}


def generate_referral_tree_stage_2_to_10(stage):
    # Définir le nombre de lignes maximales pour chaque stade
    max_lines = {
        2: 10,
        3: 12,
        4: 14,
        5: 16,
        6: 18,
        7: 20,
        8: 22,
        9: 24,
        10: 26
    }
    stage = int(stage)
    # Nombre de lignes pour le stade donné
    num_lignes = max_lines.get(stage, 10)
    rows = []

    # Initialiser les lignes
    for i in range(num_lignes):
        if i == 0:
            num_cases = 1
        else:
            num_cases = 10 + (i - 1) * 9
        rows.append([None] * num_cases)

    # Filtrer les referrals pour le stade actuel
    total_filled_slots = 20 * (stage - 1)
    referrals_with_filled_slot = Referral.objects.filter(filled_slots__gte=total_filled_slots)


    for referral in referrals_with_filled_slot:
        user = referral.referred_user
        if user:
            place_user_in_stage_tree(rows, user)

    return rows

def place_user_in_stage_tree(rows, user):
    """
    Place un utilisateur dans l'arbre du stade en fonction de la présence du parrain.
    """
    # Trouver le parrain de l'utilisateur
    try:
        referral = Referral.objects.get(referred=user)
        sponsor = referral.referrer
    except Referral.DoesNotExist:
        sponsor = None

    if sponsor:
        # Trouver la position du parrain dans les rows
        sponsor_position = None
        for row_index, row in enumerate(rows):
            if sponsor in row:
                sponsor_position = (row_index, row.index(sponsor))
                break

        if sponsor_position:
            # Démarrer la recherche de la place vide à partir de la ligne sous le parrain
            sponsor_row_index, sponsor_col_index = sponsor_position
            start_row_index = sponsor_row_index + 1

            # Recherche d'une place vide à partir du slot directement sous le parrain
            for row_index in range(start_row_index, len(rows)):
                row = rows[row_index]

                # Calculer la position de départ pour la recherche
                start_col_index = sponsor_col_index if row_index == start_row_index else 0

                # Chercher une place vide dans un champ de 10 slots à partir de start_col_index
                for col_index in range(start_col_index, min(start_col_index + 10, len(row))):
                    if row[col_index] is None:
                        row[col_index] = user
                        return

            # Si aucune place n'est trouvée dans les lignes suivantes, chercher dans toutes les lignes restantes
            for row_index in range(start_row_index, len(rows)):
                row = rows[row_index]

                # Chercher une place vide dans un champ de 10 slots à partir de la première colonne
                for col_index in range(0, min(10, len(row))):
                    if row[col_index] is None:
                        row[col_index] = user
                        return

    # Si le parrain n'est pas trouvé ou aucune place n'est trouvée selon la logique précédente
    # Place l'utilisateur dans le premier slot vide disponible
    for row in rows:
        for col_index, slot in enumerate(row):
            if slot is None:
                row[col_index] = user
                return

def referral_tree_stage_view(request, stage):
    rows = generate_referral_tree_stage_2_to_10(stage)
    template_name = f'admin/referral_tree_stage_{stage}.html'
    return render(request, template_name, {'rows': rows})

def language_change(request):
    if request.method == 'POST':
        form = LanguageChangeForm(request.POST)
        if form.is_valid():
            language_code = form.cleaned_data['language']
            translation.activate(language_code)
            request.session[translation.LANGUAGE_SESSION_KEY] = language_code
            return redirect('authentication:user_dashboard')
    else:
        form = LanguageChangeForm()
    return render(request, 'authentication/language_change.html', {'form': form})

@login_required
def theme_change(request):
    if request.method == 'POST':
        form = ThemeChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('authentication:user_dashboard')
    else:
        form = ThemeChangeForm(instance=request.user)
    return render(request, 'authentication/theme_change.html', {'form': form})

@login_required
def security_settings(request):
    security_logs = SecurityLog.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'authentication/security_settings.html', {'security_logs': security_logs})

@login_required
def avatar_settings(request):
    if request.method == 'POST':
        form = AvatarForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('authentication:view_profile')
    else:
        form = AvatarForm(instance=request.user)
    return render(request, 'authentication/avatar_settings.html', {'form': form})

@login_required
def privacy_settings(request):
    return render(request, 'authentication/privacy_settings.html')

@login_required
def communication_preferences(request):
    if request.method == 'POST':
        form = CommunicationPreferencesForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('authentication:user_dashboard')
    else:
        form = CommunicationPreferencesForm(instance=request.user)
    return render(request, 'authentication/communication_preferences.html', {'form': form})

@login_required
def content_preferences(request):
    try:
        content_preferences = ContentPreferences.objects.get(user=request.user)
    except ContentPreferences.DoesNotExist:
        content_preferences = None

    if request.method == 'POST':
        form = ContentPreferencesForm(request.POST, instance=content_preferences)
        if form.is_valid():
            form.instance.user = request.user
            form.save()
            return redirect('authentication:user_dashboard')
    else:
        form = ContentPreferencesForm(instance=content_preferences)
    return render(request, 'authentication/content_preferences.html', {'form': form})

@login_required
def permissions_management(request):
    return render(request, 'authentication/permissions_management.html')

@login_required
def activity_history(request):
    return render(request, 'authentication/activity_history.html')

@login_required
def integrations_settings(request):
    return render(request, 'authentication/integrations_settings.html')

@login_required
def payment_billing_settings(request):
    return render(request, 'authentication/payment_billing_settings.html')

@login_required
def user_settings(request):
    return render(request, 'authentication/user_settings.html')

@login_required
def view_wallet(request):
    user = request.user
    retraits = Retrait.objects.filter(user=user).order_by('-date')  # Plus récents en premier

    # Récupérer le portefeuille de l'utilisateur
    try:
        wallet = user.wallet  # Assurez-vous que chaque utilisateur a un wallet associé
    except Wallet.DoesNotExist:
        wallet = None  # Gérer le cas où le portefeuille n'existe pas

    conversion_rate = 100  # Exemple : 1 point = 100 FCFA
    local_conversion_rate = 0.01  # Exemple : taux de conversion pour d'autres devises (ex: 1 FCFA = 0.01 USD)
    country_currency = 'FCFA'  # Monnaie par défaut

    context = {
        'wallet': wallet,
        'conversion_rate': conversion_rate,
        'local_conversion_rate': local_conversion_rate,
        'country_currency': country_currency,
        'retraits': retraits,
    }

    return render(request, 'authentication/view_wallet.html', context)

@login_required
def logout_user(request):
    logout(request)
    return redirect('authentication:user_login')

def is_simple_user(user):
    return not user.is_superuser

def referral_statistics(request):
    user = request.user

    total_referrals = Referral.objects.filter(referrer=user).count()
    successful_referrals = Referral.objects.filter(referrer=user, is_confirmed=True).count()
    registered_users = Referral.objects.filter(referrer=user, referred_user__isnull=False, is_confirmed=False).count()

    context = {
        'total_referrals': total_referrals,
        'successful_referrals': successful_referrals,
        'registered_users': registered_users,
    }
    return render(request, 'authentication/referral_statistics.html', context)
@login_required
def rewards(request):
    user = request.user
    wallet, _ = Wallet.objects.get_or_create(user=user)
    # Obtenir les stades et les slots remplis
    stage = user.stage
    stage_names = {
        1: "MINIME",
        2: "SUPER MINIME",
        3: "CADET",
        4: "SUPER CADET",
        5: "JUNIOR",
        6: "SENIOR",
        7: "MAJOR",
        8: "SAGE",
        9: "CAPORAL",
        10: "GENERAL",
    }
    # Créer une liste de stages avec leur nom et statut
    stages_with_status = []
    for i in range(1, 11):  # Il y a 10 stages
        stage_name = stage_names.get(i, "Inconnu")  # On récupère le nom du stage
        if i == stage:
            status = "En cours"
        elif i < stage:
            status = "Atteint"
        else:
            status = "Non atteint"

        stages_with_status.append({
            'name': stage_name,  # Le nom du stage
            'status': status
        })

    # Récupérer les transactions existantes pour l'utilisateur
    transactions = Transaction.objects.filter(user=user)
    # Préparer le contexte pour le rendu
    context = {
        'stages_with_status': stages_with_status,
        'transactions': transactions,
    }

    messages.success(request, "Les récompenses ont été mises à jour avec succès.")
    return render(request, 'authentication/rewards.html', context)


def referral_codes(request):
    # Récupérer l'utilisateur connecté
    user = request.user

    # Récupérer les parrainages de l'utilisateur actuel
    user_referrals = Referral.objects.filter(referrer=user)

    # Extraire les emails des filleuls
    referred_username = [referral.referred.username for referral in user_referrals]

    # Logique pour la page des codes de parrainage
    context = {
        'referred_username': referred_username,
    }

    return render(request, 'authentication/referral_codes.html', context)

def transaction_history(request):
    # Logique pour l'historique des transactions
    return render(request, 'authentication/transaction_history.html')
def trends_and_charts(request):
    # Logique pour les tendances et graphiques
    return render(request, 'authentication/trends_and_charts.html')


def notifications(request):
    if not request.user.is_authenticated:
        # Redirige l'utilisateur vers la page de connexion si non authentifié
        return redirect('authentication:user_login')  # ou ajuster selon votre configuration

    # Récupère les notifications pour l'utilisateur connecté, triées par date décroissante
    notifications = Notification.objects.filter(user=request.user, is_deleted=False).order_by('-created_at')

    # Rendu du template avec les notifications dans le contexte
    return render(request, 'authentication/notifications.html', {'notifications': notifications})


def create_notification(referral=None, message_for_referrer="", message_for_referred=""):
    """
    Crée des notifications pour le parrain (referrer) et le filleul (referred), si des messages sont fournis.
    """
    # Notification pour le parrain (referrer)
    if referral and referral.referrer and message_for_referrer:
        Notification.objects.create(user=referral.referrer, message=message_for_referrer)

    # Notification pour le filleul (referred)
    if referral and referral.referred and message_for_referred:
        Notification.objects.create(user=referral.referred, message=message_for_referred)

def get_user_notifications(user):
    return Notification.objects.filter(user=user).order_by('-created_at')


def mark_as_read(request, notification_uuid):
    # Récupère la notification par son UUID et l'utilisateur connecté
    notification = get_object_or_404(Notification, uuid=notification_uuid, user=request.user)

    # Marque la notification comme lue
    notification.is_read = True
    notification.save()

    # Redirige vers la page des notifications
    messages.success(request, "Notification marquée comme lue.")
    return redirect('authentication:notifications')


def delete_notification(request, notification_uuid):
    # Récupère la notification par son UUID et l'utilisateur connecté
    notification = get_object_or_404(Notification, uuid=notification_uuid, user=request.user)

    # Met à jour l'état de la notification en supprimée (soft delete)
    notification.is_deleted = True  # Si vous utilisez un champ `is_deleted`
    notification.save()

    # Ou supprime définitivement si nécessaire
    # notification.delete()

    # Redirige vers la page des notifications
    messages.success(request, "Notification supprimée.")
    return redirect('authentication:notifications')
@login_required
def support(request):
    if request.method == 'POST':
        form = SupportForm(request.POST)
        if form.is_valid():
            support_request = form.save(commit=False)
            support_request.user = request.user  # Associer la requête à l'utilisateur connecté
            support_request.save()
            messages.success(request, "Votre demande de support a été envoyée avec succès !")
            return redirect('authentication:support')
    else:
        form = SupportForm()

    context = {'form': form}
    return render(request, 'authentication/support.html', context)
def generate_signed_referrer(user):
    signer = Signer()
    return signer.sign(user.username)
@login_required
def view_profile(request):
    user = request.user  # L'utilisateur connecté
    # Récupérer le stage de l'utilisateur (assurer qu'il existe)
    stage = user.stage
    historique_activites = ["Activité 1", "Activité 2", "Activité 3"]
    recompenses = ["Badge 1", "Récompense 2"]
    # Récupère le stage actuel de l'utilisateur

    # Vérifie si une image a été envoyée via le formulaire
    if request.method == "POST" and request.FILES.get('profile_picture'):
        profile_picture = request.FILES['profile_picture']

        # Génère un nom de fichier unique pour éviter les conflits
        file_name = f"{user.username}_{profile_picture.name}"

        # Sauvegarde du fichier dans /media/profile_pictures/
        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'profile_pictures'))
        filename = fs.save(file_name, profile_picture)

        # Mise à jour du profil utilisateur
        user.profile_picture.name = f'profile_pictures/{filename}'
        user.save()

        file_url = user.profile_picture.url  # ✅ Utilisation correcte de l'URL

        return JsonResponse({"status": "success", "file_url": file_url})

    # Récupération de l'image actuelle de l'utilisateur
    profile_picture_url = (
        user.profile_picture.url if user.profile_picture else "/static/images/default-avatar.png"
    )

    context = {
        'user': user,
        'profile_picture_url': profile_picture_url,
        'historique_activites': historique_activites,
        'recompenses': recompenses,
        'stage': stage,# Passer l'objet stage au template
    }

    return render(request, 'authentication/view_profile.html', context)


def determine_current_stage(user):
    """Détermine le stade actuel de l'utilisateur en fonction de la logique définie."""
    # Implémentez ici la logique pour déterminer le stade actuel de l'utilisateur
    # Par exemple, vous pouvez récupérer le stade de l'utilisateur à partir du modèle
    return user.stage

@login_required
def setting(request):
    user = request.user

    if request.method == 'POST':
        # Récupérer les valeurs du formulaire
        username = request.POST.get('username')
        email = request.POST.get('email')
        contact = request.POST.get('contact')
        nationalite = request.POST.get('nationalite')
        sexe = request.POST.get('sexe')
        date_of_birth = request.POST.get('date_of_birth')
        ville = request.POST.get('ville')
        quartier = request.POST.get('quartier')
        password = request.POST.get('password')

        # Mettre à jour les informations de l'utilisateur
        user.username = username
        user.email = email
        user.contact = contact
        user.nationalite = nationalite
        user.sexe = sexe
        user.date_of_birth = date_of_birth
        user.ville = ville
        user.quartier = quartier

        # Vérifier si l'utilisateur a entré un nouveau mot de passe
        if password:
            user.password = make_password(password)
            update_session_auth_hash(request, user)  # Garde la session active après le changement de mot de passe

        # Sauvegarde de l'utilisateur
        user.save()
        messages.success(request, "Vos paramètres ont été mis à jour avec succès !")
        return redirect('authentication:settings')

    context = {
        'user': user
    }
    return render(request, 'authentication/settings.html', context)


def get_unread_messages_count(request):
    # Récupérer le nombre de notifications non lues pour l'utilisateur actuel
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'unread_count': unread_count})

def password_reset_request(request):
    if request.method == "POST":
        username = request.POST.get("username")
        try:
            user = CustomUser.objects.get(username=username)
            subject = "Demande de réinitialisation du mot de passe"
            email_template_name = "authentication/password_reset_email.html"
            context = {
                "email": user.email,
                "username": user.username,
                "domain": request.get_host(),
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "token": default_token_generator.make_token(user),
            }
            email_content = render_to_string(email_template_name, context)
            send_mail(subject, email_content, settings.DEFAULT_FROM_EMAIL, [user.email])
            messages.success(request, "Un email de réinitialisation a été envoyé à l'adresse associée à ce nom d'utilisateur.")
            return redirect("authentication:password_reset_done")
        except CustomUser.DoesNotExist:
            messages.error(request, "Le nom d'utilisateur n'est pas reconnu.")

    return render(request, "authentication/password_reset_form.html")
# Vue pour afficher la confirmation de l'envoi
def password_reset_done(request):
    return render(request, "authentication/password_reset_done.html")


# Vue pour réinitialiser le mot de passe
def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = get_object_or_404(CustomUser, pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if new_password != confirm_password:
                messages.error(request, "Les mots de passe ne correspondent pas.")
                return render(request, 'authentication/password_reset_confirm.html', {'valid_token': True, 'uidb64': uidb64, 'token': token})

            # Mettre à jour le mot de passe
            user.password = make_password(new_password)
            user.save()
            messages.success(request, "Votre mot de passe a été mis à jour avec succès.")
            return redirect('authentication:user_login')  # Redirigez vers la page de connexion

        return render(request, 'authentication/password_reset_confirm.html', {'valid_token': True, 'uidb64': uidb64, 'token': token})
    else:
        messages.error(request, "Le lien de réinitialisation du mot de passe est invalide.")
        return redirect('authentication:password_reset_request')
def donateurs_list(request):
    """Vue pour afficher la liste des Donateurs."""
    donateurs = CustomUser.objects.filter(is_donateur= True)  # Filtrer les utilisateurs ayant le rôle 'DON'
    projets_necessitant_donateurs = Projet.objects.filter(montant_recolte__lt=F('montant_objectif'))  # Projets nécessitant des dons
    return render(request, 'authentication/projet_don.html', {'donateurs': donateurs, 'projets': projets_necessitant_donateurs})

def create_checkout_session_projet(request, projet_id):
    """
    Crée une session de paiement pour le projet spécifié, en fonction du mode de paiement sélectionné.
    """
    user= request.user
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'card')
        amount = request.POST.get('amount')

        # Validation du montant (doit être un nombre et >= 10)
        if not amount or not amount.isdigit() or int(amount) < 10:
            return redirect(reverse('authentication:error') + '?error=Montant invalide ou trop faible')

        amount = int(amount)
        # Si Stripe est utilisé, convertir en centimes
        stripe_amount = amount * 100 if payment_method in ['card', 'google_pay', 'apple_pay'] else amount
        # Détermination des méthodes de paiement autorisées
        if payment_method == 'card':
            payment_method_types = ['card']
        elif payment_method == 'google_pay':
            payment_method_types = ['card', 'google_pay']
        elif payment_method == 'apple_pay':
            payment_method_types = ['card', 'apple_pay']
        elif payment_method == 'tmoney' or payment_method == 'flooz':
            # Si le mode de paiement est TMoney ou Flooz, on redirige vers CinetPay
            return create_cinetpay_payment(amount, projet_id, payment_method,user)
        elif payment_method == 'wallet':
            # Si l'utilisateur choisit de payer via son portefeuille, on effectue la vérification du solde
            return handle_wallet_payment(request, amount, projet_id)
        else:
            payment_method_types = ['card']

        # Vérification du montant pour Stripe (>= 1000 FCFA)
        if amount < 10:
            return redirect(reverse('authentication:error') + '?error=Montant minimum pour Stripe est de 1000 FCFA')

        try:
            # Création d'une session de paiement Stripe
            session = stripe.checkout.Session.create(
                payment_method_types=payment_method_types,
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': 'Projet ID ' + str(projet_id),
                        },
                        'unit_amount': stripe_amount,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=request.build_absolute_uri(
                    reverse('authentication:success_projet')
                ) + f'?session_id={{CHECKOUT_SESSION_ID}}&type=confirmation&payment_method={payment_method}&projet_id={projet_id}',
                cancel_url=request.build_absolute_uri(reverse('authentication:cancel')),
                metadata={'project_id': projet_id},  # Ajout des métadonnées
            )

            return redirect(session.url, code=303)
        except Exception as e:
            return redirect(reverse('authentication:error') + f'?payment_method=Stripe&error={str(e)}')

    return render(request, 'authentication/payment_projet.html', {'projet_id': projet_id})


def create_cinetpay_payment(amount, projet_id, payment_method, user):
    transaction_id = str(uuid.uuid4())  # ID unique

    channels_map = {
        "tmoney": "MOBILE_MONEY",
        "flooz": "MOBILE_MONEY",
        "mobile_money": "MOBILE_MONEY"
    }

    payload = {
        "apikey": settings.CINETPAY_API_KEY,
        "site_id": settings.CINETPAY_SITE_ID,
        "transaction_id": transaction_id,
        "amount": amount,
        "currency": "XOF",
        "description": f"Paiement projet ID {projet_id}",
        "return_url": "http://127.0.0.1:8000/authentication/payment_success_cinet/",
        "notify_url": "http://127.0.0.1:8000/authentication/payment-notify/",
        "channels": channels_map.get(payment_method, "MOBILE_MONEY"),
        "method": payment_method,
        "customer_name": user.username,
    }

    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(settings.CINETPAY_BASE_URL, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == "201":
                return redirect(data["data"]["payment_url"])
            else:
                return redirect(
                    reverse('authentication:cancel') + f"?payment_method={payment_method}&error={data.get('message')}"
                )
        else:
            return redirect(
                reverse('authentication:cancel') + f"?payment_method={payment_method}&error=Erreur communication CinetPay"
            )
    except Exception as e:
        return redirect(
            reverse('authentication:cancel') + f"?payment_method={payment_method}&error=Exception: {str(e)}"
        )

def handle_wallet_payment(request, amount, projet_id):
    """
    Gère le paiement via le portefeuille (wallet) de l'utilisateur.
    """
    try:
        # Récupération du portefeuille de l'utilisateur
        user_wallet = Wallet.objects.get(user=request.user)

        # Vérification si le solde du portefeuille est suffisant
        if user_wallet.balance < amount:
            return redirect(reverse('authentication:error') + '?payment_method=wallet&error=Solde insuffisant')

        # Déduction du montant du portefeuille de l'utilisateur
        user_wallet.balance -= amount
        user_wallet.save()

        # Création de la donation
        don = Donation.objects.create(
            user=request.user,
            projet_id=projet_id,
            montant=amount,
        )

        # Mise à jour du montant récolté pour le projet
        projet = Projet.objects.get(id=projet_id)  # Récupère le projet
        projet.montant_recolte += don.montant
        projet.save()

        # Gestion du parrainage
        referrer = request.user.referrer
        if referrer:
            commission_fcfa = amount * Decimal('0.10')  # 10% de commission pour le parrain

            wallet, _ = Wallet.objects.get_or_create(user=referrer)
            wallet.balance += commission_fcfa
            wallet.save()

            # Enregistrement de la commission de parrainage
            Transaction.objects.create(
                user=referrer,
                amount=commission_fcfa,
                reason=f"Commission de parrainage sur le don au projet {projet.titre}",
                is_successful=True
            )

            # Notification pour le parrain
            message_for_referrer = (
                f"Bonjour {referrer.username},\n"
                f"Vous avez reçu une commission de {commission_fcfa} FCFA\n"
                f"pour le don effectué par votre filleul {request.user.username} sur le projet {projet.titre}.\n"
                f"Merci pour votre engagement !"
            )
            send_sms(referrer.contact, message_for_referrer)

        # Confirmation pour l'utilisateur donateur
        message_for_user = (
            f"Bonjour {request.user.username},\n"
            f"Vous avez effectué un don de {amount} FCFA\n"
            f"pour le projet {projet.titre}.\n"
            f"Merci pour votre générosité !"
        )
        send_sms(request.user.contact, message_for_user)

        # Préparation des détails de paiement pour la page de succès
        payment_details = {
            'payment_method': 'Wallet',
            'amount': amount,
            'currency': 'FCFA',
            'transaction_id': str(don.id),  # ID de la donation comme identifiant de transaction
            'email': request.user.email,
            'username': request.user.username,
            'status': 'Success',  # Le paiement a été effectué avec succès
            'projet': projet,
        }

        # Enregistrement de la transaction dans l'historique (optionnel)
        Transaction.objects.create(
            user=referrer,
            amount=commission_fcfa,
            reason=f"Commission de parrainage sur le don au projet {projet.titre}",
            is_successful=True
        )

        # Rendu de la page de succès avec le contexte des détails du paiement
        return render(request, 'authentication/success_projet.html', {'payment_details': payment_details})

    except ObjectDoesNotExist:
        return redirect(reverse('authentication:error') + '?payment_method=wallet&error=ProjetInexistant')


def success_projet(request):
    session_id = request.GET.get('session_id')
    projet_id = request.GET.get('projet_id')
    user = request.user

    if not session_id:
        messages.error(request, "Session de paiement introuvable.")
        return redirect('ecommerce:payment_projet')

    try:
        # Récupération de la session Stripe
        session = stripe.checkout.Session.retrieve(session_id)

        if session.payment_status == 'paid':
            if not user.is_authenticated:
                messages.error(request, "Utilisateur non authentifié.")
                return redirect('authentication:user_login')

            # Récupération du projet
            projet_id = session.metadata.get('project_id')
            projet = get_object_or_404(Projet, id=projet_id)

            # Récupération du mode de paiement (Stripe, Cynet, Wallet...)
            payment_method = session.metadata.get('payment_method', 'stripe')

            # Récupération du montant
            montant_don = Decimal(session.amount_total) / Decimal('100')  # Stripe retourne en cents

            # Conversion uniquement si Stripe
            if payment_method == 'stripe':
                montant_don_fcfa = montant_don * Decimal('600')  # Ex. 1 USD = 600 FCFA
            else:
                montant_don_fcfa = montant_don  # Déjà en FCFA pour Cynet ou Wallet

            # Enregistrement de la donation
            don = Donation.objects.create(
                user=user,
                projet=projet,
                montant=montant_don_fcfa,
            )

            # Mise à jour du montant récolté
            projet.montant_recolte += don.montant
            projet.save()

            # Gestion du parrainage
            referrer = user.referrer
            if referrer:
                commission_fcfa = montant_don_fcfa * Decimal('0.10')  # 10%

                wallet, _ = Wallet.objects.get_or_create(user=referrer)
                wallet.balance += commission_fcfa
                wallet.save()

                Transaction.objects.create(
                    user=referrer,
                    amount=commission_fcfa,
                    reason=f"Commission de parrainage sur le don au projet {projet.titre}",
                    is_successful=True
                )

                message_for_referrer = (
                    f"Bonjour {referrer.username},\n"
                    f"Vous avez reçu une commission de {commission_fcfa} FCFA\n"
                    f"pour le don effectué par votre filleul {user.username} sur le projet {projet.titre}.\n"
                    f"Merci pour votre engagement !"
                )
                send_sms(referrer.contact, message_for_referrer)

            # Confirmation pour le donateur
            message_for_user = (
                f"Bonjour {user.username},\n"
                f"Vous avez effectué un don de {montant_don_fcfa} FCFA\n"
                f"pour le projet {projet.titre}.\n"
                f"Merci pour votre générosité !"
            )
            send_sms(user.contact, message_for_user)

            # Préparation des infos à afficher
            payment_details = {
                'payment_method': payment_method.capitalize(),
                'amount': montant_don_fcfa,
                'currency': 'FCFA',
                'transaction_id': session.payment_intent,
                'email': user.email,
                'username': user.username,
                'status': session.payment_status,
            }

            return render(request, 'authentication/success_projet.html', {'payment_details': payment_details, 'projet': projet})

    except stripe.error.StripeError as e:
        messages.error(request, f"Erreur lors du paiement : {str(e)}")
        return redirect('authentication:error')


@csrf_exempt
def retrait_view(request):
    user = request.user

    if request.method == 'POST':
        montant = int(request.POST.get("montant"))
        numero = request.POST.get("numero")
        operateur = request.POST.get("operateur")

        wallet = Wallet.objects.get(user=user)

        # Vérifier le montant minimum selon l'opérateur
        if operateur in ['tmoney', 'flooz'] and montant < 2000:
            messages.error(request, "Montant minimum de retrait : 2000 FCFA pour TMoney/Flooz.")
            return redirect('authentication:retrait')
        if operateur == 'visa' and montant < 6000:
            messages.error(request, "Montant minimum de retrait : 6000 FCFA pour Visa.")
            return redirect('authentication:retrait')

        # Calcul du solde disponible (en tenant compte des retraits en attente)
        retraits_en_attente = Retrait.objects.filter(user=user, statut='EN_ATTENTE').aggregate(total=Sum('montant'))['total'] or 0
        solde_disponible = wallet.balance - retraits_en_attente

        if montant > solde_disponible:
            messages.error(request, "Solde insuffisant (en tenant compte de vos demandes de retrait en attente).")
            return redirect('authentication:retrait')

        # Créer la demande de retrait (elle sera traitée plus tard)
        Retrait.objects.create(
            user=user,
            montant=montant,
            numero=numero,
            operateur=operateur,
            statut='EN_ATTENTE'
        )

        messages.success(request, "Votre demande de retrait a été enregistrée avec succès.")
        return redirect('authentication:view_wallet')

    wallet = Wallet.objects.get(user=user)
    return render(request, 'authentication/retrait.html', {'wallet': wallet})
@csrf_exempt
def cinetpay_webhook(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        tx_id = data.get("transaction_id")
        statut = data.get("status")

        retrait = Retrait.objects.filter(transaction_id=tx_id).first()
        if retrait:
            if statut == "SUCCES":
                retrait.statut = "SUCCES"
            elif statut == "ECHEC":
                retrait.statut = "ECHEC"
                Wallet.objects.filter(user=retrait.user).update(balance=F("balance") + retrait.montant)
            retrait.save()
        return JsonResponse({"status": "ok"})
