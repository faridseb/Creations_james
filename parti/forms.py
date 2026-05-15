# parti/forms.py
from django import forms
from .models import PartiUser
from django.contrib.auth import authenticate
class PartiSignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    class Meta:
        model = PartiUser
        fields = ['email', 'username', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])  # Hachage du mot de passe
        if commit:
            user.save()
        return user
class PartiLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
