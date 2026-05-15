from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group, Permission
from avatar.models import Avatar
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField
User = settings.AUTH_USER_MODEL
import uuid
class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    points_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Solde en points

    def __str__(self):
        return f"{self.user.username}'s Wallet"
    def add_funds(self, amount):
        """Ajoute des fonds au portefeuille."""
        self.wallet_balance += amount
        self.save()
    def withdraw_funds(self, amount):
        """Retire des fonds du portefeuille."""
        if amount > 0 and self.balance >= amount:
            self.balance -= amount
            self.save()
            return True
        return False

    def deposit_money(self, amount_fcfa):
        # Convertir l'argent en points et mettre à jour le portefeuille
        conversion_rate = 10  # Exemple : 1 point = 10 FCFA
        points_earned = amount_fcfa / conversion_rate
        self.wallet_balance += amount_fcfa
        self.points_balance += points_earned
        self.save()

    def add_points(self, points):
        # Convertir les points en argent et mettre à jour le portefeuille
        conversion_rate = 10  # Exemple : 1 point = 10 FCFA
        amount_fcfa = points * conversion_rate
        self.points_balance += points
        self.wallet_balance += amount_fcfa
        self.save()

class CustomUserManager(BaseUserManager):
    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError('Le nom d\'utilisateur doit être fourni.')
        if not email:
            raise ValueError('L\'adresse email doit être fournie.')

        email = self.normalize_email(email)  # Normaliser l'email
        user = self.model(username=username, email=email, **extra_fields)  # Créer un nouvel utilisateur
        user.set_password(password)  # Définir le mot de passe
        user.save(using=self._db)  # Sauvegarder l'utilisateur dans la base de données
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(username, email, password, **extra_fields)

def generate_uuid():
    return uuid.uuid4()
class CustomUser(AbstractUser):
    STAGE_CHOICES = {
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
    email = models.EmailField(unique=False)  # email non unique
    username = models.CharField(max_length=150, unique=True)  # username unique
    nom = models.CharField(max_length=100)  # Ajouter le champ nom
    prenom = models.CharField(max_length=100)  # Ajouter le champ prénom
    nompop = models.CharField(max_length=100, default='None')  # Ajouter le champ nompopulaire
    nationalite = CountryField(blank_label='(select country)', null=True, blank=True)
    sexe = models.CharField(max_length=10, blank=True)
    profession = models.CharField(max_length=100, blank=True)
    lieu_travail = models.CharField(max_length=100, blank=True)
    country = CountryField(blank_label='(select country)', null=True, blank=True)
    ville = models.CharField(max_length=100, blank=True)
    quartier = models.CharField(max_length=100, blank=True)
    maison_non_loin_de = models.CharField(max_length=100, blank=True)
    contact = PhoneNumberField(blank=True, null=True, region="TG")
    referrer = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    stage = models.IntegerField(default=1)
    user_avatar = models.OneToOneField('Avatar', on_delete=models.SET_NULL, null=True, blank=True, related_name='user_profile')
    avatar_color = models.CharField(max_length=20, blank=True, default='blue')
    date_of_birth = models.DateField(null=True, blank=True)
    preferred_theme = models.CharField(max_length=50, default='light')
    preferred_language = models.CharField(max_length=20, default='fr')
    slot_partage = models.IntegerField(default=0)
    filled_slots = models.IntegerField(default=0)  # Si ce champ existe
    date_joined = models.DateTimeField(default=timezone.now)
    profile = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(upload_to='profile_picture/', blank=True, null=True)
    total_cases_filled_by_referrals = models.IntegerField(default=0)
    avatar_image = models.ImageField(upload_to='avatars/', null=True, blank=True,default='avatars/stages/stage1_avatar.jpeg')
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    is_confirmed = models.BooleanField(default=False)
    is_donateur = models.BooleanField(default=False)
    referral_uuid = models.UUIDField(default=generate_uuid, unique=True, editable=False)
    EMAIL_FIELD = 'email'  # Utilisation de l'email comme champ secondaire si nécessaire
    USERNAME_FIELD = 'username'  # Utilisation de 'username' pour l'authentification
    REQUIRED_FIELDS = ['email']  # 'username' est déjà requis par défaut

    objects = CustomUserManager()

    def get_stage_name(self):
        """Retourne le nom du stage correspondant au numéro."""
        return self.STAGE_CHOICES.get(self.stage, "Inconnu")

    def get_full_name(self):
        """Retourne le nom complet de l'utilisateur."""
        return f"{self.nom} {self.prenom}".strip() if self.nom and self.prenom else self.username

    def get_short_name(self):
        """Retourne le nom court de l'utilisateur."""
        return self.nom if self.nom else self.username

    def __str__(self):
        """Retourne une représentation textuelle de l'utilisateur."""
        return f"{self.username} - {self.get_stage_name()}"

    def save(self, *args, **kwargs):
        # Si l'utilisateur n'a pas d'avatar, créez-en un par défaut
        if not self.user_avatar:
            avatar_color = self.avatar_color  # Vous pouvez avoir une autre logique pour la couleur
            avatar = Avatar.objects.create(color=avatar_color)  # Créez un avatar avec cette couleur
            self.user_avatar = avatar  # Assignez l'avatar à l'utilisateur

        super().save(*args, **kwargs)  # Appelez la méthode save() du parent pour enregistrer l'utilisateur

    def get_profile_picture_url(self):
        if self.profile_picture:
            return self.profile_picture.url
        return '/static/images/default.jpg'  # Une image par défaut si aucun avatar n'est défini

class Stage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='stages', null=True)  # Champ non nullable
    current_stage = models.IntegerField(default=0)
    name = models.CharField(max_length=255)
    reward = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_slots = models.IntegerField(default=0)
    required_referrals = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)
    avatar_image = models.ImageField(upload_to='avatars/stages/', null=True, blank=True)

    def __str__(self):
        return self.name

    def check_and_update_stage(self):
        referrals_count = self.user.referrals_received.filter(stage_completed=True).count()
        if referrals_count >= self.referrals_required and not self.completed:
            self.current_stage += 1
            self.completed = True
            self.save()

    def get_reward(self):
        return self.reward

    @staticmethod
    def calculate_reward(stage_number):
        rewards = {
            1: 1500,
            2: 5100,
            3: 15300,
            4: 45900,
            5: 137700,
            6: 413100,
            7: 1229300,
            8: 3717700,
            9: 11133700,
            10: 33461100
        }
        return rewards.get(stage_number, 0)

class Avatar(models.Model):
    image = models.ImageField(upload_to='avatars/', default='avatars/OIP(7).jpeg')
    color = models.CharField(max_length=7, default="#000000")

    def save(self, *args, **kwargs):
        # Logic to update image based on color or other attributes
        super().save(*args, **kwargs)

class Transaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(default=timezone.now) # Renamed from 'timestamp'
    reason = models.CharField(max_length=255, null=True, blank=True)
    is_successful = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.user.email} - {self.amount}"

class Referral(models.Model):
    referrer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='referrals_given')
    referred = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='referrals_received')
    referred_user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='referred',
                                         null=True, blank=True)
    date_joined = models.DateTimeField(default=timezone.now)
    stage = models.IntegerField(default=1)
    stage_completed = models.BooleanField(default=False)
    reward_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    reward_paid = models.BooleanField(default=False)
    slot_partage = models.BooleanField(default=False)
    total_slots = models.IntegerField(default=0)
    used_slots = models.IntegerField(default=0)
    position = models.IntegerField(default=0)
    filled_slots = models.IntegerField(default=0)
    is_confirmed = models.BooleanField(default=False)
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(used_slots__lte=models.F('total_slots')),
                name='used_slots_lte_total_slots'
            )
        ]

    def __str__(self):
        return f"{self.referrer.username} referred {self.referred.username} on {self.date_joined}"

    def is_filled(self):
        """Vérifie si les places sous le parrain sont remplies."""
        total_filled = Referral.objects.filter(referrer=self.referrer).count()
        return total_filled >= self.total_slots

    def update_stage(self):
        """Mise à jour du stade si les conditions sont remplies."""
        if self.is_filled():
            user = self.referrer
            current_stage = user.stage
            next_stage = Stage.objects.filter(id=current_stage + 1).first()
            if next_stage:
                user.stage = next_stage
                user.save()
                # Enregistrement de la récompense
                self.process_rewards(user, next_stage)

    def process_rewards(self, user, next_stage):
        """Gère les récompenses pour l'utilisateur et le grand parrain."""
        cash_register = CashRegister.objects.first()  # Assurez-vous que vous avez une seule instance ou gérez cela autrement
        reward_amount = next_stage.calculate_reward(user.stage)
        grand_sponsor_reward = reward_amount / 2

        # Récompense pour le parrain
        if cash_register:
            if cash_register.total_amount >= reward_amount:
                cash_register.total_amount -= reward_amount
                cash_register.save()
                user.wallet.add_funds(reward_amount)

                # Récompense pour le grand parrain
                grand_sponsor = user.referrer
                if grand_sponsor.wallet:
                    grand_sponsor.wallet.add_funds(grand_sponsor_reward)

class PaymentMethod(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    method_name = models.CharField(max_length=50)
    method_type = models.CharField(max_length=20)
    account_number = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    date = models.DateTimeField(default=timezone.now)
    confirmed = models.BooleanField(default=False)
    is_successful = models.BooleanField(default=False)
    def __str__(self):
        return f"Payment of {self.amount} FCFA by {self.user.username} - {'Successful' if self.is_successful else 'Failed'}"

class SecurityLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.action}"

class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.email} - {self.action}"


class SiteSettings(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()

    def __str__(self):
        return self.key


class Statistics(models.Model):
    key = models.CharField(max_length=100)
    value = models.IntegerField(default=0)

    def __str__(self):
        return self.key


class ContentPreferences(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    receive_newsletters = models.BooleanField(default=True)
    receive_promotions = models.BooleanField(default=False)

    def __str__(self):
        return f"Content Preferences for {self.user.username}"


class Hierarchy(models.Model):
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE, related_name='hierarchies')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    level = models.IntegerField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    def __str__(self):
        return f"{self.user.username} - Level {self.level}"


class CashRegister(models.Model):
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Solde total: {self.total_amount}"

    def add_funds(self, amount):
        """Ajoute des fonds au registre de caisse."""
        if amount > 0:
            self.total_amount += amount
            self.save()

    def withdraw_funds(self, amount):
        """Retire des fonds du registre de caisse."""
        if amount > 0 and self.total_amount >= amount:
            self.total_amount -= amount
            self.save()
            return True
        return False

class Notification(models.Model):
    # Génère un UUID unique pour chaque notification
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)  # Ajoutez ce champ
    def __str__(self):
        return f'Notification for {self.user.username}: {self.message}'
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    stage = models.ForeignKey(Stage, on_delete=models.SET_NULL, null=True)
    filled_slots = models.IntegerField(default=0)  # Nombre de slots remplis
class SupportRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    sujet = models.CharField(max_length=255)
    message = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sujet} - {self.user.username}"
class Retrait(models.Model):
    STATUTS = [
        ('EN_ATTENTE', 'En attente'),
        ('SUCCES', 'Succès'),
        ('ECHEC', 'Échec'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    montant = models.PositiveIntegerField()
    numero = models.CharField(max_length=20)
    operateur = models.CharField(max_length=20, choices=[("T-MONEY", "TMoney"), ("FLOOZ", "Flooz")])
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    statut = models.CharField(max_length=20, choices=STATUTS, default='EN_ATTENTE')
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.montant} FCFA - {self.operateur}"
