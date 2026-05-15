from django.db import models
from django.contrib.auth.models import AbstractUser,Group, Permission
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils.timezone import now
from django.utils import timezone
from decimal import Decimal


class PartiUserManager(BaseUserManager):
    def create_user(self, email, username, password=None):
        if not email:
            raise ValueError("L'email doit être fourni")
        email = self.normalize_email(email)
        user = self.model(email=email, username=username)
        user.set_password(password)  # Utilise set_password pour hacher le mot de passe
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None):
        user = self.create_user(email, username, password)
        user.is_admin = True
        user.is_staff = True  # Ajout de la propriété is_staff pour permettre l'accès à l'admin
        user.is_superuser = True  # Ajout de la propriété is_superuser pour définir un superutilisateur
        user.save(using=self._db)
        return user

class PartiUser(AbstractBaseUser):  # Utilise AbstractBaseUser pour gérer l'authentification
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, blank=True)
    party_name = models.CharField(max_length=255, blank=True)  # Nom du parti auquel appartient l'utilisateur
    role_in_party = models.CharField(max_length=100, blank=True)  # Rôle de l'utilisateur au sein du parti
    membership_start_date = models.DateField(null=True, blank=True)  # Date d'adhésion au parti
    contribution_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Montant des cotisations

    is_active = models.BooleanField(default=True)  # Champ pour gérer l'activation du compte
    is_admin = models.BooleanField(default=False)  # Champ pour les utilisateurs admins
    is_staff = models.BooleanField(default=False)  # Champ pour les utilisateurs staff
    is_superuser = models.BooleanField(default=False)  # Super utilisateur pour l'admin

    objects = PartiUserManager()

    USERNAME_FIELD = 'email'  # Utilise l'email pour l'authentification
    REQUIRED_FIELDS = ['username']  # Autres champs requis pour la création de l'utilisateur

    def __str__(self):
        return f"{self.username} ({self.email})"

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin
class Parti(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField()
    # Ajoutez d'autres champs nécessaires

    def __str__(self):
        return self.nom
class Payment(models.Model):
    user = models.ForeignKey(
        PartiUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="XOF")
    payment_method = models.CharField(max_length=50, choices=[
        ("stripe", "Stripe"),
        ("paypal", "PayPal"),
        ("paygate", "PayGate"),
    ])
    reference = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=[
        ("pending", "En attente"),
        ("completed", "Réussi"),
        ("failed", "Échoué"),
    ], default="pending")
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    return_url = models.URLField()  # URL de redirection après paiement

    def __str__(self):
        return f"{self.user} - {self.amount} {self.currency} ({self.status})"
class Carnet(models.Model):
    utilisateur = models.ForeignKey(
        PartiUser, on_delete=models.CASCADE, related_name="carnets"
    )
    annee = models.PositiveIntegerField(default=timezone.now().year)
    semestre = models.PositiveSmallIntegerField(
        choices=[(1, 'Premier semestre'), (2, 'Deuxième semestre')], default=1
    )
    total_cotisation = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_penalite = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_sanctions = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    nombre_filleuls_semestre = models.IntegerField(default=0)
    interets = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    depenses_lucratives = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    dividendes = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    assistance_joie_obtenue = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    assistance_joie_reste = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('3.00'))
    assistance_detresse_obtenue = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    assistance_detresse_reste = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('7.00'))
    montant_total_pret_accorde = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    montant_total_assistance_accordee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    assistance_accorde = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    pret_accorde = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    part_sociale = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    part_lucrative = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_sociale = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_lucrative = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    def __str__(self):
        return f"{self.utilisateur} - {self.annee} - Semestre {self.semestre}"

class LigneCotisation(models.Model):
    carnet = models.ForeignKey(
        Carnet, on_delete=models.CASCADE, related_name="lignes"
    )
    date = models.DateField(default=timezone.now)
    cotisation = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    penalite = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    sanctions = models.TextField(blank=True, null=True)
    signature = models.CharField(max_length=255, blank=True, null=True)


    def __str__(self):
        return f"{self.carnet} - {self.date}"