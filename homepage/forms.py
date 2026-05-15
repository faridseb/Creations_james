from django import forms
from .models import DemandeSupport, OeuvreSocialUser
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
class UserRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput())
    password2 = forms.CharField(widget=forms.PasswordInput())

    # Exclure "Torpilleur" des choix de rôles
    filtered_roles = [choice for choice in OeuvreSocialUser.ROLE_CHOICES if choice[0] != "TOR"]

    roles = forms.MultipleChoiceField(
        choices=filtered_roles,  # Utilisation des rôles filtrés
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    class Meta:
        model = OeuvreSocialUser
        fields = ['email', 'username', 'first_name', 'last_name', 'roles']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Appliquer la classe form-control pour les champs de texte
        for field_name in ['email', 'username', 'first_name', 'last_name','password1','password2']:
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])  # Hacher le mot de passe
        user.role = ','.join(self.cleaned_data['roles'])  # Sauvegarde des rôles en chaîne

        if commit:
            user.save()
        return user
class LoginForm(forms.Form):
    """
    Formulaire de connexion personnalisé pour l'authentification par email.
    """
    email = forms.EmailField(
        label="Adresse email",
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Votre email"}),
        required=True
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Votre mot de passe"}),
        required=True
    )
class DemandeSupportForm(forms.ModelForm):
    class Meta:
        model = DemandeSupport
        fields = ['titre', 'description']
