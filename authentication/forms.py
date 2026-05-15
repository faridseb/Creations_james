from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from .models import CustomUser, Referral
from .models import Avatar
from .models import ContentPreferences
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django_countries.fields import CountryField
User = get_user_model()
from phonenumber_field.formfields import PhoneNumberField
from .models import SupportRequest
from django_countries.widgets import CountrySelectWidget


class SupportForm(forms.ModelForm):
    class Meta:
        model = SupportRequest
        fields = ['sujet', 'message']
        widgets = {
            'sujet': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sujet'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Décrivez votre problème'}),
        }
class ContentPreferencesForm(forms.ModelForm):
    class Meta:
        model = ContentPreferences
        fields = ['receive_newsletters', 'receive_promotions']

class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['nom','prenom','email', 'username', 'nationalite', 'sexe', 'profession', 'lieu_travail', 'country', 'ville', 'quartier',
                  'maison_non_loin_de', 'contact', 'referrer', 'stage', 'avatar_color', 'date_of_birth']


class ReferralForm(forms.ModelForm):
    password1 = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmer le mot de passe", widget=forms.PasswordInput)

    GENDER_CHOICES = [
        ('male', 'Homme'),
        ('female', 'Femme'),
    ]

    sexe = forms.ChoiceField(choices=GENDER_CHOICES, widget=forms.Select)
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    contact = PhoneNumberField(region='TG', required=True)
    class Meta:
        model = CustomUser
        fields = ('nom', 'prenom', 'email', 'username', 'nationalite', 'sexe','nompop',
                  'profession', 'lieu_travail', 'nationalite', 'country', 'ville',
                  'quartier', 'maison_non_loin_de', 'contact', 'date_of_birth', 'referrer')
        widgets = {
            'country': CountrySelectWidget(),
        }

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")

        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre le champ country obligatoire
        self.fields['country'].required = True
        # Filtrer pour inclure uniquement les utilisateurs qui ne sont pas administrateurs (superusers)
        self.fields['referrer'].queryset = get_user_model().objects.filter(is_superuser=False)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])  # Hache le mot de passe
        if commit:
            user.save()
        return user
class ReferrallinkForm(forms.ModelForm):
    password1 = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmer le mot de passe", widget=forms.PasswordInput)

    GENDER_CHOICES = [
        ('male', 'Homme'),
        ('female', 'Femme'),
    ]

    sexe = forms.ChoiceField(choices=GENDER_CHOICES, widget=forms.Select)
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    contact = PhoneNumberField(region='TG', required=True)
    class Meta:
        model = CustomUser
        fields = ('nom', 'prenom', 'email', 'username', 'nationalite', 'sexe','nompop',
                  'profession', 'lieu_travail', 'nationalite', 'country', 'ville',
                  'quartier', 'maison_non_loin_de', 'contact', 'date_of_birth', 'referrer')
        widgets = {
            'country': CountrySelectWidget(),
        }

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")

        return cleaned_data

    def __init__(self, *args, **kwargs):
        referrer = kwargs.pop('referrer', None)  # Récupérer le parrain
        super().__init__(*args, **kwargs)

        # Désactiver le champ referrer
        self.fields['referrer'].widget.attrs['readonly'] = True
        self.fields['referrer'].required = False  # Éviter les erreurs de validation

        # Pré-remplir le champ referrer s'il existe
        if referrer:
            self.fields['referrer'].initial = referrer

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])  # Hache le mot de passe
        if commit:
            user.save()
        return user
class AdReferralForm(forms.ModelForm):
    password1 = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmer le mot de passe", widget=forms.PasswordInput)

    GENDER_CHOICES = [
        ('male', 'Homme'),
        ('female', 'Femme'),
    ]
   

    sexe = forms.ChoiceField(choices=GENDER_CHOICES, widget=forms.Select)
   
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = CustomUser
        fields = ('nom','prenom',
            'email', 'username', 'nationalite', 'sexe', 'profession','nompop',
            'lieu_travail',  'country','ville', 'quartier', 'maison_non_loin_de',
            'contact', 'date_of_birth','referrer'
        )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")

        return cleaned_data

    def __init__(self, *args, **kwargs):
        referrer_id = kwargs.pop('referrer_id', None)
        super().__init__(*args, **kwargs)
        if referrer_id:
            self.fields['referrer'].initial = referrer_id  # Initialisez le champ referrer avec l'ID du référent

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])  # Hache le mot de passe
        if commit:
            user.save()
        return user
class PaymentForm(forms.Form):
    country = CountryField().formfield()
    amount = forms.DecimalField(decimal_places=2, max_digits=10)


class ProfileUpdateForm(forms.ModelForm):
    GENDER_CHOICES = [
        ('male', 'Homme'),
        ('female', 'Femme'),
    ]
   

    sexe = forms.ChoiceField(choices=GENDER_CHOICES, widget=forms.Select)
 
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    class Meta:
        model = CustomUser
        fields = ['email', 'username','nom','prenom', 'nationalite', 'sexe', 'profession', 'lieu_travail',
                  'country', 'ville', 'quartier', 'maison_non_loin_de', 'contact',
                     'date_of_birth']


class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput)
    new_password1 = forms.CharField(widget=forms.PasswordInput)
    new_password2 = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        if new_password1 != new_password2:
            raise forms.ValidationError("Les nouveaux mots de passe ne correspondent pas.")
        return cleaned_data


class CustomUserAuthenticationForm(forms.Form):
    username = forms.CharField(max_length=150)  # Utilise le champ 'username' au lieu de 'email'
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            self.user = authenticate(username=username, password=password)  # Authentifie avec 'username' au lieu de 'email'
            if not self.user:
                raise forms.ValidationError("Nom d'utilisateur ou mot de passe invalide.")

        return cleaned_data

    def get_user(self):
        return self.user if hasattr(self, 'user') else None


class AvatarForm(forms.ModelForm):
    class Meta:
        model = Avatar
        fields = ['image']

class ThemeChangeForm(forms.Form):
            THEME_CHOICES = [
                ('light', 'Light'),
                ('dark', 'Dark'),
            ]
            theme = forms.ChoiceField(choices=THEME_CHOICES, label='Choisissez un thème')
            # Dans authentication/forms.py

            from django import forms

class LanguageChangeForm(forms.Form):
                LANGUAGE_CHOICES = [
                    ('fr', 'Français'),
                    ('en', 'English'),
                    # Ajoutez d'autres langues selon vos besoins
                ]
                language = forms.ChoiceField(choices=LANGUAGE_CHOICES, label='Choisissez une langue')

class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['profile_picture']