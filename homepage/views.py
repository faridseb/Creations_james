from django.shortcuts import render,redirect
from blog.models import Article  # Importer le modèle Article de l'application blog
from authentication.models import CustomUser, Transaction as AuthTransaction
from ecommerce.models import EcommerceUser
from django.db.models import Sum
from django.http import HttpResponseForbidden
import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from django.db.models import F, Q
from association.models import AssociationUser
from parti.models import PartiUser
from django.contrib.auth.decorators import login_required
from .models import DemandeSupport, OeuvreSocialUser, Projet, Transaction as HomeTransaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from .forms import DemandeSupportForm
from django.contrib import messages
from django.contrib.auth import authenticate, login
from .forms import DemandeSupportForm,UserRegistrationForm,LoginForm

def search(request):
    query = request.GET.get('q')
    results = Article.objects.filter(title__icontains=query) | Article.objects.filter(content__icontains=query)
    return render(request, 'homepage/search.html', {'query': query, 'results': results})

def home(request):
    total_customuser = CustomUser.objects.filter(is_superuser=False).count()  # Nombre d'utilisateurs dans 'authentication'

    # Total des transactions pour l'application 'authentication'
    total_customuser_transactions = AuthTransaction.objects.count()
    # Total des utilisateurs pour l'application 'parti' (PartiUser)
    total_partiuser = PartiUser.objects.count()  # Nombre d'utilisateurs dans 'parti'
    # Total des utilisateurs pour l'application 'ecommerce' (EcommerceUser)
    total_ecommerceuser = EcommerceUser.objects.count()
    # Total des utilisateurs pour l'application 'association' (AssociationUser)
    total_associationuser = AssociationUser.objects.filter(role='association').count()
    donateurs_count = OeuvreSocialUser.objects.filter(role='DON').count()
    sponsors_count = OeuvreSocialUser.objects.filter(role='SPON').count()
    bienfaiteurs_count = OeuvreSocialUser.objects.filter(role='BIEN').count()
    torpilleurs_count = OeuvreSocialUser.objects.filter(role='TOR').count()


    total_actions = (donateurs_count + sponsors_count + bienfaiteurs_count + torpilleurs_count)

    # Calcul du total des utilisateurs et des transactions pour l'ensemble du projet
    total_global_users = (total_customuser + total_partiuser + total_associationuser + total_ecommerceuser
                          + total_customuser_transactions + total_actions )

    context = {
        'total_global_users': total_global_users,
        'titre': 'Bienvenue sur mon site',
        'message': 'Ceci est une page dynamique générée avec Django.',
        'carousel_images': [
            {'src': 'https://via.placeholder.com/800x400', 'alt': 'Slide 1'},
            {'src': 'https://via.placeholder.com/800x400', 'alt': 'Slide 2'},
            {'src': 'https://via.placeholder.com/800x400', 'alt': 'Slide 3'},
        ],
        'social_links': [
            {'url': '#', 'icon': 'fab fa-facebook'},
            {'url': '#', 'icon': 'fab fa-whatsapp'},
            {'url': '#', 'icon': 'fab fa-twitter'},
        ],
        'contact_info': {
            'address': '123 Rue du Lorem Ipsum, Lorem City',
            'phone': '+1234567890',
            'email': 'contact@example.com',
        }

    }
    return render(request, 'homepage/home.html', context)

def index(request):
    return render(request, 'homepage/index.html')

def bibliographie(request):
    return render(request, 'homepage/bibliographie.html')

def formation(request):
    return render(request, 'homepage/formation.html')
def sante(request):
    return render(request, 'homepage/sante.html')

def oeuvreSocial(request):
    # Nombre total d'utilisateurs dans différentes applications
    total_customuser = CustomUser.objects.filter(is_superuser=False).count()  # Nombre d'utilisateurs dans 'authentication'
    total_customuser_transactions = AuthTransaction.objects.count()  # Total des transactions pour 'authentication'
    total_partiuser = PartiUser.objects.count()  # Nombre d'utilisateurs dans 'parti'
    total_ecommerceuser = EcommerceUser.objects.count()  # Nombre d'utilisateurs dans 'ecommerce'
    total_associationuser = AssociationUser.objects.filter(role='association').count()  # Nombre d'associations

    # Nombre d'utilisateurs dans les catégories sociales
    donateurs_count = CustomUser.objects.filter(is_donateur=True).count()
    sponsors_count = OeuvreSocialUser.objects.filter(role__icontains='SPON').count()
    bienfaiteurs_count = OeuvreSocialUser.objects.filter(role__icontains='BIEN').count()
    torpilleurs_count = OeuvreSocialUser.objects.filter(role__icontains='TOR').count()

    # Total des actions sociales
    total_actions = (donateurs_count + sponsors_count + bienfaiteurs_count + torpilleurs_count)
    # Calcul du total des utilisateurs et des transactions pour l'ensemble du projet
    total_global_users = (
            total_customuser +
            total_partiuser +
            total_associationuser +
            total_ecommerceuser +
            total_customuser_transactions +
            total_actions
    )
    if request.method == 'POST':
        form = DemandeSupportForm(request.POST)
        if form.is_valid():
            # Vous pouvez enregistrer la demande ou envoyer un email ici
            form.save()  # Exemple d'enregistrement de la demande (assurez-vous d'avoir un modèle pour ça)
            message = "Votre demande de support a été soumise avec succès."
        else:
            message = "Il y a une erreur dans votre soumission."
    else:
        form = DemandeSupportForm()

    context = {
        'total_global_users': total_global_users,
        'donateurs_count': donateurs_count,
        'sponsors_count': sponsors_count,
        'bienfaiteurs_count': bienfaiteurs_count,
        'torpilleurs_count': torpilleurs_count,
        'form': form,  # Inclure le formulaire dans le contexte
        'message': message if 'message' in locals() else None,  # Afficher un message si présent
    }

    return render(request, 'homepage/oeuvreSocial.html', context)
@login_required
def make_donation(request, projet_id):
    projet = Projet.objects.get(id=projet_id)

    if request.method == 'POST':
        amount = request.POST.get('amount')
        transaction_type = 'DON'
        description = request.POST.get('description', '')

        try:
            # Créer une nouvelle transaction pour ce projet
            transaction = HomeTransaction.objects.create(
                user=request.user,
                transaction_type=transaction_type,
                amount=amount,
                description=description,
                projet=projet
            )

            # Mettre à jour le montant récolté du projet
            projet.montant_recolte += float(amount)
            projet.save()

            messages.success(request, f"Votre don de {amount} CFA a été enregistré pour le projet '{projet.titre}'.")
            return redirect('projet_detail', projet_id=projet.id)  # Rediriger vers la page du projet

        except Exception as e:
            messages.error(request, "Une erreur est survenue lors de l'enregistrement de votre don.")
            return redirect('make_donation', projet_id=projet.id)

    return render(request, 'make_donation.html', {'projet': projet})
def projet_detail(request, projet_id):
    projet = Projet.objects.get(id=projet_id)
    return render(request, 'projet_detail.html', {'projet': projet})

def educationEconomie(request):
    return render(request, 'homepage/educationEconomie.html')

def artisEntrep(request):
    return render(request, 'homepage/artisEntrep.html')
def connexion(request):
    # Nombre total d'utilisateurs dans différentes applications
    total_customuser = CustomUser.objects.filter(
        is_superuser=False).count()  # Nombre d'utilisateurs dans 'authentication'
    total_customuser_transactions = AuthTransaction.objects.count()  # Total des transactions pour 'authentication'
    total_partiuser = PartiUser.objects.count()  # Nombre d'utilisateurs dans 'parti'
    total_ecommerceuser = EcommerceUser.objects.count()  # Nombre d'utilisateurs dans 'ecommerce'
    total_associationuser = AssociationUser.objects.filter(role='association').count()  # Nombre d'associations

    # Nombre d'utilisateurs dans les catégories sociales
    donateurs_count = OeuvreSocialUser.objects.filter(role='DON').count()
    sponsors_count = OeuvreSocialUser.objects.filter(role='SPON').count()
    bienfaiteurs_count = OeuvreSocialUser.objects.filter(role='BIEN').count()
    torpilleurs_count = OeuvreSocialUser.objects.filter(role='TOR').count()

    # Total des actions sociales
    total_actions = (donateurs_count + sponsors_count + bienfaiteurs_count + torpilleurs_count)
    # Calcul du total des utilisateurs et des transactions pour l'ensemble du projet
    total_global_users = (
            total_customuser +
            total_partiuser +
            total_associationuser +
            total_ecommerceuser +
            total_customuser_transactions +
            total_actions
    )
    context = {
        'total_global_users': total_global_users,

    }
    return render(request, 'homepage/login.html',context)
def adherer(request):
    return render(request, 'homepage/adherer.html')

def politique(request):
    return render(request, 'homepage/politique.html')
    
def leadershipMF(request):
    return render(request, 'homepage/leadershipMF.html')

def liste_formations(request):
    formations_semaine = []
    formations_mois = []
    formations_annee = []

    # Filtrer les formations par semaine
    semaine = request.GET.get('semaine')
    if semaine:
        formations_semaine = Formation.objects.filter(semaine=semaine)

    # Filtrer les formations par mois
    mois = request.GET.get('mois')
    if mois:
        formations_mois = Formation.objects.filter(mois=mois)

    # Filtrer les formations par année
    annee = request.GET.get('annee')
    if annee:
        formations_annee = Formation.objects.filter(annee=annee)

    return render(request, 'homepage/formation.html', {'formations_semaine': formations_semaine,
                                                'formations_mois': formations_mois,
                                                'formations_annee': formations_annee})

@login_required
def transaction_history(request):
    transactions = HomeTransaction.objects.filter(user=request.user).order_by('-date')
    return render(request, 'homepage/transaction_history.html', {'transactions': transactions})

def donateurs_list(request):
    """Vue pour afficher la liste des Donateurs."""
    donateurs = CustomUser.objects.filter(is_donateur=True)  # Filtrer les utilisateurs ayant le rôle 'DON'
    projets_necessitant_donateurs = Projet.objects.filter(montant_recolte__lt=F('montant_objectif'))  # Projets nécessitant des dons
    return render(request, 'homepage/donateurs_list.html', {'donateurs': donateurs, 'projets': projets_necessitant_donateurs})
def sponsors_list(request):
    """Vue pour afficher la liste des Sponsors."""
    sponsors = OeuvreSocialUser.objects.filter(role__icontains='SPON')  # Filtrer les utilisateurs ayant le rôle 'SPON'
    projets_necessitant_sponsors = Projet.objects.filter(montant_recolte__lt=F('montant_objectif'))  # Projets nécessitant des sponsors
    return render(request, 'homepage/sponsors_list.html', {'sponsors': sponsors, 'projets': projets_necessitant_sponsors})
def bienfaiteurs_list(request):
    """Vue pour afficher la liste des Bienfaiteurs."""
    bienfaiteurs = OeuvreSocialUser.objects.filter(role__icontains='BIEN')  # Filtrer les utilisateurs ayant le rôle 'BIEN'
    projets_necessitant_bienfaiteurs = Projet.objects.filter(montant_recolte__lt=F('montant_objectif'))  # Projets nécessitant des bienfaiteurs
    return render(request, 'homepage/bienfaiteurs_list.html', {'bienfaiteurs': bienfaiteurs, 'projets': projets_necessitant_bienfaiteurs})
def torpilleurs_list(request):
    """Vue pour afficher la liste des Torpilleurs."""
    torpilleurs = OeuvreSocialUser.objects.filter(role__icontains='TOR')  # Filtrer les utilisateurs ayant le rôle 'TOR'
    return render(request, 'homepage/torpilleurs_list.html', {'torpilleurs': torpilleurs})
def whatsapp_redirect(request):
    numero = settings.WHATSAPP_NUMBER
    return redirect(f"https://wa.me/{numero}")
# Vue pour afficher et soumettre des demandes de support
def user_login(request):
    form = LoginForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]
        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            # Vérification de la session après connexion
            print("Utilisateur authentifié :", request.user)
            print("Session ID :", request.session.session_key)
            return redirect("homepage:user_dashboard")  # Redirection vers le dashboard
        else:
            messages.error(request, "Email ou mot de passe incorrect.")

    return render(request, "homepage/connection.html", {"form": form})


def user_register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)  # Créez une instance du formulaire avec les données POST
        if form.is_valid():  # Validez le formulaire
            # Si le formulaire est valide, créez l'utilisateur
            form.save()
            messages.success(request, "Compte créé avec succès ! Connectez-vous maintenant.")
            return redirect("homepage:connection")  # Rediriger vers la page de connexion
        else:
            # Si le formulaire n'est pas valide, affichez les erreurs
            messages.error(request, "Veuillez vérifier les erreurs du formulaire.")
    else:
        form = UserRegistrationForm()  # Créez un formulaire vide pour un GET

    return render(request, "homepage/inscription.html", {"form": form})  # Passez le formulaire au template
def user_logout(request):
    logout(request)
    return redirect("homepage/connection")


def user_dashboard(request):

    print("Utilisateur dans le dashboard :", request.user)
    user = request.user  # L'utilisateur connecté
    print("Utilisateur dans le dashboard :", user)
    roles = request.session.get("user_roles", [])  # Récupérer les rôles depuis la session

    print("Roles de l'utilisateur :", roles)  # Debug

    # Initialisation des projets concernés et disponibles
    projets_concernes = Projet.objects.none()
    projets_disponibles = Projet.objects.all()
    actions_possibles = []

    # Vérifie chaque rôle et ajoute les projets correspondants
    if "DON" in roles:
        projets_concernes |= Projet.objects.filter(donateurs=user)
        projets_disponibles = projets_disponibles.exclude(donateurs=user)
        actions_possibles.append("Faire un don")

    if "SPON" in roles:
        projets_concernes |= Projet.objects.filter(sponsors=user)
        projets_disponibles = projets_disponibles.exclude(sponsors=user)
        actions_possibles.append("Sponsoriser un projet")

    if "BIEN" in roles:
        projets_concernes |= Projet.objects.filter(bienfaiteurs=user)
        projets_disponibles = projets_disponibles.exclude(bienfaiteurs=user)
        actions_possibles.append("Être bienfaiteur")

    # Si aucun rôle spécifique, afficher tous les projets
    if not actions_possibles:
        projets_concernes = Projet.objects.none()
        projets_disponibles = Projet.objects.all()
        actions_possibles.append("Explorer les projets")

    # Éliminer les doublons
    projets_concernes = projets_concernes.distinct()
    projets_disponibles = projets_disponibles.distinct()

    context = {
        "user": user,
        "roles": roles,
        "projets_concernes": projets_concernes,
        "projets_disponibles": projets_disponibles,
        "actions_possibles": actions_possibles,
    }

    return render(request, "homepage/user_dashboard.html", context)

@login_required
def faire_un_don(request, projet_id):
    projet = Projet.objects.get(id=projet_id)
    # Logique pour faire un don
    # Vous pouvez ajouter ici la mise à jour du montant récolté pour ce projet
    if request.method == 'POST':
        montant_don = request.POST.get('montant')
        projet.montant_recolte += float(montant_don)
        projet.save()
        projet.donateurs.add(request.user)  # Ajout du donateur au projet
        return redirect('homepage:user_dashboard')  # Redirection vers le tableau de bord

    return render(request, 'homepage/faire_un_don.html', {'projet': projet})

@login_required
def sponsoriser_un_projet(request, projet_id):
    projet = Projet.objects.get(id=projet_id)
    # Logique pour sponsoriser un projet
    if request.method == 'POST':
        projet.sponsors.add(request.user)  # Ajout du sponsor au projet
        return redirect('homepage:user_dashboard')

    return render(request, 'homepage/sponsoriser_un_projet.html', {'projet': projet})

@login_required
def etre_bienfaiteur(request, projet_id):
    projet = Projet.objects.get(id=projet_id)
    # Logique pour être bienfaiteur d'un projet
    if request.method == 'POST':
        projet.bienfaiteurs.add(request.user)  # Ajout du bienfaiteur au projet
        return redirect('homepage:user_dashboard')

    return render(request, 'homepage/etre_bienfaiteur.html', {'projet': projet})