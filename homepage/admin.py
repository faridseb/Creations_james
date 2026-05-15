from django.contrib import admin
from .models import OeuvreSocialUser, Projet, Formation,Transaction
from .forms import UserRegistrationForm
# Enregistrement du modèle OeuvreSocialUser dans l'admin
class OeuvreSocialUserAdmin(admin.ModelAdmin):
    form = UserRegistrationForm
    model = OeuvreSocialUser
    list_display = ('email', 'username', 'role', 'first_name', 'last_name', 'date_joined','profile_picture', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('date_joined',)
    fieldsets = (
        ('Informations principales', {'fields': ('email', 'username', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )

    add_fieldsets = (
        ('Créer un nouvel utilisateur', {
            'classes': ('wide',),
            'fields': ('email', 'username', 'role', 'password1', 'password2','profile_picture'),
        }),
    )

    def get_role_display(self, obj):
        return obj.get_role_display()  # Affiche 'Donateur' au lieu de 'DON'

    get_role_display.short_description = "Rôle"  # Change le titre dans l'admin

admin.site.register(OeuvreSocialUser, OeuvreSocialUserAdmin)


# Enregistrement des autres modèles dans l'admin

class ProjetAdmin(admin.ModelAdmin):
    list_display = ('titre', 'montant_objectif', 'montant_recolte', 'date_debut', 'date_fin',
                    'afficher_donateurs', 'afficher_sponsors', 'afficher_bienfaiteurs')
    list_filter = ('date_debut', 'date_fin')
    search_fields = ('titre', 'description')
    ordering = ('date_debut',)

    def afficher_donateurs(self, obj):
        return ", ".join([user.username for user in obj.donateurs.all()]) if obj.donateurs.exists() else "Aucun"

    def afficher_sponsors(self, obj):
        return ", ".join([user.username for user in obj.sponsors.all()]) if obj.sponsors.exists() else "Aucun"

    def afficher_bienfaiteurs(self, obj):
        return ", ".join([user.username for user in obj.bienfaiteurs.all()]) if obj.bienfaiteurs.exists() else "Aucun"

    afficher_donateurs.short_description = "Donateurs"
    afficher_sponsors.short_description = "Sponsors"
    afficher_bienfaiteurs.short_description = "Bienfaiteurs"


admin.site.register(Projet, ProjetAdmin)


class FormationAdmin(admin.ModelAdmin):
    list_display = ('nom', 'periode_duree', 'date', 'heures')
    list_filter = ('date',)
    search_fields = ('nom',)
    ordering = ('date',)

admin.site.register(Formation, FormationAdmin)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'transaction_type', 'amount', 'date', 'projet')
    list_filter = ('transaction_type', 'date')
    search_fields = ('user__email', 'projet__titre', 'transaction_type')
    ordering = ('date',)

admin.site.register(Transaction, TransactionAdmin)
