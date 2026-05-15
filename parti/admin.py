from django.contrib import admin
from .models import PartiUser, Parti,Carnet,LigneCotisation
from .forms import PartiSignupForm
@admin.register(PartiUser)
class PartiUserAdmin(admin.ModelAdmin):
    form = PartiSignupForm
    model = PartiUser
    list_display = ('username', 'email', 'party_name', 'role_in_party', 'membership_start_date', 'contribution_amount', 'is_active', 'is_admin')  # Champs à afficher dans la liste
    search_fields = ('username', 'email', 'party_name')  # Champs à rechercher dans l'admin
    list_filter = ('is_active', 'is_admin', 'party_name')  # Filtres pour la liste
    ordering = ('username',)  # Ordre de tri par défaut

@admin.register(Parti)
class PartiAdmin(admin.ModelAdmin):
    list_display = ('nom',)  # Champs à afficher dans la liste
    search_fields = ('nom',)  # Champs à rechercher dans l'admin
    ordering = ('nom',)  # Ordre de tri par défaut
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