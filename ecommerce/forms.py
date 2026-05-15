from django import forms
from .models import Product, Category, Article, ArticleCategory
from django.contrib.auth.forms import AuthenticationForm
from .models import Statistic
from django.contrib.auth import authenticate
from .models import EcommerceUser

class EcommerceSignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = EcommerceUser
        fields = ['username', 'email', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])  # Hachage du mot de passe
        if commit:
            user.save()
        return user

class EcommerceLoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = EcommerceUser
        fields = ['username', 'email', 'shipping_address']
class StatisticForm(forms.ModelForm):
    class Meta:
        model = Statistic
        fields = '__all__'
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'category', 'image_url']

    def clean_name(self):
        name = self.cleaned_data['name']
        if Product.objects.filter(name=name).exists():
            raise forms.ValidationError("Un produit avec ce nom existe déjà.")
        return name

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = '__all__'

    def clean_name(self):
        name = self.cleaned_data['name']
        if Category.objects.filter(name=name).exists():
            raise forms.ValidationError("Une catégorie avec ce nom existe déjà.")
        return name

class ArticleForm(forms.ModelForm):
    category = forms.ModelChoiceField(queryset=ArticleCategory.objects.all(), required=True)
    class Meta:
        model = Article
        fields = ['name', 'description', 'price', 'category', 'image_url']

    def clean_name(self):
        name = self.cleaned_data['name']
        if Article.objects.filter(name=name).exists():
            raise forms.ValidationError("Un article avec ce nom existe déjà.")
        return name

class ArticleCategoryForm(forms.ModelForm):
    class Meta:
        model = ArticleCategory
        fields = '__all__'

    def clean_name(self):
        name = self.cleaned_data['name']
        if ArticleCategory.objects.filter(name=name).exists():
            raise forms.ValidationError("Une catégorie d'article avec ce nom existe déjà.")
        return name

class AdminAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label="Email", max_length=150)
    password = forms.CharField(label="Mot de passe", strip=False, widget=forms.PasswordInput)

    error_messages = {
        'invalid_login': "Veuillez saisir un email et un mot de passe corrects.",
        'inactive': "Ce compte est inactif.",
    }

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(self.error_messages['invalid_login'], code='invalid_login')
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

