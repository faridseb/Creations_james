from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from .models import (CustomUser, Stage, Hierarchy, Wallet, Avatar,
Transaction, Referral, PaymentMethod, SecurityLog, AuditLog,SupportRequest,
    SiteSettings, Statistics, ContentPreferences)
from django.contrib.auth import get_user_model
from collections import deque
from django.contrib.auth.hashers import make_password
import logging
from .forms import ReferralForm,AdReferralForm


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    form = AdReferralForm
    model = CustomUser
    list_display = ('nom','prenom','email','nompop', 'username', 'nationalite', 'sexe', 'profession',
        'lieu_travail', 'ville', 'quartier', 'maison_non_loin_de',
        'contact', 'referrer', 'stage', 'user_avatar', 'avatar_color', 'date_of_birth',
        'preferred_theme', 'preferred_language', 'slot_partage',
        'profile', 'profile_picture','total_cases_filled_by_referrals', 'filled_slots','wallet_balance','referral_uuid')
    search_fields = ('email', 'username', 'nationalite', 'sexe', 'profession')
    list_filter = ('stage', 'nationalite', 'sexe')

    def save_model(self, request, obj, form, change):
        if not change:  # Si c'est un nouvel utilisateur
            password = form.cleaned_data.get('password')
            if password:
                obj.password = make_password(password)  # Hache le mot de passe
        super().save_model(request, obj, form, change)  # Appel à la méthode parent pour sauvegarder


@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    class StageAdmin(admin.ModelAdmin):
        list_display = (
     'current_stage', 'name','reward', 'get_reward','cases_filled','completed'
        )
        list_filter = ('completed', 'current_stage')  # Ajoutez des filtres pour faciliter la recherche
        search_fields = ('name', 'user__username')  # Permet de rechercher par nom de stage et nom d'utilisateur
        ordering = ('-current_stage',)  # Trie par stade actuel en ordre décroissant
        readonly_fields = ('user',)
    def get_reward(self, obj):
        return obj.reward  # Assurez-vous que reward est un attribut ou une méthode de Stage
    get_reward.short_description = 'Reward'  # Titre du champ dans l'admin

class HierarchyInline(admin.TabularInline):
    model = Hierarchy
    fk_name = 'stage'
    extra = 0

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance','points_balance')
    search_fields = ('user__email',)

@admin.register(Avatar)
class AvatarAdmin(admin.ModelAdmin):
    list_display = ( 'image', 'color')
    search_fields = ('user__email',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'timestamp','created_at')
    search_fields = ('user__email', 'amount')

@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = (
        'referrer', 'referred', 'stage','stage_completed', 'referred_user',
        'date_joined', 'total_slots', 'used_slots', 'position',
        'reward_amount', 'reward_paid', 'slot_partage', 'filled_slots','is_confirmed'
    )
    search_fields = ('referrer__email', 'referred__email', 'referred_user__email')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('referral_tree/', self.admin_site.admin_view(self.referral_tree_view), name='referral_tree'),
            path('referral_tree/<int:stage>/', self.admin_site.admin_view(self.referral_tree_stage_view),
                 name='referral_tree_stage'),
        ]
        return custom_urls + urls

    def referral_tree_view(self, request):
        num_lignes = 20
        rows = []
        for i in range(num_lignes):
            if i == 0:
                num_cases = 1
            else:
                num_cases = 10 + (i - 1) * 9
            rows.append([None] * num_cases)

        # Obtenir le premier utilisateur non-admin pour la première ligne
        User = get_user_model()
        first_user = User.objects.exclude(is_superuser=True).order_by('date_joined').first()

        if first_user:
            rows[0][0] = first_user

        # Obtenir tous les utilisateurs et les trier par date d'inscription
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

        for referral in referrals:
            user = referral.referred
            referrer = get_referrer(user)
            if referrer:
                referrer_row_index, referrer_index = find_referrer_index(referrer)
                if referrer_row_index is None or referrer_index is None:
                    continue
            else:
                referrer_row_index, referrer_index = 0, 0

            placed = False
            for row_index in range(referrer_row_index + 1, len(rows)):
                segment_start = referrer_index
                segment_end = min(segment_start + 10, len(rows[row_index]))

                for col_index in range(segment_start, segment_end):
                    if rows[row_index][col_index] is None:
                        rows[row_index][col_index] = user
                        placed = True
                        break
                if placed:
                    break

            if not placed:
                print(f"No empty slot found for {user}")

        context = {
            'rows': rows,
        }

        return render(request, 'admin/referral_tree.html', context)

    def generate_tree_structure(self, stage):
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

        num_lignes = max_lines.get(stage, 10)  # Nombre de lignes pour le stade donné
        rows = []

        # Initialiser les lignes
        for i in range(num_lignes):
            if i == 0:
                num_cases = 1
            else:
                num_cases = 10 + (i - 1) * 9
            rows.append([None] * num_cases)

        return rows

    def place_user_in_stage_tree(self, rows, user):
        """
        Place un utilisateur dans l'arbre du stade en fonction de la présence du parrain.

        :param rows: Liste de listes représentant les lignes et les colonnes dans l'arbre.
        :param user: L'utilisateur à placer.
        """
        User = get_user_model()

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

        # Si le parrain n'est pas trouvé, chercher le grand parrain
        grand_sponsor = None
        if sponsor:
            try:
                grand_referral = Referral.objects.get(referred=sponsor)
                grand_sponsor = grand_referral.referrer
            except Referral.DoesNotExist:
                grand_sponsor = None

        if grand_sponsor:
            # Répéter la logique de placement pour le grand parrain
            grand_sponsor_position = None
            for row_index, row in enumerate(rows):
                if grand_sponsor in row:
                    grand_sponsor_position = (row_index, row.index(grand_sponsor))
                    break

            if grand_sponsor_position:
                grand_sponsor_row_index, grand_sponsor_col_index = grand_sponsor_position
                start_row_index = grand_sponsor_row_index + 1

                for row_index in range(start_row_index, len(rows)):
                    row = rows[row_index]
                    start_col_index = grand_sponsor_col_index if row_index == start_row_index else 0

                    for col_index in range(start_col_index, min(start_col_index + 10, len(row))):
                        if row[col_index] is None:
                            row[col_index] = user
                            return

        # Chercher le parrain de secours (james@gmail.com)
        try:
            backup_sponsor = User.objects.get(email='james@gmail.com')
            backup_sponsor_position = None
            for row_index, row in enumerate(rows):
                if backup_sponsor in row:
                    backup_sponsor_position = (row_index, row.index(backup_sponsor))
                    break

            if backup_sponsor_position:
                backup_sponsor_row_index, backup_sponsor_col_index = backup_sponsor_position
                start_row_index = backup_sponsor_row_index + 1

                for row_index in range(start_row_index, len(rows)):
                    row = rows[row_index]
                    start_col_index = backup_sponsor_col_index if row_index == start_row_index else 0

                    for col_index in range(start_col_index, min(start_col_index + 10, len(row))):
                        if row[col_index] is None:
                            row[col_index] = user
                            return
        except User.DoesNotExist:
            pass  # L'utilisateur avec l'email james@gmail.com n'existe pas

        # Si aucune des recherches précédentes n'a trouvé une place
        # Placer l'utilisateur dans le premier slot vide disponible
        for row in rows:
            for col_index, slot in enumerate(row):
                if slot is None:
                    row[col_index] = user
                    return
    def referral_tree_stage_view(self, request, stage):
        rows = self.generate_tree_structure(stage)
        # Le nombre total de slots remplis requis pour chaque stade
        total_filled_slots = 20 * (stage - 1)

        if stage > 1:
            # Filtrer les utilisateurs du stade précédent ayant le nombre de filled_slots requis

            referrals_with_filled_slot = Referral.objects.filter(filled_slots__gte=total_filled_slots)
            for referral in referrals_with_filled_slot:
                user = referral.referred_user
                if user:
                    # Trouver l'emplacement pour cet utilisateur dans l'arbre du stade actuel
                    self.place_user_in_stage_tree(rows, user)

        template_name = f'admin/referral_tree_stage_{stage}.html'
        return render(request, template_name, {'rows': rows})

        return render(request, 'admin/referral_tree_stage.html', context)
@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('user', 'method_name', 'method_type', 'account_number', 'is_active', 'date', 'confirmed')
    search_fields = ('user__email', 'method_name')

@admin.register(SecurityLog)
class SecurityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'timestamp')
    search_fields = ('user__email', 'action')

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'timestamp')
    search_fields = ('user__email', 'action')

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('key', 'value')
    search_fields = ('key',)

@admin.register(Statistics)
class StatisticsAdmin(admin.ModelAdmin):
    list_display = ('key', 'value')
    search_fields = ('key',)

@admin.register(ContentPreferences)
class ContentPreferencesAdmin(admin.ModelAdmin):
    list_display = ('user', 'receive_newsletters', 'receive_promotions')
    search_fields = ('user__email',)
@admin.register(SupportRequest)
class SupportRequestAdmin(admin.ModelAdmin):
    list_display = ('sujet', 'user', 'date_creation')
    list_filter = ('date_creation',)
    search_fields = ('sujet', 'user__username', 'message')