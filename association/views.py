# association/views.py
from builtins import print

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from .forms import (AssociationSignupForm, AssociationLoginForm,AssociationForm,MembreUForm,
                    AssociationUserForm,HeritierForm,MembreForm)
from .models import (AssociationUser,Association, Membre,Carnet,Pret,Comptabilite, Message,Payment
,ObjectifSemestriel,LigneCotisation)  # Assurez-vous d'importer tous les modèles nécessaires
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models import Sum
from django.conf import settings
from django.forms import modelformset_factory
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import check_password
from django.http import HttpResponseNotFound
from django.http import HttpResponse
from datetime import datetime,timedelta
from django.utils import timezone
from django.http import JsonResponse
from time import sleep
from django.contrib.auth import logout
from datetime import date
from django.db import transaction
import json
import re
from services.sms import send_sms
from decimal import Decimal
from django.utils.timezone import now
# Inscription
def association_signup(request):
    if request.method == 'POST':
        form = AssociationSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('association_dashboard')
    else:
        form = AssociationSignupForm()
    return render(request, 'association/association_signup.html', {'form': form})

# Connexion
def association_login(request):
    if request.method == 'POST':
        form = AssociationLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('association_dashboard')
    else:
        form = AssociationLoginForm()
    return render(request, 'association/association_login.html', {'form': form})

def accueil(request):
    associations = Association.objects.all()  # Récupérer toutes les associations
    total_associations = associations.count()
    return render(request, 'association/accueil.html', {'associations': associations,
                                                        'total_associations': total_associations })


def creer_association(request):
    if request.method == 'POST':
        form = AssociationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()  # Le mot de passe est haché ici
            return redirect('association:comite_dashboard')  # Redirigez vers une autre vue après la création
    else:
        form = AssociationForm()

    return render(request, 'association/creer_association.html', {'form': form})

def connexion_association(request, assoc_uuid):
    # Récupération de l'association par son assoc_uuid
    association = get_object_or_404(Association, assoc_uuid=assoc_uuid)
    # Récupérer les utilisateurs inscrits pour cette association
    utilisateurs = AssociationUser.objects.filter(association=association, role='association')
    total_users = AssociationUser.objects.filter(association=association, role='association').count()

    total_actions = total_users   # 🔥 Calcul du total des actions

    if request.method == 'POST':
        form = AssociationLoginForm(request.POST)  # Instancie le formulaire avec les données POST
        if form.is_valid():  # Vérifie si le formulaire est valide
            # Récupère le nom d'association et le mot de passe
            nom = form.cleaned_data['nom']
            password = form.cleaned_data['password']

            # Vérifie si le nom correspond et utilise check_password pour vérifier le mot de passe
            if association.nom == nom and association.check_password(password):
                request.session['assoc_uuid'] = str(association.assoc_uuid)  # Convertir l'UUID en chaîne de caractères
 # Stocke l'ID de l'association dans la session
                messages.success(request, "Connexion réussie ! Bienvenue.")  # Affiche un message de succès
                return redirect('association:homepage_association', assoc_uuid=assoc_uuid)  # Redirige vers la page d'accueil de l'association
            else:
                messages.error(request, "Nom d'association ou mot de passe incorrect.")  # Affiche un message d'erreur
    else:
        form = AssociationLoginForm()  # Affiche un formulaire vide pour GET

    return render(request, 'association/connexion_association.html', {
        'association': association,  # Passe l'association au contexte
        'form': form,  # Passe le formulaire au contexte
        'utilisateurs': utilisateurs,
        'total_actions': total_actions
    })
def homepage_association(request, assoc_uuid):
    association = get_object_or_404(Association, assoc_uuid=assoc_uuid)
    # Assurez-vous d'utiliser uniquement AssociationUser pour récupérer les membres du comité
    membres_comite = Membre.objects.filter(association=association)
    membres_association = AssociationUser.objects.filter(association=association, role='association')  # Gardez seulement pour les membres non-comité
    total_membres = membres_comite.count() + membres_association.count()
    error_message_association = None  # Pour gérer les messages d'erreur pour l'Association
    error_message_comite = None  # Pour gérer les messages d'erreur pour le Comité

    if request.method == "POST":
        # Connexion pour l'Association
        if 'id_association' in request.POST and 'password_association' in request.POST:
            identifiant = request.POST['id_association']
            password = request.POST['password_association']

            # Utilisation du backend personnalisé pour authentifier avec l'identifiant et le mot de passe
            user = authenticate(request, identifiant=identifiant, password=password)

            if user is not None:
                if user.role == 'association':
                    login(request, user)
                    messages.success(request, "Connexion réussie ! Bienvenue.")
                    return redirect('association:association_dashboard')
                else:
                    messages.error(request, "Vous n'êtes pas un membre de l'association.")
            else:
                messages.error(request, "Identifiant ou mot de passe incorrect pour l'Association.")

        # Connexion pour le Comité
        elif 'id_comite' in request.POST and 'password_comite' in request.POST:
            identifiant = request.POST['id_comite']
            password = request.POST['password_comite']

            # Utilisation du backend personnalisé pour authentifier avec l'identifiant et le mot de passe
            user = authenticate(request, identifiant=identifiant, password=password)

            if user is not None:
                if user.role == 'comite':
                    login(request, user)
                    messages.success(request, "Connexion réussie ! Bienvenue au Comité.")
                    return redirect('association:comite_dashboard')
                else:
                    messages.error(request, "Vous n'êtes pas un membre du comité.")
            else:
                messages.error(request, "Identifiant ou mot de passe incorrect pour le Comité.")

    context = {
        'association': association,
        'error_message_association': error_message_association,
        'error_message_comite': error_message_comite,
        'membres_comite': membres_comite,
        'membres_association': membres_association,
        'total_membres': total_membres,
        'total_membres_comite': membres_comite.count(),
        'total_membres_association': membres_association.count(),
    }
    return render(request, 'association/homepage_association.html', context)
def custom_logout(request):
    if request.user.is_authenticated:
        # Récupérer l'association de l'utilisateur connecté
        association = getattr(request.user, 'association', None)
        logout(request)  # Déconnexion de l'utilisateur

        # Si l'utilisateur a une association, rediriger vers homepage_association
        if association:
            return redirect('association:homepage_association', assoc_uuid=association.assoc_uuid)

    # Rediriger vers une page par défaut si pas d'association
    return redirect('association:acceuil')
def lister_associations(request):
    associations = Association.objects.all()
    return render(request, 'association/liste_associations.html', {'associations': associations})


def situation(request):
    # Liste des montants de cotisation
    montants = [500, 1000, 1500, 2000, 5000, 10000]
    association = request.user.association  # Obtenez l'association de l'utilisateur

    updated_users_by_montant = {}  # Dictionnaire pour stocker les utilisateurs mis à jour par montant

    if request.method == "POST":
        try:
            with transaction.atomic():
                print("Soumission du formulaire détectée.")

                updated_users_by_montant = {}  # Crée cette variable pour stocker les utilisateurs mis à jour

                for montant in montants:
                    print(f"--- Traitement pour le montant {montant} CFA ---")

                    selected_user_ids = request.POST.getlist(f'selected_users_{montant}')
                    print(f"IDs des utilisateurs sélectionnés : {selected_user_ids}")

                    if selected_user_ids:
                        users_selected = AssociationUser.objects.filter(
                            id__in=selected_user_ids, association=association
                        )
                        print(f"Utilisateurs trouvés en base pour ce montant : {list(users_selected)}")

                        nombre_mois = request.POST.get(f'mois_{montant}', None)
                        montant_total = request.POST.get(f'montant_{montant}', None)
                        print(f"Valeurs reçues : Nombre de mois = {nombre_mois}, Montant total = {montant_total}")

                        if nombre_mois and montant_total:
                            nombre_mois = int(nombre_mois)
                            montant_total = montant_total.replace('\u202f', '').replace(',', '').replace(' CFA', '')
                            montant_total = Decimal(montant_total)

                            print(
                                f"Valeurs après conversion : Nombre de mois = {nombre_mois}, Montant total = {montant_total} CFA")

                            for user in users_selected:
                                annee_courante = datetime.now().year
                                semestre_courant = 1 if datetime.now().month <= 6 else 2

                                objectif_semestriel, created = ObjectifSemestriel.objects.get_or_create(
                                    utilisateur=user,
                                    annee=annee_courante,
                                    semestre=semestre_courant,
                                    defaults={
                                        'objectif_general': nombre_mois,
                                        'solde_objectif_general': montant_total,
                                        'objectif_personnel_6_mois': 0,
                                        'solde_objectif_personnel': 0,
                                        'date_limite_objectifs': datetime.now() + timedelta(days=30 * nombre_mois)
                                    }
                                )
                                if not created:
                                    objectif_semestriel.objectif_general = nombre_mois
                                    objectif_semestriel.solde_objectif_general += montant_total
                                    objectif_semestriel.date_limite_objectifs = datetime.now() + timedelta(
                                        days=30 * nombre_mois)
                                    objectif_semestriel.save()

                                print(
                                    f"Objectif semestriel mis à jour pour l'utilisateur {user.id} ({user.last_name}):")
                                print(f"  - Objectif général : {objectif_semestriel.objectif_general}")
                                print(f"  - Solde objectif général : {objectif_semestriel.solde_objectif_general} CFA")

                            updated_users_by_montant[montant] = users_selected
                        else:
                            print(f"Aucune mise à jour effectuée pour le montant {montant} (valeurs invalides).")

                messages.success(request, "Les mises à jour ont été effectuées avec succès.")
                print(">>> Mise à jour réussie pour tous les montants.")
        except Exception as e:
            messages.error(request, f"Une erreur est survenue : {str(e)}")
            print(f"!!! Erreur pendant la mise à jour : {str(e)}")

        print(">>> Récapitulatif des utilisateurs mis à jour :")
        for montant, users in updated_users_by_montant.items():
            print(f"Montant {montant} CFA :")
            for user in users:
                objectif_semestriel = ObjectifSemestriel.objects.filter(utilisateur=user).latest('annee', 'semestre')
                print(
                    f"- {user.id} ({user.last_name}) - Objectif : {objectif_semestriel.objectif_general}, Solde : {objectif_semestriel.solde_objectif_general} CFA")

        return render(request, 'association/situation.html', {
            'montants': montants,
            'updated_users_by_montant': updated_users_by_montant,
        })

    # Si le formulaire n'est pas soumis, récupérer les utilisateurs
    users = AssociationUser.objects.filter(
        association=association,
        montant_adhesion__in=montants
    ).exclude(role='comite')

    print(">>> Chargement initial des utilisateurs disponibles :")
    for user in users:
        print(f"- {user.id} ({user.last_name}) - Montant adhésion : {user.montant_adhesion} CFA")

    return render(request, 'association/situation.html', {
        'users': users,
        'montants': montants,
        'updated_users_by_montant': {},  # Vide au chargement initial
    })


def objectif6mois(request):
    # Liste des montants de cotisation
    montants = [500, 1000, 1500, 2000, 5000, 10000]
    association = request.user.association  # Obtenez l'association de l'utilisateur

    updated_users_by_montant = {}  # Dictionnaire pour stocker les utilisateurs mis à jour par montant

    if request.method == "POST":
        try:
            with transaction.atomic():
                print("Soumission du formulaire détectée.")

                # Récupérer les utilisateurs sélectionnés pour mise à jour
                for montant in montants:
                    print(f"--- Traitement pour le montant {montant} CFA ---")

                    # Récupération des utilisateurs sélectionnés pour ce montant
                    selected_user_ids = request.POST.getlist(f'selected_users_{montant}')
                    print(f"IDs des utilisateurs sélectionnés : {selected_user_ids}")

                    if selected_user_ids:
                        # Filtrer les utilisateurs dans la base de données
                        users_selected = AssociationUser.objects.filter(
                            id__in=selected_user_ids, association=association
                        )
                        print(f"Utilisateurs trouvés en base pour ce montant : {list(users_selected)}")

                        # Récupérer les valeurs saisies pour ce montant
                        nombre_mois = request.POST.get(f'mois_{montant}', None)
                        montant_total = request.POST.get(f'montant_{montant}', None)
                        print(f"Valeurs reçues : Nombre de mois = {nombre_mois}, Montant total = {montant_total}")

                        if nombre_mois and montant_total:
                            # Convertir les données
                            nombre_mois = int(nombre_mois)
                            montant_total = montant_total.replace('\u202f', '').replace(',', '').replace(' CFA', '')
                            montant_total = Decimal(montant_total)

                            print(
                                f"Valeurs après conversion : Nombre de mois = {nombre_mois}, Montant total = {montant_total} CFA")

                            # Mettre à jour les utilisateurs sélectionnés
                            for user in users_selected:
                                annee_courante = datetime.now().year
                                semestre_courant = 1 if datetime.now().month <= 6 else 2

                                objectif_semestriel, created = ObjectifSemestriel.objects.get_or_create(
                                    utilisateur=user,
                                    annee=annee_courante,
                                    semestre=semestre_courant,
                                    defaults={
                                        'objectif_general': 0,
                                        'solde_objectif_general': 0,
                                        'objectif_personnel_6_mois': nombre_mois,
                                        'solde_objectif_': montant_total,
                                        'date_limite_objectifs': datetime.now() + timedelta(days=30 * nombre_mois)
                                    }
                                )
                                if not created:
                                    objectif_semestriel.objectif_personnel_6_mois = nombre_mois
                                    objectif_semestriel.solde_objectif_personnel += montant_total
                                    objectif_semestriel.date_limitepersonnel_objectifs = datetime.now() + timedelta(
                                        days=30 * nombre_mois)
                                    objectif_semestriel.save()

                                print(
                                    f"Objectif semestriel mis à jour pour l'utilisateur {user.id} ({user.last_name}):")
                                print(f"  - Objectif personnel : {objectif_semestriel.objectif_personnel_6_mois}")
                                print(f"  - Solde objectif personnel : {objectif_semestriel.solde_objectif_personnel} CFA")

                            # Enregistrer les utilisateurs mis à jour pour affichage
                            updated_users_by_montant[montant] = users_selected
                        else:
                            print(f"Aucune mise à jour effectuée pour le montant {montant} (valeurs invalides).")

                messages.success(request, "Les mises à jour ont été effectuées avec succès.")
                print(">>> Mise à jour réussie pour tous les montants.")
        except Exception as e:
            messages.error(request, f"Une erreur est survenue : {str(e)}")
            print(f"!!! Erreur pendant la mise à jour : {str(e)}")

        # Affichage des utilisateurs mis à jour dans les prints
        print(">>> Récapitulatif des utilisateurs mis à jour :")
        for montant, users in updated_users_by_montant.items():
            print(f"Montant {montant} CFA :")
            for user in users:
                print(
                    f"- {user.id} ({user.last_name}) - Objectif : {user.objectif_personnel_6_mois}, Solde : {user.solde_objectif_personnel} CFA")

        return render(request, 'association/objectif6mois.html', {
            'montants': montants,
            'updated_users_by_montant': updated_users_by_montant,
        })

    # Si le formulaire n'est pas soumis, récupérer les utilisateurs
    users = AssociationUser.objects.filter(
        association=association,
        montant_adhesion__in=montants
    ).exclude(role='comite')

    print(">>> Chargement initial des utilisateurs disponibles :")
    for user in users:
        print(f"- {user.id} ({user.last_name}) - Montant adhésion : {user.montant_adhesion} CFA")

    return render(request, 'association/objectif6mois.html', {
        'users': users,
        'montants': montants,
        'updated_users_by_montant': {},  # Vide au chargement initial
    })
def get_current_semester():
    month = timezone.now().month
    if month <= 6:
        return 1  # Premier semestre
    else:
        return 2  # Deuxième semestre

def comite_dashboard(request):
    today = datetime.today()
    recette_actuelle = request.session.get('recette_actuelle', 0)
    nombre_inscriptions = int(request.GET.get('nombre_inscriptions', 1))
    association = request.user.association
    types_cotisation = [500, 1000, 1500, 2000, 5000, 10000]
    utilisateur_connecte = get_object_or_404(AssociationUser, identifiant=request.user.identifiant)
    # Récupérer ou définir le selected_cotisation
    selected_cotisation = request.POST.get('type_cotisation', request.GET.get('type_cotisation'))
    if not selected_cotisation:
        selected_cotisation = request.session.get('current_selected_cotisation')

    try:
        selected_cotisation = int(selected_cotisation) if selected_cotisation else None
    except ValueError:
        selected_cotisation = None

    if selected_cotisation:
        request.session['current_selected_cotisation'] = selected_cotisation

    AssociationUserFormSet = modelformset_factory(
        AssociationUser,
        form=AssociationUserForm,
        extra=nombre_inscriptions
    )

    membres = AssociationUser.objects.none()
    formset = AssociationUserFormSet(queryset=AssociationUser.objects.none())

    if request.method == 'POST' and 'submit' in request.POST:
        formset = AssociationUserFormSet(request.POST, queryset=AssociationUser.objects.none())
        if formset.is_valid():
            # Récupérer l'association du comité connecté (request.user)
            association_du_comite = request.user.association  # Assurez-vous que 'association' est un champ sur le modèle User

            # Enregistrer les utilisateurs pour l'association du comité
            instances = formset.save(
                commit=False)  # Ne pas enregistrer immédiatement pour ajouter des données supplémentaires
            for instance in instances:
                instance.association = association_du_comite  # Lier l'utilisateur à l'association du comité connecté
                instance.save()

                # Mettre à jour le parrainage (si applicable)
                parrain = instance.parrain
                if parrain:
                    parrain.nombre_total_filleuls += 1
                    parrain.save()

            if parrain:
                # Année et semestre actuels
                current_year = now().year
                current_month = now().month
                semestre = 1 if current_month <= 6 else 2

                # Vérifier si un carnet existe déjà pour le parrain, l'année et le semestre
                carnet, created = Carnet.objects.get_or_create(
                    utilisateur=parrain,
                    annee=current_year,
                    semestre=semestre,
                    defaults={
                        'total_cotisation': 0.00,
                        'total_penalite': 0.00,
                        'total_sanctions': 0.00,
                        'nombre_filleuls_semestre': 0,
                        'interets': 0.00,
                        'depenses_lucratives': 0.00,
                        'dividendes': 0.00,
                    }
                )

                # Mettre à jour le nombre de filleuls pour ce semestre
                carnet.nombre_filleuls_semestre += 1
                carnet.save()
            messages.success(request, "Les inscriptions ont été validées avec succès.")
            return redirect('association:comite_dashboard')
        else:
            messages.error(request, "Une erreur s'est produite lors de la validation des inscriptions.")

    inscrits = AssociationUser.objects.filter(association=association).exclude(role='comite')

    if selected_cotisation:
        users = AssociationUser.objects.filter(association=association, montant_adhesion=selected_cotisation).exclude(role='comite')
    else:
        users = AssociationUser.objects.filter(association=association).exclude(role='comite')

    if request.method == 'POST' and 'valider' in request.POST:
        selected_users_ids = request.POST.getlist('user_ids')

        try:
            if selected_users_ids:
                selected_users = AssociationUser.objects.filter(id__in=selected_users_ids)
            else:
                selected_users = users

            total_cotisations = 0
            for user in selected_users:
                user.solde_cotisation_mensuelle += selected_cotisation
                user.save()
                total_cotisations += selected_cotisation
                # Récupérer ou créer un carnet pour l'utilisateur avec le semestre automatique
                semestre_actuel = get_current_semester()
                carnet, created = Carnet.objects.get_or_create(
                    utilisateur=user,
                    annee=timezone.now().year,
                    semestre=semestre_actuel
                )
                carnet.total_cotisation += selected_cotisation
                carnet.save()

                # Créer une ligne de cotisation associée à ce carnet
                ligne = LigneCotisation.objects.create(
                    carnet=carnet,
                    cotisation=selected_cotisation
                )
                ligne.save()

            messages.success(request, f"Les cotisations ont été mises à jour avec succès. Total des cotisations : {total_cotisations} CFA.")

            request.session.pop('current_selected_cotisation', None)

        except Exception as e:
            messages.error(request, f"Une erreur s'est produite lors de la mise à jour des cotisations : {str(e)}")

        return redirect('association:comite_dashboard')

    return render(request, 'association/comite_dashboard.html', {
        'formset': formset,
        'nombre_inscriptions': nombre_inscriptions,
        'inscrits': inscrits,
        'membres': membres,
        'types_cotisation': types_cotisation,
        'users': users,
        'selected_cotisation': selected_cotisation,
        'today': today,
        'recette_actuelle': recette_actuelle,
        'utilisateur_connecte': utilisateur_connecte
    })


def get_infos_du_mois(carnets, annee, mois):
    cotisation = penalite = sanction = 0
    for carnet in carnets.filter(annee=annee):
        for ligne in carnet.lignes.filter(date__month=mois):
            # Vérifier et convertir en Decimal si nécessaire
            cotisation += Decimal(ligne.cotisation) if ligne.cotisation else Decimal(0)
            penalite += Decimal(ligne.penalite) if ligne.penalite else Decimal(0)
            sanction += Decimal(ligne.sanctions) if ligne.sanctions else Decimal(0)
    return {'cotisation': cotisation, 'penalite': penalite, 'sanction': sanction}


def association_dashboard(request):
    utilisateur_connecte = None
    membre = None
    association_id = None
    cotisations = []
    carnets = []
    annee_courante = datetime.now().year

    try:
        if request.user.is_authenticated:
            utilisateur_connecte = AssociationUser.objects.get(identifiant=request.user.identifiant)
            carnets = Carnet.objects.filter(utilisateur=utilisateur_connecte)
            objectifs_semestriels = ObjectifSemestriel.objects.filter(utilisateur=utilisateur_connecte)

            if utilisateur_connecte.association:
                assoc_uuid = utilisateur_connecte.association.assoc_uuid
                messages.success(request,
                                 f"Bienvenue, {request.user.first_name} ! Vous êtes connecté à votre tableau de bord.")
            else:
                association_id = None
                messages.warning(request, "Vous n'êtes associé à aucune organisation.")


        else:
            messages.warning(request, "Vous devez être connecté pour accéder à votre tableau de bord.")
    except (AssociationUser.DoesNotExist, Membre.DoesNotExist):
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
                'objectif_general': "Non renseigné",
                'solde_objectif_general': "Non renseigné",
                'objectif_personnel_6_mois': "Non renseigné",
                'solde_objectif_personnel': "Non renseigné",
                'date_limite_objectifs': "Non renseigné",
            }
            for mois in mois_semestre[semestre]:
                infos_du_mois = get_infos_du_mois(carnets, annee, mois) if annee <= annee_courante else {
                    'cotisation': 0, 'penalite': 0, 'sanction': 0, 'mois': mois}
                infos_du_mois['mois'] = mois
                semestre_infos['mois_infos'].append(infos_du_mois)

                # Ajouter les valeurs aux totaux du semestre
                semestre_infos['totaux']['total_cotisation'] += infos_du_mois['cotisation']
                semestre_infos['totaux']['total_penalite'] += infos_du_mois['penalite']
                semestre_infos['totaux']['total_sanction'] += infos_du_mois['sanction']

            # Vérifier si les objectifs semestriels existent et les ajouter
            objectif_semestriel = objectifs_semestriels.filter(annee=annee, semestre=semestre).first()
            if objectif_semestriel:
                semestre_infos['objectif_general'] = objectif_semestriel.objectif_general
                semestre_infos['solde_objectif_general'] = objectif_semestriel.solde_objectif_general
                semestre_infos['objectif_personnel_6_mois'] = objectif_semestriel.objectif_personnel_6_mois
                semestre_infos['solde_objectif_personnel'] = objectif_semestriel.solde_objectif_personnel
                semestre_infos['date_limite_objectifs'] = objectif_semestriel.date_limite_objectifs

            informations_par_annee_semestre.append(semestre_infos)

    context = {
        'membre': membre,
        'association_id': association_id,
        'cotisations': cotisations,
        'association_user': utilisateur_connecte,
        'carnets': carnets,
        'annees': annees,
        'semestres': semestres,
        'informations_par_annee_semestre': informations_par_annee_semestre
    }

    return render(request, 'association/association_dashboard.html', context)


def update_member(request):
    try:
        user = request.user

        if request.method == 'POST':
            form = MembreForm(request.POST, request.FILES, instance=user)
            if form.is_valid():
                form.save()
                messages.success(request, "Les informations ont été mises à jour avec succès.")
                return redirect('association:mes_information')  # Redirige vers la page appropriée

        else:
            form = MembreForm(instance=user)

    except AssociationUser.DoesNotExist:
        form = MembreForm()  # En cas d'erreur, afficher un formulaire vide

    return render(request, 'association/update_member.html', {'form': form})
def update_heritier(request):
    try:
        # Récupérer l'utilisateur connecté
        user = request.user  # Utilisateur actuellement connecté

        # Si c'est un envoi de formulaire
        if request.method == 'POST':
            form = HeritierForm(request.POST, request.FILES, instance=user)

            if form.is_valid():
                form.save()  # Enregistrer les modifications
                messages.success(request, "Les informations de l'héritier ont été mises à jour avec succès.")
                return redirect('association:mes_information')  # Rediriger après la mise à jour

        else:
            form = HeritierForm(instance=user)  # Pré-remplir le formulaire avec les données existantes

    except AssociationUser.DoesNotExist:
        form = HeritierForm()  # Si l'utilisateur n'existe pas encore, afficher un formulaire vide

    return render(request, 'association/update_heritier.html', {'form': form})
@login_required
def creer_membre(request):
    if request.method == 'POST':
        form = MembreForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('association:liste_membres')
    else:
        form = MembreForm()
    return render(request, 'association/creer_membre.html', {'form': form})

def validate_contributions(request):
    utilisateurs = AssociationUser.objects.filter(role='membre')
    total_validated = 0

    if request.method == 'POST':
        montant = request.POST.get('montant')
        nombre_personnes = request.POST.get('nombre_personnes')
        montant_total = int(montant) * int(nombre_personnes)

        # Commencer une transaction atomique pour valider
        try:
            with transaction.atomic():
                for utilisateur in utilisateurs:
                    if utilisateur.solde < montant_total:
                        raise ValidationError(_("Solde insuffisant pour l'utilisateur"))

                    # Valider chaque contribution pour chaque utilisateur
                    Transaction.objects.create(
                        utilisateur=utilisateur,
                        type_transaction='validation',
                        montant=montant_total
                    )
                    total_validated += montant_total
                messages.success(request, "Validation réussie.")
        except ValidationError as e:
            messages.error(request, f"Échec de la validation : {str(e)}")

    return render(request, 'validate_contributions.html', {
        'utilisateurs': utilisateurs,
        'total_validated': total_validated,
    })

def restore_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    if transaction.type_transaction == 'validation' and transaction.valide:
        # Créer une transaction de restauration
        Transaction.objects.create(
            utilisateur=transaction.utilisateur,
            type_transaction='restoration',
            montant=transaction.montant
        )
        messages.success(request, "Restauration effectuée.")
    else:
        messages.error(request, "Restauration impossible pour cette transaction.")
    return redirect('validate_contributions')


def mes_information(request):
    utilisateur_connecte = None
    membre = None
    association_id = None
    try:
        if request.user.is_authenticated:
            # Récupérer l'utilisateur connecté
            utilisateur_connecte = AssociationUser.objects.get(identifiant=request.user.identifiant)

            # Vérifier que l'utilisateur appartient à une association et qu'il a le rôle 'association'
            if utilisateur_connecte.association and utilisateur_connecte.role == 'association':
                association_association = utilisateur_connecte.association.nom
            else:
                # Si l'utilisateur n'a pas de rôle 'association', rediriger ou gérer l'erreur
                return redirect('association:acceuil')  # Ou un autre comportement

            # Récupérer l'objet Membre lié à cet utilisateur
            membre = Membre.objects.get(utilisateur=utilisateur_connecte)
        else:
            # Si l'utilisateur n'est pas connecté, on définit membre et association_id à None
            membre = None
            association_id = None

    except (AssociationUser.DoesNotExist, Membre.DoesNotExist) as e:
        # Gérer le cas où l'utilisateur ou le membre n'existe pas
        print(f"Erreur: {e}")
        membre = None
        association_id = None

    context = {
        'membre': membre,
        'association_id': association_id,
        'association_user': utilisateur_connecte,  # Ajouter l'utilisateur connecté dans le contexte
    }
    return render(request, 'association/mes_information.html', context)

def demande_assistance(request):
    utilisateur_connecte = get_object_or_404(AssociationUser, identifiant=request.user.identifiant)
    current_year = timezone.now().year
    semestre = 1 if timezone.now().month <= 6 else 2

    try:
        carnet = Carnet.objects.get(utilisateur=utilisateur_connecte, annee=current_year, semestre=semestre)
        part_sociale = carnet.total_sociale
    except Carnet.DoesNotExist:
        part_sociale = Decimal('0.00')

    parrain = utilisateur_connecte.parrain
    filleuls = AssociationUser.objects.filter(parrain=utilisateur_connecte)

    montant_parrain = parrain.montant_adhesion * Decimal('0.50') if parrain else Decimal('0.00')
    montant_filleuls = sum(filleul.montant_adhesion * Decimal('0.25') for filleul in filleuls)

    if request.method == 'POST':
        date = request.POST.get('date')
        evenement = request.POST.get('evenement')
        description = request.POST.get('description')
        quota = request.POST.get('quota')
        membre_nom = request.POST.get('membre_nom')
        comptable_nom = request.POST.get('comptable_nom')
        date_accord = request.POST.get('date_accord')
        date_retrait = request.POST.get('date_retrait')

        montant_total = (part_sociale * Decimal(quota.replace('X', ''))) + montant_parrain + montant_filleuls

        lettre = f"""
        Lomé, le {date}
        À
        Monsieur le Président
        du CEG CON PRO

        Objet : Demande d’Assistance

        Monsieur le Président,

        Suite à un événement {evenement} que je vis,
        Suite au {description},
        Et selon mon statut de membre et nos règlements intérieurs du club,
        Je vous prie de m'accorder une assistance de {quota} le quota de ma part sociale.
        L'apport de 50% de la mise de mon parrain, et 25% de tous mes filleuls du club,
        Une somme qui pourrait s'élever à {montant_total} F CFA – 10% de commission.

        Exact…. Non réclamation…. (Justifier)

        Veuillez agréer, Monsieur le Président, l'expression de mes salutations distinguées.

   
        """

        # Créer et enregistrer le message
        comite_user = AssociationUser.objects.get(role='comite',association=utilisateur_connecte.association)  # Assurez-vous que le rôle 'comite' est correct
        Message.objects.create(
            sender=utilisateur_connecte,
            recipient=comite_user,
            subject='Demande d’Assistance',
            body=lettre
        )

        # Afficher un message de succès
        messages.success(request, "Votre demande d'assistance a été envoyée avec succès au comité.")
        return redirect('association:demande_assistance')
    context = {
        'part_sociale': part_sociale,
        'montant_parrain': montant_parrain,
        'montant_filleuls': montant_filleuls,
        'utilisateur': utilisateur_connecte,
    }

    return render(request, 'association/demande_assistance.html', context)


def inbox(request):
    utilisateur_connecte = get_object_or_404(AssociationUser, identifiant=request.user.identifiant)

    if request.method == 'POST':
        message_id = request.POST.get('message_id')
        if not message_id:
            return JsonResponse({'success': False, 'error': 'ID de message manquant'})

        # Récupérer le message non complété pour l'utilisateur connecté
        message = get_object_or_404(Message, id=message_id, recipient=utilisateur_connecte, is_completed=False)

        # Récupérer les données du formulaire
        date_accord = request.POST.get('date_accord')
        date_retrait = request.POST.get('date_retrait')
        comptable_nom = request.POST.get('comptable_nom')
        signature = request.POST.get('signature')

        # Compléter la lettre existante avec les nouvelles informations en fonction du type de demande
        lettre = message.body
        if message.subject == 'Demande d’Assistance':
            lettre += f"""
            Réponse du Président
            Lu et approuvé… Votre requête est accordée et sera virée au plus tard le {date_accord} Désolé Demande non accordée………   Signature
                                                Retirée, le {date_retrait}
            Nom et Prénom du Comptable : {comptable_nom}
            Signature : {signature}
            """
        elif message.subject == 'Demande de Pret':
            montant_pret = request.POST.get('montant_pret')
            taux_interet = request.POST.get('taux_interet')
            duree_remboursement = request.POST.get('duree_remboursement')
            lettre += f"""
            Réponse du Président
            Lu et approuvé…Accordé pour {montant_pret} CFA avec un taux de {taux_interet}%. Remboursement en {duree_remboursement} mois.
            Retirée le {date_retrait}
            Nom et Prénom du Comptable : {comptable_nom}
            Signature : {signature}
            """
        else:
            return JsonResponse({'success': False, 'error': 'Sujet inconnu'})

        # Mettre à jour le message avec la lettre complétée
        message.body = lettre
        message.is_completed = True
        message.is_grayed = True
        message.save()

    # Récupérer les messages non complétés pour l'utilisateur connecté
    messages = Message.objects.filter(recipient=utilisateur_connecte, is_completed=False).order_by('-timestamp')

    demandes_assistance = messages.filter(subject="Demande d’Assistance")
    demandes_pret = messages.filter(subject='Demande de Pret')
    return render(request, 'association/inbox.html', {'messages': messages, 'demandes_pret': demandes_pret, 'demandes_assistance': demandes_assistance})

def accepter_message(request, message_id):
    # Récupérer le message en fonction de l'ID
    message = get_object_or_404(Message, id=message_id)

    # Mettre à jour le statut du message à 'accepté'
    message.status = 'accepté'
    message.save()

    # Vérifier si le message est une demande de prêt et extraire les informations
    if "Demande de Pret" in message.subject:
        # Extraire les informations du body (utilisez des expressions régulières ou des méthodes simples de découpe)
        evenement = extraire_informations(message.body, 'evenement')
        description = extraire_informations(message.body, 'description')
        montant_pret = extraire_informations(message.body, 'montant_pret')
        taux_interet = extraire_informations(message.body, 'interet')
        duree_remboursement = extraire_informations(message.body, 'duree_remboursement')

        # Créer un objet Pret avec les données extraites
        pret = Pret.objects.create(
            utilisateur=message.sender,  # L'utilisateur qui a envoyé la demande
            montant=montant_pret,
            taux_interet=taux_interet,
            duree_mois=duree_remboursement,
            statut='en cours',  # Statut initial du prêt
        )

        # Afficher un message de succès pour l'acceptation du prêt
        messages.success(request, "La demande de prêt a été acceptée et le prêt a été créé.")

    else:
        # Si ce n'est pas une demande de prêt, vous pouvez ajouter un autre traitement ici
        messages.info(request, "Le message a été accepté, mais ce n'est pas une demande de prêt.")

    # Retourner à la boîte de réception après traitement
    return redirect('association:inbox')


# Fonction pour extraire les informations du corps de la lettre
def extraire_informations(body, champ):
    """ Fonction pour extraire les informations du body en fonction du champ donné"""
    pattern = r"\{" + champ + r"\} (.*?) \{"  # Recherche des variables entre crochets
    result = re.search(pattern, body)
    if result:
        return result.group(1)  # Retourner la valeur trouvée
    return None  # Si le champ n'est pas trouvé


def rejeter_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)

    if request.method == 'POST':
        motif = request.POST.get('motif', '').strip()

        if motif:
            message.status = 'rejeté'
            message. is_grayed = True
            message.rejet_motif = motif  # On enregistre le motif
            message.save()
            messages.success(request, "Le message a été rejeté avec succès.")
        else:
            messages.error(request, "Veuillez fournir un motif de rejet.")

    return redirect('association:inbox')

def mettre_en_attente_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    message.status = 'en attente'
    message.save()
    messages.success(request, "Le message a été mis en attente.")
    return redirect('association:inbox')

def completer_lettre(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    if request.method == 'POST':
        message.date_accord = request.POST.get('date_accord')
        message.date_retrait = request.POST.get('date_retrait')
        message.comptable_nom = request.POST.get('comptable_nom')
        message.is_completed = True
        message.save()
        messages.success(request, "La lettre a été complétée et renvoyée avec succès.")
        return redirect('association:inbox')
    return render(request, 'association/inbox.html', {'message': message})

def message_envoye(request):
    utilisateur_connecte = request.user
    messages = Message.objects.filter(recipient=utilisateur_connecte, is_completed=True).order_by('-timestamp')  # Affiche uniquement les messages complétés
    return render(request, 'association/message_envoye.html', {'messages': messages})
def message_envoye_comite(request):
    utilisateur_connecte = request.user
    messages = Message.objects.filter(sender=request.user).order_by('-timestamp')  # Récupère tous les messages envoyés par l'utilisateur connecté

    # Filtrer la partie "Réponse du Président" dans le corps du message (body)
    for message in messages:
        if "Réponse du Président" in message.body:
            # Séparer la réponse du président du message
            message.body = message.body.split("Réponse du Président")[0]

    return render(request, 'association/message_envoye_comite.html', {'messages': messages})

def message_recu_comite(request):
    utilisateur_connecte = request.user
    messages = Message.objects.filter(sender=utilisateur_connecte, is_completed=True).order_by('-timestamp')  # Affiche uniquement les messages complétés
    message = Message.objects.filter(sender=utilisateur_connecte, status='rejeté').order_by('-timestamp')
    return render(request, 'association/message_recu_comite.html', {'messages': messages
                                ,'message': message})


def demande_pret(request):
    utilisateur_connecte = get_object_or_404(AssociationUser, identifiant=request.user.identifiant)
    current_year = datetime.now().year
    semestre = 1 if datetime.now().month <= 6 else 2

    try:
        carnet = Carnet.objects.get(utilisateur=utilisateur_connecte, annee=current_year, semestre=semestre)
        part_lucrative = carnet.total_lucrative
    except Carnet.DoesNotExist:
        part_lucrative = Decimal('0.00')

    if request.method == 'POST':
        # Récupérer les données du formulaire
        date = request.POST.get('date')
        evenement = request.POST.get('evenement')
        description = request.POST.get('description')
        try:
            pourcentage_pret = Decimal(request.POST.get('pourcentage_pret'))
            duree_remboursement = int(request.POST.get('duree_remboursement'))
            interet = Decimal(request.POST.get('interet'))
        except (ValueError, TypeError):
            messages.error(request, "Les valeurs de pourcentage, durée et intérêt doivent être valides.")
            return redirect('association:demande_pret')

        membre_nom = request.POST.get('membre_nom')
        comptable_nom = request.POST.get('comptable_nom')
        date_accord = request.POST.get('date_accord')
        date_retrait = request.POST.get('date_retrait')

        # Calculer le montant du prêt et le total à rembourser
        montant_pret = part_lucrative * (pourcentage_pret / 100)
        total_remboursement = montant_pret + (montant_pret * (interet / 100))

        # Créer la lettre
        lettre = f"""
        Lomé, le {date}
        À
        Monsieur le Président
        du CEG CON PRO

        Objet : Demande de Pret

        Monsieur le Président,

        Suite à un événement {evenement} que je vis,
        Suite au {description},
        Selon mon statut de membre, nos règlements intérieurs du club,
        Je vous prie de m'accorder un prêt de {pourcentage_pret}% de mon net lucratif dans le club,
        Une somme qui pourrait s'élever à {montant_pret} F CFA. Que je compte payer en {duree_remboursement} Mois. Avec un intérêt de {interet}%.Un totale de {total_remboursement} F CFA. Compte Exacte…. Non réclamation…. Envoyer

        Veuillez agréer, Monsieur le Président, l'expression de mes salutations distinguées.

 
        """

        # Enregistrer le message
        try:
            comite_user = AssociationUser.objects.get(role='comite',association=utilisateur_connecte.association)  # Assurez-vous que le rôle 'comite' est correct
            Message.objects.create(
                sender=utilisateur_connecte,
                recipient=comite_user,
                subject='Demande de Pret',
                body=lettre

            )
            # Message de succès
            messages.success(request, "Votre demande d'assistance a été envoyée avec succès au comité.")
        except AssociationUser.DoesNotExist:
            messages.error(request, "Le comité n'a pas été trouvé. Veuillez vérifier votre configuration.")

        return redirect('association:demande_pret')

    context = {
        'part_lucrative': part_lucrative,
        'utilisateur': utilisateur_connecte,
    }

    return render(request, 'association/demande_pret.html', context)


def autre_detail(request):
    # Utilisateur connecté
    utilisateur_connecte = get_object_or_404(AssociationUser, identifiant=request.user.identifiant)

    # Définir l'année de début manuellement ici
    debut = 2024  # Vous pouvez changer cette année manuellement à tout moment

    # L'année de fin est 5 ans après l'année de début
    end_year = debut + 5

    # Récupérer les carnets à partir de l'année de début
    carnets = Carnet.objects.filter(utilisateur=utilisateur_connecte, annee__gte=debut).order_by('annee', 'semestre')

    details = []
    previous_total_sociale = Decimal('0.00')
    previous_total_lucrative = Decimal('0.00')

    # Commencer à partir de l'année de début
    for annee in range(debut, end_year + 1):
        for semestre in [1, 2]:
            try:
                carnet = carnets.get(annee=annee, semestre=semestre)
                total_cotisation = carnet.total_cotisation
                part_sociale = total_cotisation * Decimal('0.25')
                part_lucrative = total_cotisation * Decimal('0.75')
                nombre_filleuls_semestre = carnet.nombre_filleuls_semestre

                ancien_total_sociale = previous_total_sociale
                ancien_total_lucrative = previous_total_lucrative
                nouveau_total_sociale = part_sociale
                nouveau_total_lucrative = part_lucrative

                total_sociale = ancien_total_sociale + nouveau_total_sociale
                total_lucrative = ancien_total_lucrative + nouveau_total_lucrative
                carnet.part_sociale = part_sociale
                carnet.part_lucrative = part_lucrative
                carnet.total_sociale = total_sociale
                carnet.total_lucrative = total_lucrative
                carnet.save()
                details.append({
                    'annee': annee,
                    'semestre': semestre,
                    'part_sociale': part_sociale,
                    'part_lucrative': part_lucrative,
                    'nombre_filleuls': nombre_filleuls_semestre,
                    'ancien_total_sociale': ancien_total_sociale,
                    'ancien_total_lucrative': ancien_total_lucrative,
                    'nouveau_total_sociale': nouveau_total_sociale,
                    'nouveau_total_lucrative': nouveau_total_lucrative,
                    'total_sociale': total_sociale,
                    'total_lucrative': total_lucrative,
                    'assistance_joie_obtenue': carnet.assistance_joie_obtenue,
                    'assistance_joie_reste': carnet.assistance_joie_reste,
                    'assistance_detresse_obtenue': carnet.assistance_detresse_obtenue,
                    'assistance_detresse_reste': carnet.assistance_detresse_reste,
                })

                previous_total_sociale = total_sociale
                previous_total_lucrative = total_lucrative

            except Carnet.DoesNotExist:
                details.append({
                    'annee': annee,
                    'semestre': semestre,
                    'part_sociale': None,
                    'part_lucrative': None,
                    'nombre_filleuls': 0,
                    'ancien_total_sociale': previous_total_sociale,
                    'ancien_total_lucrative': previous_total_lucrative,
                    'nouveau_total_sociale': Decimal('0.00'),
                    'nouveau_total_lucrative': Decimal('0.00'),
                    'total_sociale': previous_total_sociale,
                    'total_lucrative': previous_total_lucrative,
                    'assistance_joie_obtenue': Decimal('0.00'),
                    'assistance_joie_reste': Decimal('3.00'),
                    'assistance_detresse_obtenue': Decimal('0.00'),
                    'assistance_detresse_reste': Decimal('7.00'),
                })

    context = {
        'details': details,
        'association_user': utilisateur_connecte,
        'debut': debut,  # Passer l'année de début dans le contexte
    }
    return render(request, 'association/autre_detail.html', context)
@login_required
def lister_membres(request):
    membres = Membre.objects.all()
    return render(request, 'association/liste_membres.html', {'membres': membres})

@login_required
def creer_cotisation(request):
    if request.method == 'POST':
        form = CotisationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('association:liste_cotisations')
    else:
        form = CotisationForm()
    return render(request, 'association/creer_cotisation.html', {'form': form})

@login_required
def lister_cotisations(request):
    cotisations = Cotisation.objects.all()
    return render(request, 'association/liste_cotisations.html', {'cotisations': cotisations})

@login_required
def creer_penalite(request):
    if request.method == 'POST':
        form = PenaliteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('association:liste_penalites')
    else:
        form = PenaliteForm()
    return render(request, 'association/creer_penalite.html', {'form': form})

@login_required
def lister_penalites(request):
    penalites = Penalite.objects.all()
    return render(request, 'association/liste_penalites.html', {'penalites': penalites})

@login_required
def creer_demande_pret(request):
    if request.method == 'POST':
        form = DemandePretForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('association:liste_demandes_pret')
    else:
        form = DemandePretForm()
    return render(request, 'association/creer_demande_pret.html', {'form': form})

@login_required
def lister_demandes_pret(request):
    demandes = DemandePret.objects.all()
    return render(request, 'association/liste_demandes_pret.html', {'demandes': demandes})

@login_required
def creer_demande_assistance(request):
    if request.method == 'POST':
        form = DemandeAssistanceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('association:liste_demandes_assistance')
    else:
        form = DemandeAssistanceForm()
    return render(request, 'association/creer_demande_assistance.html', {'form': form})

@login_required
def lister_demandes_assistance(request):
    demandes = DemandeAssistance.objects.all()
    return render(request, 'association/liste_demandes_assistance.html', {'demandes': demandes})


def get_current_semester():
    # Fonction pour obtenir le semestre actuel (à adapter selon votre logique)
    current_month = timezone.now().month
    return 1 if current_month <= 6 else 2


def penalite_caisse(request):
    """
    Vue pour afficher les utilisateurs associés à une association spécifique,
    filtrés par montant d'adhésion et rôle exclu (comité).
    """
    # Récupérez l'association de l'utilisateur actuel
    association = request.user.association

    # Récupérez les utilisateurs correspondant aux critères
    users = AssociationUser.objects.filter(association=association).exclude(role='comite')

    # Récupérer l'année et le mois actuels
    current_year = timezone.now().year
    current_month = timezone.now().month
    semestre_actuel = get_current_semester()

    if request.method == "POST":
        error_messages = []  # Accumuler les erreurs

        # Traitement des pénalités
        for user in users:
            carnet, created = Carnet.objects.get_or_create(
                utilisateur=user,
                annee=current_year,
                semestre=semestre_actuel
            )

            # Vérifier si une pénalité a déjà été appliquée ce mois-ci
            lignes_cotisation = LigneCotisation.objects.filter(carnet=carnet)

            for ligne in lignes_cotisation:
                if ligne.date.month == current_month:
                    error_messages.append(f"Les pénalités pour {user.last_name} ont déjà été validées ce mois-ci.")
                    break  # Stoppe la boucle si une pénalité a déjà été appliquée

            if error_messages:
                continue  # Passe à l'utilisateur suivant si une pénalité est déjà enregistrée

            # Récupérer les utilisateurs sélectionnés via les cases à cocher
            selected_users_15min = request.POST.getlist('selected_users_15min')
            selected_users_30min = request.POST.getlist('selected_users_30min')
            selected_users_45min = request.POST.getlist('selected_users_45min')
            selected_users_60min = request.POST.getlist('selected_users_60min')
            selected_users_absence = request.POST.getlist('selected_users_absence')

            # Pénalités définies dans le template
            penalite_retard_15min = Decimal(request.POST.get('penalite_retard_15min'))
            penalite_retard_30min = Decimal(request.POST.get('penalite_retard_30min'))
            penalite_retard_45min = Decimal(request.POST.get('penalite_retard_45min'))
            penalite_retard_60min = Decimal(request.POST.get('penalite_retard_60min'))
            penalite_absence = Decimal(request.POST.get('penalite_absence'))

            penalite = Decimal(0)  # Initialisation de la pénalité

            # Mise à jour des pénalités pour les utilisateurs sélectionnés
            if str(user.id) in selected_users_15min:
                penalite += penalite_retard_15min
            if str(user.id) in selected_users_30min:
                penalite += penalite_retard_30min
            if str(user.id) in selected_users_45min:
                penalite += penalite_retard_45min
            if str(user.id) in selected_users_60min:
                penalite += penalite_retard_60min
            if str(user.id) in selected_users_absence:
                penalite += penalite_absence

            if penalite > 0:
                # Mise à jour du carnet avec la pénalité
                carnet.total_penalite += penalite
                carnet.save()

                # Enregistrer une ligne de cotisation
                LigneCotisation.objects.create(
                    carnet=carnet,
                    penalite=penalite,
                )

                user.save()

        # Si des erreurs ont été accumulées, les afficher et rediriger
        if error_messages:
            for error in error_messages:
                messages.error(request, error)
            return redirect('association:penalite_caisse')

        # Message de succès
        messages.success(request, "Les pénalités ont été enregistrées avec succès.")
        return redirect('association:penalite_caisse')

    # Si le formulaire est chargé, récupérer la liste des utilisateurs
    penalites = {
        'penalite_retard_15min': Decimal('100'),
        'penalite_retard_30min': Decimal('150'),
        'penalite_retard_45min': Decimal('200'),
        'penalite_retard_60min': Decimal('250'),
        'penalite_absence': Decimal('300'),
    }

    # Renvoyer les utilisateurs à la vue avec les pénalités définies
    return render(request, 'association/penalite_caisse.html', {
        'users': users,
        **penalites,
    })



def penalite_pret(request):
    """
       Vue pour gérer les pénalités en fonction des mois de retard et du montant net à rembourser.
       """
    association = request.user.association
    users = AssociationUser.objects.filter(association=association).exclude(role='comite')

    if request.method == "POST":
        # Récupérer les utilisateurs sélectionnés pour chaque période de retard
        selected_users_1mois = request.POST.getlist('selected_users_1mois')
        selected_users_2mois = request.POST.getlist('selected_users_2mois')
        selected_users_3mois = request.POST.getlist('selected_users_3mois')
        selected_users_4mois = request.POST.getlist('selected_users_4mois')

        # Coefficients de pénalité définis
        penalite_1mois = Decimal('0.05') * 1
        penalite_2mois = Decimal('0.05') * 2
        penalite_3mois = Decimal('0.05') * 3
        penalite_4mois = Decimal('0.05') * 4

        # Mise à jour des pénalités pour les utilisateurs sélectionnés
        for user in users:
            semestre_actuel = get_current_semester()
            carnet, created = Carnet.objects.get_or_create(
                utilisateur=user,
                annee=timezone.now().year,
                semestre=semestre_actuel
            )

            montant_total = carnet.montant_total_net_restant  # Supposez que ce champ existe
            penalite = Decimal(0)

            if str(user.id) in selected_users_1mois:
                penalite += montant_total * penalite_1mois
            if str(user.id) in selected_users_2mois:
                penalite += montant_total * penalite_2mois
            if str(user.id) in selected_users_3mois:
                penalite += montant_total * penalite_3mois
            if str(user.id) in selected_users_4mois:
                penalite += montant_total * penalite_4mois

            if penalite > 0:
                carnet.total_penalite += penalite
                carnet.save()

                LigneCotisation.objects.create(
                    carnet=carnet,
                    penalite=penalite,
                )

                user.save()
                print(f"Pénalité de {penalite} ajoutée pour {user.last_name}")

        messages.success(request, "Les pénalités ont été enregistrées avec succès.")
        return redirect('association:penalite_caisse')

    # Pénalités par mois
    penalites = {
        'penalite_1mois': Decimal('5'),
        'penalite_2mois': Decimal('10'),
        'penalite_3mois': Decimal('15'),
        'penalite_4mois': Decimal('20'),
    }
    return render(request, 'association/penalite_pret.html',{
        'users': users,
        **penalites,
    } )

def gestion_remboursements(request):
    """
    Gère les demandes de prêt et d'assistance en récupérant les messages complétés
    et en accordant les montants dans le carnet de l'utilisateur.
    """
    # Récupérer tous les messages complétés
    completed_messages = Message.objects.filter(is_completed=True, is_accorder=False)
    loan_messages = completed_messages.filter(subject="Demande de Pret")
    assistance_messages = completed_messages.filter(subject="Demande d’Assistance")

    # Récupérer les utilisateurs ayant des demandes de prêt et d'assistance
    users_with_loan_requests = AssociationUser.objects.filter(
        id__in=loan_messages.values('sender').distinct()
    )
    users_with_assistance_requests = AssociationUser.objects.filter(
        id__in=assistance_messages.values('sender').distinct()
    )

    if request.method == "POST":
        try:
            # Récupérer les données envoyées dans la requête POST
            data = json.loads(request.body)
            message_id = data.get('message_id')
            action_type = data.get('action_type')

            # Vérifier si les données nécessaires sont présentes
            if not message_id or not action_type:
                return JsonResponse({'success': False, 'message': "Données incomplètes."}, status=400)

            message = Message.objects.get(id=message_id)
            utilisateur = message.sender
            montant = Decimal(0)
            evenement = None
            duree_remboursement = 0
            interet = Decimal(0)

            if action_type == "pret":
                print("Contenu du message de prêt:", message.body)  # Impression du contenu du message
                # Utiliser des regex pour extraire les informations du corps du message
                montant_match = re.search(r'Un totale de ([\d,]+(?:\.\d{1,5})?) F CFA', message.body)
                evenement_match = re.search(r'Suite à un événement (\w+)', message.body)
                duree_match = re.search(r'Que je compte payer en (\d+) Mois', message.body)
                interet_match = re.search(r'Avec un intérêt de (\d+(\.\d{1,2})?)%', message.body)

                if montant_match:

                    montant_str =montant_match.group(1)
                    print("Montant extrait avant remplacement:", montant_str)  # Impression du montant extrait
                    montant_str = montant_str.replace(',', '')
                    print("Montant extrait après remplacement:", montant_str)  # Impression du montant après remplacement
                    montant = Decimal(montant_str)
                else:
                    montant = Decimal(0)

                if evenement_match:
                    evenement = evenement_match.group(1)
                else:
                    evenement = "Non spécifié"

                if duree_match:
                    duree_remboursement = int(duree_match.group(1))
                else:
                    duree_remboursement = 0

                if interet_match:
                    interet = Decimal(interet_match.group(1))
                else:
                    interet = Decimal(0)
                # Calculer le remboursement mensuel
                remboursement_mensuel = montant / duree_remboursement if duree_remboursement > 0 else montant

                # Effectuer les mises à jour dans une transaction atomique
                with transaction.atomic():
                    carnet, created = Carnet.objects.get_or_create(
                        utilisateur=utilisateur,
                        annee=timezone.now().year,
                        semestre=1 if timezone.now().month <= 6 else 2,
                    )
                    carnet.montant_total_pret_accorde += montant
                    carnet.pret_accorde = montant
                    message.is_accorder = True  # Mettre à jour is_accorder pour le message de prêt
                    message.save()
                    carnet.save()

                    # Enregistrer les paiements mensuels
                    for mois in range(1, duree_remboursement + 1):
                        payment = Payment(
                            user=utilisateur,
                            month=mois,
                            amount=remboursement_mensuel,
                            reste_a_payer=montant - remboursement_mensuel * mois,
                            is_paid=False,
                            payment_date=None
                        )
                        payment.save()

            elif action_type == "assistance":
                print("Contenu du message d'assistance:", message.body)  # Impression du contenu du message
                # Utiliser une regex pour extraire le montant du corps du message
                match = re.search(r'somme qui pourrait s\'élever à ([\d,]+(?:\.\d{1,5})?) F CFA', message.body)
                print("Résultat de l'expression régulière:", match)  # Impression du résultat de l'expression régulière
                if match:
                    montant_str = match.group(1)
                    print("Montant extrait avant remplacement:", montant_str)  # Impression du montant extrait
                    montant_str = montant_str.replace('.', '').replace(',', '.')
                    print("Montant extrait après remplacement:", montant_str)  # Impression du montant après remplacement
                else:
                    montant_str = "0"
                montant = Decimal(montant_str)
                print("Montant de l'assistance:", montant)  # Impression du montant
                match = re.search(r"Suite à un événement (\w+)", message.body)
                if match:
                    evenement = match.group(1)
                    print("Événement de l'assistance:", evenement)

                # Effectuer les mises à jour dans une transaction atomique
                with transaction.atomic():
                    carnet, created = Carnet.objects.get_or_create(
                        utilisateur=utilisateur,
                        annee=timezone.now().year,
                        semestre=1 if timezone.now().month <= 6 else 2,
                    )

                    # Traitement selon le type d'événement (heureux ou détresse)
                    if evenement == "Heureux":
                        carnet.assistance_joie_obtenue += 1
                        carnet.assistance_joie_reste -= 1
                    elif evenement == "Malheureux":
                        carnet.assistance_detresse_obtenue += 1
                        carnet.assistance_detresse_reste -= 1

                    carnet.montant_total_assistance_accordee += montant
                    carnet.assistance_accorde = montant
                    message.is_accorder = True  # Mettre à jour is_accorder pour le message d'assistance
                    message.save()
                    carnet.save()

            else:
                return JsonResponse({'success': False, 'message': "Type d'action invalide."}, status=400)

            return JsonResponse({'success': True, 'message': "Action effectuée avec succès.", 'montant': str(montant)})

        except Message.DoesNotExist:
            return JsonResponse({'success': False, 'message': "Message introuvable."}, status=404)
        except AssociationUser.DoesNotExist:
            return JsonResponse({'success': False, 'message': "Utilisateur introuvable."}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    # Récupérer les utilisateurs ayant des demandes de prêt et d'assistance pour affichage
    context = {
        'loan_messages': loan_messages,
        'assistance_messages': assistance_messages,
    }

    return render(request, 'association/gestion_remboursement.html', context)
def extract_amount_from_body(body):
    """ Fonction pour extraire un montant du corps du message """
    match = re.search(r'\d+', body)
    if match:
        # Utilisation de Decimal pour éviter les problèmes de précision
        return Decimal(match.group(0))
    else:
        # Logique d'erreur ou retour par défaut si aucun montant n'est trouvé
        return Decimal('0.00')
def valider_remboursement(request, remboursement_id):
    remboursement = get_object_or_404(RemboursementMensuel, id=remboursement_id)
    remboursement.est_valide = True
    remboursement.save()
    remboursement.appliquer_penalite()  # Appliquer la pénalité si nécessaire
    return redirect('association:gestion_remboursement')
@login_required
def loan_payments_view(request):
    if request.method == 'POST':
        try:
            print('Received POST request')
            data = json.loads(request.body)
            payment_id = data.get('payment_id')
            action = data.get('action')
            print(f'Payment ID: {payment_id}, Action: {action}')

            payment = Payment.objects.filter(id=payment_id).first()
            if not payment:
                print('Payment not found')
                return JsonResponse({'status': 'error', 'message': 'Payment not found'}, status=400)

            if action == 'rembourser':
                payment.is_paid = True
                payment.is_non_rembourser = False
                payment.payment_date = timezone.now().date()
                payment.save()
                print('Payment marked as paid')

                payments = Payment.objects.filter(user=payment.user, month__gte=payment.month).order_by('month')
                reste_a_payer = sum(p.amount for p in payments if not p.is_paid)
                for p in payments:
                    p.reste_a_payer = reste_a_payer
                    reste_a_payer -= p.amount
                    p.save()
                print('Updated remaining payments')

            elif action == 'non_rembourser':
                payment.is_paid = False
                payment.is_non_rembourser = True
                payment.save()
                print('Payment marked as not paid')

                current_month = timezone.now().month
                semestre = 1 if current_month <= 6 else 2
                sanction_semestrielle = payment.amount * Decimal(0.05)

                ligne_cotisations = LigneCotisation.objects.filter(carnet__utilisateur=payment.user, carnet__semestre=semestre)
                if ligne_cotisations.exists():
                    ligne_cotisation = ligne_cotisations.first()
                    ligne_cotisation.sanctions = sanction_semestrielle
                    ligne_cotisation.save()
                else:
                    carnet = Carnet.objects.filter(utilisateur=payment.user, semestre=semestre).first()
                    if not carnet:
                        carnet = Carnet.objects.create(
                            utilisateur=payment.user,
                            semestre=semestre,
                            total_sanctions=sanction_semestrielle
                        )
                    else:
                        carnet.total_sanctions += sanction_semestrielle
                        carnet.save()

                    LigneCotisation.objects.create(
                        carnet=carnet,
                        sanctions=sanction_semestrielle
                    )

                carnet = Carnet.objects.filter(utilisateur=payment.user, semestre=semestre).first()
                if carnet:
                    carnet.total_sanctions += sanction_semestrielle
                    carnet.save()

            print('Returning success response')
            return JsonResponse({
                'status': 'success',
                'is_paid': payment.is_paid,
                'payment_date': payment.payment_date,
                'reste_a_payer': payment.reste_a_payer
            })
        except json.JSONDecodeError:
            print('Invalid JSON format')
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON format'}, status=400)
        except Exception as e:
            print(f'Error: {str(e)}')
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    payments = Payment.objects.all()
    loans = {}

    for payment in payments:
        user = payment.user
        montant_pret = payment.amount
        reste_a_payer = payment.reste_a_payer

        loan_key = (user.id, montant_pret)

        if loan_key not in loans:
            loans[loan_key] = {
                'user': user,
                'duree': 0,
                'reste_a_payer': reste_a_payer,
                'payments': []
            }

        loans[loan_key]['payments'].append(payment)
        loans[loan_key]['duree'] += 1

    filtered_loans = [loan for loan in loans.values() if any(not payment.is_paid for payment in loan['payments'])]

    context = {
        'loans': filtered_loans,
    }
    return render(request, 'association/loan_payments.html', context)
@login_required
def completed_loans_view(request):
    messages = Message.objects.filter(is_completed=True, is_accorder=True, subject="Demande de Pret")
    completed_loans = []

    for message in messages:
        user = message.sender

        # Vérifier si tous les paiements de l'utilisateur sont remboursés
        if not Payment.objects.filter(user=user, is_paid=False).exists():
            body = message.body
            duree_match = re.search(r'Que je compte payer en (\d+) mois', body)
            total_match = re.search(r'Un total de (\d+(\.\d{1,4})?) F CFA', body)

            if duree_match and total_match:
                duree = int(duree_match.group(1))
                total_remboursement = Decimal(total_match.group(1))

                completed_loans.append({
                    'user': user,
                    'duree': duree,
                    'total_remboursement': total_remboursement,

                })

    context = {
        'completed_loans': completed_loans,
    }
    return render(request, 'association/completed_loans.html', context)
def comptabilite_view(request):
    # Calculs des totaux
    total_adhesions = AssociationUser.objects.aggregate(Sum('montant_adhesion'))['montant_adhesion__sum'] or 0

    total_penalites_caisse = Carnet.objects.aggregate(Sum('total_penalite'))['total_penalite__sum'] or 0

    total_sanctions = Carnet.objects.aggregate(Sum('total_sanctions'))['total_sanctions__sum'] or 0
    total_interet_pret= Comptabilite.objects.aggregate(Sum('interet'))['interet__sum'] or 0
    # Exemple de données additionnelles à calculer
    total_commissions_heureuses = 0  # Remplacez par votre logique
    total_commissions_malheureuses = 0  # Remplacez par votre logique

    # Total des entrées
    total_entrees = (
        total_adhesions +
        total_penalites_caisse +
        total_sanctions +
        total_commissions_heureuses +
        total_commissions_malheureuses +
        total_interet_pret  # Ajouté pour l'exemple de données additionnelles à calculer'
    )

    # Exemple pour les dépenses
    total_depenses = 0  # Calculez selon votre logique

    # Calcul du bilan
    bilan_total = total_entrees - total_depenses

    # Envoi des données au template
    context = {
        'total_adhesions': total_adhesions,
        'total_penalites_caisse': total_penalites_caisse,
        'total_sanctions': total_sanctions,
        'total_entrees': total_entrees,
        'total_depenses': total_depenses,
        'bilan_total': bilan_total,
        'total_interet_pret': total_interet_pret,  # Ajouté pour l'exemple de données additionnelles à calculer'
    }

    return render(request, 'association/comptabilite.html', context)
def send_welcome_sms(request):
    # Exemple de numéro international
    phone_number = '+22899855971'
    message = 'Bienvenue sur notre plateforme !'

    try:
        # Appel de la fonction pour envoyer un SMS
        sms_sid = send_sms(phone_number, message)
        return HttpResponse(f"SMS envoyé avec succès, SID: {sms_sid}")
    except ValueError as e:
        return HttpResponse(f"Erreur lors de l'envoi du SMS : {str(e)}")