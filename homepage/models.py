from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from authentication.models import CustomUser
class OeuvreSocialUserManager(BaseUserManager):
    """Manager pour gérer la création d'un utilisateur et d'un superutilisateur."""

    def create_user(self, email, username, password=None, **extra_fields):
        """Créer et retourner un utilisateur avec un email et un mot de passe."""
        if not email:
            raise ValueError('L\'email doit être fourni')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        """Créer et retourner un superutilisateur."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, username, password, **extra_fields)


class OeuvreSocialUser(AbstractBaseUser):
    """Modèle utilisateur personnalisé pour l'application Oeuvre Sociale."""

    ROLE_CHOICES = [
        ('SPON', 'Sponsor'),
        ('BIEN', 'Bienfaiteur'),
        ('TOR', 'Torpilleur'),
    ]

    email = models.EmailField(unique=True)  # Email unique pour chaque utilisateur
    username = models.CharField(max_length=150, unique=True)
    profile_picture = models.ImageField(upload_to='profile_picture/', blank=True, null=True)
    role = models.CharField(max_length=200, blank=True)  # Changement ici pour permettre plusieurs rôles (séparés par des virgules)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)  # Indique si l'utilisateur est actif
    is_staff = models.BooleanField(default=False)  # Indique si l'utilisateur a des droits administratifs
    is_superuser = models.BooleanField(default=False)  # Indique si l'utilisateur est un superutilisateur
    objects = OeuvreSocialUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # Champs requis lors de la création d'un utilisateur (en plus de l'email)

    def __str__(self):
        return self.username

    def get_roles(self):
        """Retourne la liste des rôles séparés par des virgules."""
        return self.role.split(',')

    def add_role(self, new_role):
        """Ajoute un nouveau rôle à l'utilisateur sans dupliquer."""
        if new_role not in self.get_roles():
            if self.role:
                self.role += ',' + new_role
            else:
                self.role = new_role
            self.save()

    def get_roles_display(self):
        """Retourne une version lisible des rôles."""
        if not self.role:
            return ""
        roles_list = [r.strip() for r in self.role.split(',')]
        mapping = dict(self.ROLE_CHOICES)
        display_list = [mapping.get(code, code) for code in roles_list]
        return ", ".join(display_list)

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'


class Projet(models.Model):
    """Modèle représentant un projet pour lequel des fonds sont récoltés."""

    ROLE_CHOICES = [
        ('DON', 'Donateur'),
        ('SPON', 'Sponsor'),
        ('BIEN', 'Bienfaiteur'),

    ]

    titre = models.CharField(max_length=255)
    description = models.TextField()
    montant_objectif = models.DecimalField(max_digits=12, decimal_places=2)  # Montant à atteindre
    montant_recolte = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # Montant déjà récolté
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()

    # Liens avec les utilisateurs (donateurs, sponsors, bienfaiteurs)
    donateurs = models.ManyToManyField('authentication.CustomUser', related_name='projets_donnes', blank=True)
    sponsors = models.ManyToManyField('OeuvreSocialUser', related_name='projets_sponsories', blank=True)
    bienfaiteurs = models.ManyToManyField('OeuvreSocialUser', related_name='projets_bienfaits', blank=True)


    def __str__(self):
            return self.titre

    def rester_a_sponsoriser(self):
        """Retourne le montant restant à récolter pour les sponsors."""
        return self.montant_objectif - self.montant_recolte

    def rester_a_donner(self):
        """Retourne le montant restant à récolter pour les donateurs."""
        return self.montant_objectif - self.montant_recolte

    class Meta:
        verbose_name = 'Projet'
        verbose_name_plural = 'Projets'
class Donation(models.Model):
    """Modèle représentant un don effectué pour un projet."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dons')
    projet = models.ForeignKey(Projet, on_delete=models.CASCADE, related_name='dons')
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    date_don = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Don de {self.montant} sur le projet {self.projet.titre} par {self.user.username}'

    class Meta:
        verbose_name = 'Donation'
        verbose_name_plural = 'Donations'
class Formation(models.Model):
    """Modèle représentant une formation liée à l'oeuvre sociale."""
    nom = models.CharField(max_length=100)
    periode_duree = models.CharField(max_length=100)
    date = models.DateField()
    heures = models.CharField(max_length=100)

    def __str__(self):
        return self.nom


class Transaction(models.Model):
    """Modèle représentant une transaction effectuée par un utilisateur."""
    TRANSACTION_TYPES = [
        ('DON', 'Donateur'),
        ('SPON', 'Sponsor'),
        ('BIEN', 'Bienfaiteur'),
    ]

    user = models.ForeignKey(OeuvreSocialUser, on_delete=models.CASCADE)  # Utilisateur qui effectue la transaction
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Montant de la transaction
    date = models.DateTimeField(auto_now_add=True)  # Date de la transaction
    description = models.TextField(blank=True, null=True)  # Description facultative
    projet = models.ForeignKey(Projet, on_delete=models.CASCADE, related_name='transactions')  # Lien vers le projet auquel appartient le don

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} CFA - {self.date.strftime('%Y-%m-%d %H:%M:%S')} pour {self.projet.titre}"

    class Meta:
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'


class DemandeSupport(models.Model):
    titre = models.CharField(max_length=255)
    description = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titre

