from django.contrib import admin
from .models import (AssociationUser, Association, Membre,
                     ObjectifSemestriel, Message, Pret, Payment, Comptabilite, Carnet,LigneCotisation)
from django.contrib.auth.hashers import make_password
from .forms import AssociationForm
from .forms import AssociationUserChangeForm, AssociationUserCreationForm
# Administration pour le modèle AssociationUser
@admin.register(AssociationUser)
class AssociationUserAdmin(admin.ModelAdmin):
    form = AssociationUserChangeForm
    add_form = AssociationUserCreationForm
    list_display = ('email', 'first_name', 'last_name','role','association', 'contact','adresse', 'is_staff', 'is_active', 'date_joined', 'identifiant')  # Champs à afficher dans la liste
    search_fields = ('email', 'first_name', 'last_name')  # Champs à rechercher dans l'admin
    list_filter = ('is_staff', 'is_active')  # Filtres pour la liste
    ordering = ('email',)  # Ordre de tri par défaut
    list_per_page = 25
    def save_model(self, request, obj, form, change):
        # Hachage du mot de passe si modifié
        if form.cleaned_data["password"]:
            obj.set_password(form.cleaned_data["password"])
        super().save_model(request, obj, form, change)
# Administration pour le modèle Association
@admin.register(Association)
class AssociationAdmin(admin.ModelAdmin):
    form = AssociationForm
    list_display = ('nom','logo', 'description', 'adresse', 'gestion_cotisations', 'gestion_penalites', 'gestion_pret', 'gestion_assistance')
    search_fields = ('nom',)  # Champs à rechercher dans l'admin
    ordering = ('nom',)  # Ordre de tri par défaut
    list_per_page = 25
# Administration pour le modèle Membre
@admin.register(Membre)
class MembreAdmin(admin.ModelAdmin):
    list_display = (
    'first_name', 'last_name', 'role', 'association', 'telephone', 'email', 'date_of_birth', 'profession')
    search_fields = ('first_name', 'last_name', 'role', 'email', 'association__nom')
    list_filter = ('association', 'role')  # Filtres pour la liste
    ordering = ('email',)  # Ordre de tri par défaut
    list_per_page = 25


# Pour le modèle ObjectifSemestriel
@admin.register(ObjectifSemestriel)
class ObjectifSemestrielAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'semestre', 'annee', 'objectif_general', 'solde_objectif_general',
                    'objectif_personnel_6_mois', 'solde_objectif_personnel', 'date_limite_objectifs')
    search_fields = ('utilisateur__username', 'utilisateur__email')
    list_filter = ('semestre', 'annee')
    ordering = ('-annee', '-semestre')


# Pour le modèle Message
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'subject', 'timestamp', 'status', 'is_grayed', 'is_completed',
                    'is_accorder', 'objet')
    search_fields = ('sender__username', 'recipient__username', 'subject', 'body')
    list_filter = ('status', 'is_grayed', 'is_completed', 'is_accorder')
    actions = ['mark_as_completed', 'mark_as_accepted', 'mark_as_rejected']

    # Actions personnalisées
    def mark_as_completed(self, request, queryset):
        queryset.update(is_completed=True)

    mark_as_completed.short_description = "Marquer comme complété"

    def mark_as_accepted(self, request, queryset):
        queryset.update(status='accepté')

    mark_as_accepted.short_description = "Marquer comme accepté"

    def mark_as_rejected(self, request, queryset):
        queryset.update(status='rejeté')

    mark_as_rejected.short_description = "Marquer comme rejeté"


# Pour le modèle Pret
@admin.register(Pret)
class PretAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'montant', 'taux_interet', 'date_debut', 'duree_mois', 'date_limite',
                    'statut', 'montant_total')
    search_fields = ('utilisateur__username', 'utilisateur__email')
    list_filter = ('statut', 'date_debut')
    ordering = ('-date_debut',)


# Pour le modèle Payment
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'month', 'amount', 'reste_a_payer', 'is_paid', 'payment_date', 'remboursement_complet')
    search_fields = ('user__username', 'user__email')
    list_filter = ('is_paid', 'payment_date')
    ordering = ('-payment_date',)

    # Méthode personnalisée pour vérifier le remboursement complet
    def remboursement_complet(self, obj):
        return obj.reste_a_payer <= 0 and obj.is_paid

    remboursement_complet.boolean = True
    remboursement_complet.short_description = "Remboursement complet"


# Pour le modèle Comptabilite
@admin.register(Comptabilite)
class ComptabiliteAdmin(admin.ModelAdmin):
    list_display = (
    'user', 'payment', 'montant_pret', 'pourcentage_pret', 'interet', 'total_remboursement', 'date_enregistrement')
    search_fields = ('user__username', 'payment__id')
    list_filter = ('date_enregistrement',)
    ordering = ('-date_enregistrement',)

@admin.register(Carnet)
class CarnetAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'annee', 'semestre', 'total_cotisation', 'total_penalite',
                    'total_sanctions', 'nombre_filleuls_semestre', 'interets', 'depenses_lucratives',
                    'dividendes', 'assistance_joie_obtenue', 'assistance_joie_reste',
                    'assistance_detresse_obtenue', 'assistance_detresse_reste',
                    'montant_total_pret_accorde', 'montant_total_assistance_accordee',
                    'assistance_accorde', 'pret_accorde', 'part_sociale', 'part_lucrative',
                    'total_sociale', 'total_lucrative')
    search_fields = ('utilisateur__username', 'utilisateur__email')
    list_filter = ('annee', 'semestre')
    ordering = ('-annee', '-semestre')

    # Ajoutez ici des actions ou des méthodes supplémentaires si nécessaire

    def montant_total(self, obj):
        return format_html('<strong>{}</strong>', obj.total_cotisation + obj.total_penalite + obj.total_sanctions)
    montant_total.short_description = 'Total général'

@admin.register(LigneCotisation)
class LigneCotisationAdmin(admin.ModelAdmin):
    list_display = ('id', 'carnet', 'date', 'cotisation', 'penalite', 'signature')
    list_filter = ('date', 'carnet')
    search_fields = ('carnet__nom', 'signature')
    ordering = ('-date',)