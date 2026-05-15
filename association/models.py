from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import json
import uuid
import re

class AssociationUserManager(BaseUserManager):
    def create_user_with_optional_email(self, email=None, password=None, **extra_fields):
        # Vérifier que le prénom et le nom de famille sont fournis
        if not extra_fields.get('first_name') or not extra_fields.get('last_name'):
            raise ValueError("Le prénom et le nom de famille doivent être renseignés")

        # Normaliser l'email si fourni
        if email:
            email = self.normalize_email(email)

        # Créer l'utilisateur en utilisant l'email (s'il est fourni) ou sans email
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_association_with_nom(self, nom, password=None, **extra_fields):
        if not nom:
            raise ValueError("Le nom de l'association est requis")
        association = self.model(nom=nom, **extra_fields)
        association.set_password(password)  # Hachage du mot de passe
        association.save(using=self._db)
        return association

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user_with_optional_email(email, password, **extra_fields)
def generate_uuid():
    return uuid.uuid4()
class Association(AbstractBaseUser):
    nom = models.CharField(max_length=255, unique=True)  # Assurez-vous que le nom soit unique
    description = models.TextField()
    adresse = models.CharField(max_length=255)
    gestion_cotisations = models.BooleanField(default=True)
    gestion_penalites = models.BooleanField(default=True)
    gestion_pret = models.BooleanField(default=True)
    gestion_assistance = models.BooleanField(default=True)
    logo = models.ImageField(upload_to='logos/',blank=True, null=True)
    assoc_uuid = models.UUIDField(default=generate_uuid, editable=False, unique=True, primary_key=True)

    objects = AssociationUserManager()

    USERNAME_FIELD = 'nom'
    REQUIRED_FIELDS = []  # Aucune exigence supplémentaire

    def __str__(self):
        return self.nom

    def has_minimum_committee_members(self):
        return self.members.filter(role='comite').count() >= 5
class AssociationUser(AbstractBaseUser):
    ROLE_CHOICES = [
        ('comite', 'Membre du Comité'),
        ('association', 'Membre de l\'Association'),
    ]
    TYPE_COMPTE_CHOICES = [
        (500, '500 FCFA'),
        (1000, '1000 FCFA'),
        (1500, '1500 FCFA'),
        (2000, '2000 FCFA'),
        (5000, '5000 FCFA'),
        (10000, '10000 FCFA'),
    ]
    TAILLE_CHEMISE_CHOICES = [
        ('XS', 'XS (Très Petit)'),
        ('S', 'S (Petit)'),
        ('M', 'M (Moyen)'),
        ('L', 'L (Grand)'),
        ('XL', 'XL (Très Grand)'),
        ('XXL', 'XXL (Très Très Grand)'),
    ]
    assocuser_uuid = models.UUIDField(default=generate_uuid, editable=False, unique=True)
    identifiant = models.IntegerField(unique=True, null=True, blank=True)
    email = models.EmailField(unique=True,null=True, blank=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    nationalite = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    sexe = models.CharField(max_length=10, blank=True)
    profession = models.CharField(max_length=100, blank=True)
    prefecture = models.CharField(max_length=100, blank=True)
    maison_non_loin_de = models.CharField(max_length=100, blank=True)
    adresse = models.CharField(max_length=255, blank=True)  # Champ pour l'adresse
    quartier = models.CharField(max_length=255, blank=True)  # Champ pour l'adresse
    contact = models.CharField(max_length=15, blank=True)  # Champ pour le contact
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='association')
    association = models.ForeignKey(Association, related_name='members', on_delete=models.CASCADE,default=1)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    photo_membre = models.ImageField(upload_to='photos_membres/', blank=True, null=True)
    nom_heritier = models.CharField(max_length=100, blank=True)
    prenom_heritier = models.CharField(max_length=100, blank=True)
    nationalite_heritier = models.CharField(max_length=100, blank=True)
    date_of_birth_heritier = models.DateField(null=True, blank=True)
    nompop = models.CharField(max_length=100, default='None')  # Ajouter le champ nompopulaire
    sexe_heritier = models.CharField(max_length=10, blank=True)
    profession_heritier = models.CharField(max_length=100, blank=True)
    prefecture_heritier = models.CharField(max_length=100, blank=True)
    maison_non_loin_de_heritier = models.CharField(max_length=100, blank=True)
    photo_membre_heritier = models.ImageField(upload_to='photos_membres/', blank=True, null=True)
    contact_heritier = models.CharField(max_length=15, blank=True)  # Champ pour le contact
    taille_chemise = models.CharField(
        max_length=3,
        choices=TAILLE_CHEMISE_CHOICES,
        null=True,
        blank=True,
        verbose_name="Taille de chemise"
    )

    taille_pied = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Pointure"
    )
    # ### Informations de cotisation et pénalités ###
    montant_adhesion =models.IntegerField(choices=TYPE_COMPTE_CHOICES, default=500)
    solde_cotisation_mensuelle = models.IntegerField( default=0)
    solde_objectif_general = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    solde_objectif_personnel = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # ### Informations sur les filleuls et les membres ###
    nombre_total_filleuls = models.IntegerField(default=0)
    nombre_total_filleuls_association = models.IntegerField(default=0)
    nombre_total_membres = models.IntegerField(default=0)
    parrain = models.ForeignKey(
        'self',  # Référence à soi-même pour un lien auto-référent
        on_delete=models.SET_NULL,  # Par exemple, si le parrain est supprimé, l’affilié ne sera pas supprimé
        null=True,  # Permet d'avoir des utilisateurs sans parrain
        blank=True,
        related_name="affiliés"  # Donne accès aux affiliés via l'attribut `parrain.affiliés.all()`
    )

    # ### Objectifs ###
    objectif_general = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    objectif_personnel_6_mois = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    date_limite_objectifs = models.DateField(default=timezone.now)
    dates_reunions = models.JSONField(default=list, blank=True)  # Liste des dates de réunions

    objects = AssociationUserManager()

    USERNAME_FIELD = 'identifiant'
    REQUIRED_FIELDS = ['first_name', 'last_name','adresse', 'contact']

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.identifiant}"
    def save(self, *args, **kwargs):
        # Vérifiez si un compte comité existe déjà pour cette association
        if self.role == 'comite' and self.pk is None:
            if AssociationUser.objects.filter(association=self.association, role='comite').exists():
                raise ValidationError(("Un compte comité existe déjà pour cette association."))

        # Remplir le champ identifiant avec l'id si l'objet est nouveau
        if not self.pk:  # Si l'objet n'a pas encore été enregistré
            super().save(*args, **kwargs)  # Sauvegarder d'abord pour générer l'ID
            self.identifiant = self.id  # Assignation de l'ID à identifiant

        super().save(*args, **kwargs)
    def deposit(self, amount):
        """Augmente le solde de l'utilisateur."""
        self.solde += amount
        self.save()

    def withdraw(self, amount):
        """Diminue le solde de l'utilisateur si fonds suffisants."""
        if self.solde < amount:
            raise ValidationError(_("Solde insuffisant"))
        self.solde -= amount
        self.save()

    def mettre_a_jour_solde_cotisation(self):
        """
        Met à jour le solde de cotisation mensuelle et le solde total.
        """
        self.solde_cotisation_mensuelle += self.montant_adhesion
        self.solde += self.montant_adhesion
        self.save()
    def est_cotisation_grisee(self):
        if self.date_derniere_cotisation:
            # Grise l'option si la dernière cotisation est dans le mois en cours
            return self.date_derniere_cotisation.month == timezone.now().month
        return False

    def get_donnees_mensuelles(self):
        try:
            return json.loads(self.donnees_mensuelles)
        except json.JSONDecodeError:
            return {}

    def set_donnees_mensuelles(self, donnees):
        self.donnees_mensuelles = json.dumps(donnees)
def validate_image(image):
    # Limite la taille de l’image à 5 MB
    max_size = 5 * 1024 * 1024  # 5 MB
    if image.size > max_size:
        raise ValidationError("L'image dépasse la taille maximale de 5 MB.")
    # Limite le format
    valid_formats = ['image/jpeg', 'image/png', 'image/gif']
    if image.file.content_type not in valid_formats:
        raise ValidationError("Format d'image non supporté. Formats acceptés : JPEG, PNG, GIF.")
class ComiteSession(models.Model):
    user = models.ForeignKey(AssociationUser, on_delete=models.CASCADE)  # Utilisez AssociationUser ici
    session_key = models.CharField(max_length=40)  # La clé de session unique
    session_start = models.DateTimeField(auto_now_add=True)  # Heure de début de session
    session_end = models.DateTimeField(null=True, blank=True)  # Heure de fin de session (null = session toujours ouverte)

    def __str__(self):
        return f"Session de {self.user.username} - {self.session_key}"
class Membre(models.Model):
    # Définir les rôles possibles du comité
    ROLES_CHOICES = [
        ('PRESIDENT', 'Président'),
        ('VICE_PRESIDENT', 'Vice-Président'),
        ('SECRETAIRE', 'Secrétaire'),
        ('TRESORIER', 'Trésorier'),
    ]

    # L'association à laquelle ce membre appartient
    association = models.ForeignKey(Association, on_delete=models.CASCADE)
    # Rôle du membre dans le comité
    role = models.CharField(max_length=50, choices=ROLES_CHOICES)
    # Informations de contact
    telephone = models.CharField(max_length=15,default=0)
    email = models.EmailField(default=0)
    # Autres informations importantes
    first_name = models.CharField(max_length=30,default=0)
    last_name = models.CharField(max_length=30,default=0)
    nationalite = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    sexe = models.CharField(max_length=10, blank=True)
    profession = models.CharField(max_length=100, blank=True)
    prefecture = models.CharField(max_length=100, blank=True)
    maison_non_loin_de = models.CharField(max_length=100, blank=True)
    adresse = models.CharField(max_length=255, null=True, blank=True)
    date_naissance = models.DateField(null=True, blank=True)
    # Vous pouvez ajouter d'autres champs selon vos besoins

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.get_role_display()}"


class Carnet(models.Model):
    utilisateur = models.ForeignKey(
        AssociationUser, on_delete=models.CASCADE, related_name="carnets"
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
class ObjectifSemestriel(models.Model):
    utilisateur = models.ForeignKey(AssociationUser, on_delete=models.CASCADE, related_name="objectifs_semestriels")
    semestre = models.PositiveSmallIntegerField(choices=[(1, 'Premier semestre'), (2, 'Deuxième semestre')])
    annee = models.PositiveIntegerField(default=timezone.now().year)
    objectif_general = models.PositiveIntegerField(default=0)
    solde_objectif_general = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    objectif_personnel_6_mois = models.PositiveIntegerField(default=0)
    solde_objectif_personnel = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    date_limite_objectifs = models.DateField(null=True, blank=True)
class Message(models.Model):
    sender = models.ForeignKey(AssociationUser, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(AssociationUser, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=100)
    body = models.TextField()
    rejet_motif = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('accepté', 'Accepté'), ('rejeté', 'Rejeté'), ('en attente', 'En attente')], default='en attente')
    is_grayed = models.BooleanField(default=False)  # Nouveau champ
    is_completed = models.BooleanField(default=False)  # Nouveau champ
    is_accorder = models.BooleanField(default=False)

    @property
    def objet(self):

        if "Demande d’Assistance" in self.subject:  # Apostrophe standard
            return 'assistance'
        elif "Demande de Pret" in self.subject:  # Apostrophe standard
            return 'pret'
        return 'autre'

    def get_body_data(self):
        """
        Cette méthode essaie de convertir le corps du message en JSON (ou dictionnaire) pour en extraire les données.
        """
        try:
            return json.loads(self.body)  # Tente de charger le JSON du corps du message
        except (json.JSONDecodeError, TypeError):
            return {}
    def get_duree_remboursement(self):
        # Utilisation d'une regex pour extraire la durée (par exemple "12 Mois")
        match = re.search(r'(\d+)\s*Mois', self.body)
        if match:
            return match.group(1)  # Renvoie la durée extraite
        return None

    def get_pret_montant(self):
        # Utilisation d'une regex pour extraire un montant (par exemple "100000 F CFA")
        match = re.search(r'(\d+(\.\d{1,2})?)\s*F CFA', self.body)
        if match:
            return match.group(1)  # Renvoie le montant extrait
        return None
    def get_interet(self):
        # Utilisation d'une regex pour extraire l'intérêt (par exemple "10%")
        match = re.search(r'(\d+)%', self.body)
        if match:
            return match.group(1)  # Renvoie l'intérêt extrait
        return None

    def get_assistance_details(self):
        """
        Cette méthode essaie d'extraire les détails de la demande d'assistance dans le body du message.
        Si le body contient des informations spécifiques au problème, elles sont retournées.
        """
        try:
            # Supposons que le body contienne une description structurée
            match = re.search(r'Description du problème: (.+)', self.body)
            if match:
                return match.group(1)  # Retourne la description du problème
            else:
                return "Aucune description trouvée"
        except Exception as e:
            return f"Erreur lors de l'extraction des détails: {str(e)}"
class Pret(models.Model):
    utilisateur = models.ForeignKey(AssociationUser, on_delete=models.CASCADE)  # L'utilisateur qui a pris le prêt
    montant = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # Montant total du prêt
    taux_interet = models.DecimalField(max_digits=5, decimal_places=2, default=0 ,null=True)  # Taux d'intérêt
    date_debut = models.DateField(default=timezone.now)  # Date de début du prêt
    duree_mois = models.PositiveIntegerField(null=True)  # Durée du remboursement en mois
    date_limite = models.DateField(null=True)  # Date limite de remboursement (calculée en fonction de la durée)
    statut = models.CharField(max_length=20, choices=[('en cours', 'En cours'), ('remboursé', 'Remboursé')],
                              default='en cours')

    @property
    def montant_total(self):
        """Calculer le montant total à rembourser avec les intérêts"""
        return self.montant + (self.montant * (self.taux_interet / 100))

    def __str__(self):
        return f"Prêt de {self.montant} F CFA pour {self.utilisateur}"

    def save(self, *args, **kwargs):
        """Calculer la date limite du prêt en fonction de la durée"""
        if not self.date_limite and self.duree_mois is not None:
            self.date_limite = self.date_debut.replace(year=self.date_debut.year + self.duree_mois // 12)
        super(Pret, self).save(*args, **kwargs)


class Payment(models.Model):
    user = models.ForeignKey(AssociationUser, on_delete=models.CASCADE, related_name='user_payment',default=1)
    month = models.IntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reste_a_payer= models.DecimalField(max_digits=10, decimal_places=2,default=0)
    is_paid = models.BooleanField(default=False)
    payment_date = models.DateField(null=True, blank=True)
    is_non_rembourser = models.BooleanField(default=False)  # Nouveau champ
    def remboursement_complet(self):
        # Vérifie si le paiement est complet (vous pouvez ajuster la logique selon vos besoins)
        return self.is_paid and self.montant >= self.total_remboursement


class Comptabilite(models.Model):
    user = models.ForeignKey('AssociationUser', on_delete=models.CASCADE)
    payment = models.ForeignKey('Payment', on_delete=models.CASCADE, related_name='comptabilites')
    montant_pret = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0))
    pourcentage_pret = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(0))
    interet = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0))
    total_remboursement = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0))
    date_enregistrement = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"Comptabilité de {self.user.username} pour le paiement {self.payment.id}"
