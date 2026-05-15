#*fi association/forms.py
from django import forms
from .models import AssociationUser,Association
from .models import   Membre


class RejetMotifForm(forms.Form):
    motif = forms.CharField(
        label="Motif du rejet",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        max_length=500
    )

class HeritierForm(forms.ModelForm):
    class Meta:
        model = AssociationUser  # Spécification du modèle à utiliser
        fields = [
            'nom_heritier', 'prenom_heritier', 'nationalite_heritier',
            'date_of_birth_heritier', 'sexe_heritier', 'profession_heritier',
            'prefecture_heritier', 'maison_non_loin_de_heritier', 'photo_membre_heritier',
            'contact_heritier'
        ]

    sexe_heritier = forms.ChoiceField(
        choices=[('', 'Sélectionnez le sexe'), ('M', 'Masculin'), ('F', 'Féminin')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class MembreForm(forms.ModelForm):
    class Meta:
        model = AssociationUser
        fields = [
            'email', 'first_name', 'last_name','nompop', 'nationalite', 'date_of_birth',
            'sexe', 'profession', 'prefecture', 'maison_non_loin_de', 'adresse',
            'quartier', 'contact', 'association',
            'photo_membre', 'taille_chemise', 'taille_pied'
        ]

    # Définir les choix pour le sexe avec un widget radio
    sexe = forms.ChoiceField(
        choices=[('M', 'Masculin'), ('F', 'Féminin')],
        widget=forms.RadioSelect
    )

    # Taille de la chemise, facultatif
    taille_chemise = forms.ChoiceField(
        choices=[('S', 'S'), ('M', 'M'), ('L', 'L'), ('XL', 'XL')],
        required=False,  # Optionnel, donc l'utilisateur peut ne pas le remplir
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Taille de pied (peut être facultatif selon le cas)
    taille_pied = forms.CharField(
        max_length=10, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )


class AssociationLoginForm(forms.Form):
    nom = forms.CharField(max_length=255, label="Nom de l'association :",)
    password = forms.CharField(widget=forms.PasswordInput(), label="Mot de passe :")

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)

        # Si une instance d'association est fournie, on préremplit le champ nom avec le nom de l'association
        if instance:
            self.fields['nom'].initial = instance.nom
        else:
            self.fields['nom'].initial = ''
class AssociationSignupForm(forms.ModelForm):
    class Meta:
        model = AssociationUser
        fields = ['email', 'first_name', 'last_name', 'password']  # Assurez-vous que ces champs existent dans AssociationUser

    # Optionnel : Ajouter une validation pour le mot de passe
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class AssociationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label='Mot de passe')  # Ajout d'un champ de mot de passe

    class Meta:
        model = Association
        fields = ['logo', 'nom', 'description', 'adresse']

    def save(self, commit=True):
        # Obtenez l'instance associée
        association = super().save(commit=False)

        # Hachez le mot de passe et définissez-le
        if self.cleaned_data.get('password'):
            association.set_password(self.cleaned_data['password'])  # Utilisez set_password pour le hachage

        # Sauvegarder l'instance
        if commit:
            association.save()

        return association
class MembreUForm(forms.ModelForm):
    class Meta:
        model = Membre
        fields = ['association', 'role']



class AssociationUserCreationForm(forms.ModelForm):
    class Meta:
        model = AssociationUser
        fields = ('email', 'first_name', 'last_name','nompop', 'association','contact','adresse','role', 'is_staff', 'is_active')

    def save(self, commit=True):
        user = super().save(commit=False)
        # Hacher le mot de passe avant de sauvegarder
        if 'password' in self.cleaned_data:
            user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class AssociationUserChangeForm(forms.ModelForm):
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput, required=False)

    class Meta:
        model = AssociationUser
        fields = ('email', 'first_name', 'last_name','nompop','association','contact','adresse','montant_adhesion','parrain', 'nom_heritier', 'role', 'is_staff', 'is_active')

    def save(self, commit=True):
        user = super().save(commit=False)
        # Hacher le mot de passe si un nouveau mot de passe est fourni
        if self.cleaned_data["password"]:
            user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user
class AssociationUserForm(forms.ModelForm):
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput, required=False)
    class Meta:
        model = AssociationUser
        # Inclure tous les champs nécessaires
        fields = [
             'first_name', 'last_name','nompop', 'adresse','quartier',
            'photo_membre','montant_adhesion','parrain', 'nom_heritier'
        ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer les parrains pour exclure ceux qui ont le rôle "comite"
        self.fields['parrain'].queryset = AssociationUser.objects.exclude(role='comite')

    def save(self, commit=True):
        user = super().save(commit=False)
        # Hacher le mot de passe avant de sauvegarder
        if 'password' in self.cleaned_data:
            user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


