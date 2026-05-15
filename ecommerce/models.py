from django.db import models
from django.utils import timezone
from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class EcommerceUserManager(BaseUserManager):
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
class EcommerceUser(AbstractBaseUser):  # Hérite de models.Model
    # Lien vers CustomUser
    email = models.EmailField(unique=False)  # email non unique
    username = models.CharField(max_length=150, unique=True)  # username unique
    shipping_address = models.CharField(max_length=255, blank=True)
    billing_address = models.CharField(max_length=255, blank=True)
    loyalty_points = models.IntegerField(default=0)  # Points de fidélité spécifiques à l'e-commerce
    preferred_payment_method = models.CharField(max_length=50, blank=True)  # Moyen de paiement préféré
    password = models.CharField(max_length=128, blank=True)
    referrer = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL,
                                 related_name='ecommerce_referrals_given')
    objects = EcommerceUserManager()

    USERNAME_FIELD = 'email'  # Utilise l'email pour l'authentification
    REQUIRED_FIELDS = ['username']  # Autres champs requis pour la création de l'utilisateur

    def calculate_referral_rewards(self):
        total_rewards = 0
        for referral in self.referrals_given.all():
            total_rewards += referral.loyalty_points  # Par exemple, vous pouvez ajouter les points de fidélité des parrains
        return total_rewards

    def calculate_total_referral_rewards(self):
        total_rewards = sum(referral.reward_earned for referral in self.referrals_given.all())
        return total_rewards
    def __str__(self):
        return f"{self.username} ({self.email})"

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
class Referral(models.Model):
    referrer = models.ForeignKey(EcommerceUser, on_delete=models.CASCADE, related_name='referrals_given')
    referred = models.ForeignKey(EcommerceUser, on_delete=models.CASCADE, related_name='referrals_received')
    date_referred = models.DateTimeField(auto_now_add=True)
    reward_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.referrer.email} a parrainé {self.referred.email}"

    def calculate_reward(self):
        # Définir une logique pour calculer la récompense en fonction des règles
        self.reward_earned = 500  # Par exemple, 500 points de récompense pour chaque parrainage réussi
        return self.reward_earned

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    image_url = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_sold = models.BooleanField(default=False)
    is_ordered = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def toggle_sold(self):
        self.is_sold = not self.is_sold
        self.save()

    def toggle_ordered(self):
        self.is_ordered = not self.is_ordered
        self.save()

@receiver(pre_delete, sender=Product)
def set_deleted_at(sender, instance, **kwargs):
    instance.deleted_at = timezone.now()
    instance.save()

@receiver(pre_save, sender=Category)
def normalize_category_name(sender, instance, **kwargs):
    instance.name = instance.name.lower()
    existing_category = Category.objects.filter(name=instance.name).first()
    if existing_category and instance.pk != existing_category.pk:
        raise ValidationError("Une catégorie avec ce nom existe déjà.")



class ArticleCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class Article(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(ArticleCategory, on_delete=models.CASCADE, related_name='articles')
    image_url = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_sold = models.BooleanField(default=False)
    is_ordered = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def toggle_sold(self):
        self.is_sold = not self.is_sold
        self.save()

    def toggle_ordered(self):
        self.is_ordered = not self.is_ordered
        self.save()


class ArticleAction(models.Model):
    ACTION_CHOICES = [
        ('addition', 'Addition'),
        ('modification', 'Modification'),
        ('deletion', 'Deletion'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)
    validated = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.action} - {self.product.name}"

    class Meta:
        ordering = ['-timestamp']

class Statistic(models.Model):
    data = models.CharField(max_length=100, default='your_default_value_here')

    def __str__(self):
        return f'Statistic {self.id}'
