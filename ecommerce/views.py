from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required,user_passes_test
from django.urls import reverse_lazy
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import logout
from django.contrib import messages
from django.db.models import Q
from .models import Category, Product, Article, ArticleCategory,  ArticleAction
from .forms import ProductForm, CategoryForm, ArticleForm, ArticleCategoryForm, AdminAuthenticationForm
import logging

from django.http import JsonResponse
from urllib.parse import quote

from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView, View
# your_app/admin.py
from django.contrib import admin
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib.auth import logout
from django.contrib import messages
from django.db.models import Q
from .models import Category, Product, Article, ArticleCategory,  ArticleAction
from .forms import ProductForm, CategoryForm, ArticleForm, ArticleCategoryForm, AdminAuthenticationForm
import logging
from django.views.generic import TemplateView, View
from .forms import EcommerceSignupForm, EcommerceLoginForm
from .models import EcommerceUser
from django.contrib.auth import authenticate, login
from .forms import UserProfileForm
def ecommerce_signup(request):
    if request.method == 'POST':
        form = EcommerceSignupForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            # Créer une instance de PartiUser
            user = EcommerceUser(
                email=email,
                username=username,
            )
            user.set_password(password)  # Hache le mot de passe
            user.save()  # Enregistre l'utilisateur

            messages.success(request, 'Inscription réussie. Vous pouvez maintenant vous connecter.')
            return redirect('ecommerce:ecommerce_login')  # Redirige vers la page de connexion

    else:
        form = EcommerceSignupForm  # Créer un formulaire vide pour un GET

    return render(request, 'ecommerce/ecommerce_signup.html', {'form': form})

# Connexion

def ecommerce_login(request):
    utilisateurs = EcommerceUser.objects.all()

    if request.method == 'POST':
        form = EcommerceLoginForm(request.POST)
        show_password_reset_link = False
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            # Authentification via l'email
            user = authenticate(request, username=username, password=password)
            if user is not None and isinstance(user, EcommerceUser):  # Vérifie que l'utilisateur est une instance de EcommerceUser
                login(request, user)  # Connexion de l'utilisateur
                messages.success(request, "Connexion réussie !")
                return redirect('ecommerce:ecommerce_dashboard')  # Redirection après la connexion réussie
            else:
                show_password_reset_link = True
                messages.error(request, "Accès réservé aux utilisateurs du modèle EcommerceUser ou identifiants invalides.")
        else:
            messages.error(request, "Erreur dans le formulaire. Veuillez vérifier vos informations.")
    else:
        form = EcommerceLoginForm()

    return render(request, 'ecommerce/ecommerce_login.html',
                  {'form': form,
                   'show_password_reset_link': True,
                   'utilisateurs': utilisateurs
                   })

def ecommerce_dashboard(request):
    return render(request, 'ecommerce/ecommerce_dashboard.html')

def ecommerce_profile(request):
    user = request.user
    return render(request, 'ecommerce/profile.html', {'user': user})


def ecommerce_rewards(request):
    user = request.user
    return render(request, 'ecommerce/rewards.html', {'user': user})


def ecommerce_referrals(request):
    user = request.user
    return render(request, 'ecommerce/referrals.html', {'user': user})


def ecommerce_notifications(request):
    user = request.user
    return render(request, 'ecommerce/notifications.html', {'user': user})
def edit_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('ecommerce:profile')  # Redirige vers la page de profil après la sauvegarde
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'ecommerce/edit_profile.html', {'form': form})
def conditions(request):
    return render(request, 'ecommerce/conditions.html')
def conditions_commande(request):
    return render(request, 'ecommerce/conditions.html')
def ecommerce_profile_view(request):
    user = request.user.ecommerceuser
    total_referral_rewards = user.calculate_total_referral_rewards()
    referrals = user.referrals_given.all()

    context = {
        'user': user,
        'total_referral_rewards': total_referral_rewards,
        'referrals': referrals,
    }
    return render(request, 'ecommerce/profile.html', context)
def is_admin(user):
    return (user.is_superuser
            @user_passes_test(is_admin))
def admin_product_list(request):
    products = Product.objects.all()
    return render(request, 'ecommerce/admin_product_list.html', {'products': products})

def admin_add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data.get('name')
            if Product.objects.filter(name=name).exists():
                messages.error(request, 'Un produit avec ce nom existe déjà.')
            else:
                form.save()
                messages.success(request, 'Produit ajouté avec succès.')
                return redirect('admin_product_list')
    else:
        form = ProductForm()

    categories = Category.objects.all()
    return render(request, 'ecommerce/admin_add_product.html', {'form': form, 'categories': categories})

@user_passes_test(is_admin)
def admin_edit_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    categories = Category.objects.all()
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Produit modifié avec succès.')
            return redirect('admin_product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'ecommerce/admin_edit_product.html', {'form': form, 'product': product, 'categories': categories})

@user_passes_test(is_admin)
def admin_delete_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Produit supprimé avec succès.')
        return redirect('admin_product_list')
    return render(request, 'ecommerce/admin_delete_product.html', {'product': product})

class EcommerceAdminLoginView(LoginView):
    form_class = AdminAuthenticationForm
    template_name = 'ecommerce/admin_login.html'

    def get_success_url(self):
        return reverse_lazy('ecommerce:admin_dashboard')

@login_required
@user_passes_test(is_admin)
def ecommerce_admin_dashboard(request):
    return render(request, 'ecommerce/admin_dashboard.html')

def admin_logout(request):
    logout(request)
    return redirect('ecommerce:admin_login')

@user_passes_test(is_admin)
def admin_add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category_name = form.cleaned_data.get('name')
            existing_category = Category.objects.filter(name=category_name).exists()
            if existing_category:
                messages.error(request, 'La catégorie existe déjà. Veuillez en choisir une autre.')
            else:
                form.save()
                messages.success(request, 'La catégorie a été ajoutée avec succès.')
                return redirect('ecommerce:admin_add_category')
        else:
            messages.error(request, 'Le formulaire n\'est pas valide, veuillez corriger les erreurs.')
    else:
        form = CategoryForm()
    return render(request, 'ecommerce/admin_add_category.html', {'form': form})

@user_passes_test(is_admin)
def admin_add_article_category(request):
    if request.method == 'POST':
        form = ArticleCategoryForm(request.POST)
        if form.is_valid():
            category_name = form.cleaned_data.get('name')
            existing_category = ArticleCategory.objects.filter(name=category_name).exists()
            if existing_category:
                messages.error(request, 'La catégorie existe déjà. Veuillez en choisir une autre.')
            else:
                form.save()
                messages.success(request, 'La catégorie a été ajoutée avec succès.')
                return redirect('ecommerce:admin_add_article_category')
        else:
            messages.error(request, 'Le formulaire n\'est pas valide, veuillez corriger les erreurs.')
    else:
        form = ArticleCategoryForm()
    return render(request, 'ecommerce/admin_add_article_category.html', {'form': form})

@user_passes_test(is_admin)
def admin_add_article(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data.get('name')
            if Article.objects.filter(name=name).exists():
                messages.error(request, 'Un article avec ce nom existe déjà.')
            else:
                form.save()
                messages.success(request, 'Article ajouté avec succès.')
                return redirect('ecommerce:admin_article_list')
    else:
        form = ArticleForm()

    categories = ArticleCategory.objects.all()
    return render(request, 'ecommerce/admin_add_article.html', {'form': form, 'categories': categories})

@user_passes_test(is_admin)
def admin_edit_article(request, article_id):
    article = get_object_or_404(Article, pk=article_id)
    categories = ArticleCategory.objects.all()
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, 'Article modifié avec succès.')
            return redirect('ecommerce:admin_article_list')
    else:
        form = ArticleForm(instance=article)
    return render(request, 'ecommerce/admin_edit_article.html', {'form': form, 'article': article, 'categories': categories})

@user_passes_test(is_admin)
def admin_delete_article(request, article_id):
    article = get_object_or_404(Article, pk=article_id)
    if request.method == 'POST':
        article.delete()
        messages.success(request, 'Article supprimé avec succès.')
        return redirect('ecommerce:admin_article_list')
    return render(request, 'ecommerce/admin_delete_article.html', {'article': article})

@user_passes_test(is_admin)
def admin_article_list(request):
    articles = Article.objects.all()
    return render(request, 'ecommerce/admin_article_list.html', {'articles': articles})


logger = logging.getLogger(__name__)

def filter_products(request, action):
    categories = Category.objects.all()
    products = Product.objects.filter(articleaction__action=action)

    # Filtrage
    category_id = request.GET.get('category')
    year = request.GET.get('year')
    month = request.GET.get('month')
    day = request.GET.get('day')
    hour = request.GET.get('hour')

    if category_id:
        products = products.filter(category_id=category_id)
    if year:
        products = products.filter(Q(created_at__year=year) | Q(updated_at__year=year) | Q(deleted_at__year=year))
    if month:
        products = products.filter(Q(created_at__month=month) | Q(updated_at__month=month) | Q(deleted_at__month=month))
    if day:
        products = products.filter(Q(created_at__day=day) | Q(updated_at__day=day) | Q(deleted_at__day=day))
    if hour:
        products = products.filter(Q(created_at__hour=hour) | Q(updated_at__hour=hour) | Q(deleted_at__hour=hour))

    context = {
        'categories': categories,
        'products': products,
        'action': action,
    }

    return render(request, 'ecommerce/products_filtered.html', context)

def is_admin(user):
    return user.is_superuser


def article_vendu(request):
    # Votre logique ici (par exemple, récupérer les articles vendus)
    return render(request, 'ecommerce/sale_page.html')

def total_users(request):
    total_users = CustomUser.objects.count()
    return render(request, 'total_users.html', {'total_users': total_users})

def total_products(request):
    total_products = Product.objects.count()
    return render(request, 'total_products.html', {'total_products': total_products})


def article_list(request):
    article_categories = ArticleCategory.objects.prefetch_related('articles').all()
    return render(request, 'ecommerce/article_list.html', {
        'article_categories': article_categories
    })

def stats_page(request):
    total_users = CustomUser.objects.count()
    total_products = Product.objects.count()
    total_articles = Article.objects.count()

    # Total des actions d'ajout, de modification et de suppression pour les produits
    product_actions = ArticleAction.objects.filter(product__isnull=False)
    total_product_additions = product_actions.filter(action='addition').count()
    total_product_modifications = product_actions.filter(action='modification').count()
    total_product_deletions = product_actions.filter(action='deletion').count()

    # Total des actions d'ajout, de modification et de suppression pour les articles
    article_actions = ArticleAction.objects.filter(product__isnull=True)
    total_article_additions = article_actions.filter(action='addition').count()
    total_article_modifications = article_actions.filter(action='modification').count()
    total_article_deletions = article_actions.filter(action='deletion').count()

    context = {
        'total_users': total_users,
        'total_products': total_products,
        'total_articles': total_articles,
        'total_product_additions': total_product_additions,
        'total_product_modifications': total_product_modifications,
        'total_product_deletions': total_product_deletions,
        'total_article_additions': total_article_additions,
        'total_article_modifications': total_article_modifications,
        'total_article_deletions': total_article_deletions,
    }

    return render(request, 'ecommerce/stats_page.html', context)

class SalePageView(TemplateView):
    template_name = 'ecommerce/sale_page.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.objects.all()
        context['articles'] = Article.objects.all()
        return context

class SellProductView(View):
    def post(self, request):
        product_id = request.POST.get('product_id')
        # Récupérer le produit à vendre
        product = Product.objects.get(id=product_id)
        # Enregistrer le produit vendu dans une autre table
        # (par exemple, ProductSold) et supprimer l'entrée de Product
        # Exemple :
        # ProductSold.objects.create(name=product.name, description=product.description, ...)
        product.delete()
        return redirect('ecommerce:product_list')  # Rediriger vers la liste des produits

class OrderProductView(View):
    def get(self, request, product_id):
        # Réaliser les opérations nécessaires pour commander le produit
        # (par exemple, afficher un formulaire de commande)
        return redirect('ecommerce:order_form')  # Rediriger vers le formulaire de commande

@login_required
@user_passes_test(is_admin)
def toggle_product_sold(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.toggle_sold()
    action = "vendu" if product.is_sold else "non vendu"
    messages.success(request, f'Le produit "{product.name}" est maintenant marqué comme {action}.')
    return redirect('ecommerce:sale_page')

@login_required
@user_passes_test(is_admin)
def toggle_product_ordered(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.toggle_ordered()
    action = "commandé" if product.is_ordered else "non commandé"
    messages.success(request, f'Le produit "{product.name}" est maintenant marqué comme {action}.')
    return redirect('ecommerce:sale_page')
@login_required
@user_passes_test(is_admin)
def toggle_article_sold(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    article.toggle_sold()
    action = "vendu" if article.is_sold else "non vendu"
    messages.success(request, f'L\'article "{article.name}" est maintenant marqué comme {action}.')
    return redirect('ecommerce:sale_page')

@login_required
@user_passes_test(is_admin)
def toggle_article_ordered(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    article.toggle_ordered()
    action = "commandé" if article.is_ordered else "non commandé"
    messages.success(request, f'L\'article "{article.name}" est maintenant marqué comme {action}.')
    return redirect('ecommerce:sale_page')
def sold_products(request):
    categories = Category.objects.all()
    products = Product.objects.filter(is_sold=True)

    # Filtrage
    category_id = request.GET.get('category')
    year = request.GET.get('year')
    month = request.GET.get('month')
    day = request.GET.get('day')
    hour = request.GET.get('hour')

    if category_id:
        products = products.filter(category_id=category_id)
    if year:
        products = products.filter(Q(created_at__year=year) | Q(updated_at__year=year) | Q(deleted_at__year=year))
    if month:
        products = products.filter(Q(created_at__month=month) | Q(updated_at__month=month) | Q(deleted_at__month=month))
    if day:
        products = products.filter(Q(created_at__day=day) | Q(updated_at__day=day) | Q(deleted_at__day=day))
    if hour:
        products = products.filter(Q(created_at__hour=hour) | Q(updated_at__hour=hour) | Q(deleted_at__hour=hour))

    context = {
        'categories': categories,
        'products': products,
    }

    return render(request, 'ecommerce/sold_products.html', context)

def ordered_products(request):
    categories = Category.objects.all()
    products = Product.objects.filter(is_ordered=True)

    # Filtrage
    category_id = request.GET.get('category')
    year = request.GET.get('year')
    month = request.GET.get('month')
    day = request.GET.get('day')
    hour = request.GET.get('hour')

    if category_id:
        products = products.filter(category_id=category_id)
    if year:
        products = products.filter(Q(created_at__year=year) | Q(updated_at__year=year) | Q(deleted_at__year=year))
    if month:
        products = products.filter(Q(created_at__month=month) | Q(updated_at__month=month) | Q(deleted_at__month=month))
    if day:
        products = products.filter(Q(created_at__day=day) | Q(updated_at__day=day) | Q(deleted_at__day=day))
    if hour:
        products = products.filter(Q(created_at__hour=hour) | Q(updated_at__hour=hour) | Q(deleted_at__hour=hour))

    context = {
        'categories': categories,
        'products': products,
    }

    return render(request, 'ecommerce/ordered_products.html', context)
def sold_articles(request):
    categories = ArticleCategory.objects.all()
    articles = Article.objects.filter(is_sold=True)

    # Filtrage
    category_id = request.GET.get('category')
    year = request.GET.get('year')
    month = request.GET.get('month')
    day = request.GET.get('day')
    hour = request.GET.get('hour')

    if category_id:
        articles = articles.filter(category_id=category_id)
    if year:
        articles = articles.filter(Q(created_at__year=year) | Q(updated_at__year=year) | Q(deleted_at__year=year))
    if month:
        articles = articles.filter(Q(created_at__month=month) | Q(updated_at__month=month) | Q(deleted_at__month=month))
    if day:
        articles = articles.filter(Q(created_at__day=day) | Q(updated_at__day=day) | Q(deleted_at__day=day))
    if hour:
        articles = articles.filter(Q(created_at__hour=hour) | Q(updated_at__hour=hour) | Q(deleted_at__hour=hour))

    context = {
        'categories': categories,
        'articles': articles,
    }

    return render(request, 'ecommerce/sold_articles.html', context)

def ordered_articles(request):
    categories = ArticleCategory.objects.all()
    articles = Article.objects.filter(is_ordered=True)

    # Filtrage
    category_id = request.GET.get('category')
    year = request.GET.get('year')
    month = request.GET.get('month')
    day = request.GET.get('day')
    hour = request.GET.get('hour')

    if category_id:
        articles = articles.filter(category_id=category_id)
    if year:
        articles = articles.filter(Q(created_at__year=year) | Q(updated_at__year=year) | Q(deleted_at__year=year))
    if month:
        articles = articles.filter(Q(created_at__month=month) | Q(updated_at__month=month) | Q(deleted_at__month=month))
    if day:
        articles = articles.filter(Q(created_at__day=day) | Q(updated_at__day=day) | Q(deleted_at__day=day))
    if hour:
        articles = articles.filter(Q(created_at__hour=hour) | Q(updated_at__hour=hour) | Q(deleted_at__hour=hour))

    context = {
        'categories': categories,
        'articles': articles,
    }

    return render(request, 'ecommerce/ordered_articles.html', context)

def sold_articles(request):
    categories = ArticleCategory.objects.all()
    articles = Article.objects.filter(is_sold=True)

    # Filtrage
    category_id = request.GET.get('category')
    year = request.GET.get('year')
    month = request.GET.get('month')
    day = request.GET.get('day')
    hour = request.GET.get('hour')

    if category_id:
        articles = articles.filter(category_id=category_id)
    if year:
        articles = articles.filter(Q(created_at__year=year) | Q(updated_at__year=year) | Q(deleted_at__year=year))
    if month:
        articles = articles.filter(Q(created_at__month=month) | Q(updated_at__month=month) | Q(deleted_at__month=month))
    if day:
        articles = articles.filter(Q(created_at__day=day) | Q(updated_at__day=day) | Q(deleted_at__day=day))
    if hour:
        articles = articles.filter(Q(created_at__hour=hour) | Q(updated_at__hour=hour) | Q(deleted_at__hour=hour))

    context = {
        'categories': categories,
        'articles': articles,
    }

    return render(request, 'ecommerce/sold_articles.html', context)

def ordered_articles(request):
    categories = ArticleCategory.objects.all()
    articles = Article.objects.filter(is_ordered=True)

    # Filtrage
    category_id = request.GET.get('category')
    year = request.GET.get('year')
    month = request.GET.get('month')
    day = request.GET.get('day')
    hour = request.GET.get('hour')

    if category_id:
        articles = articles.filter(category_id=category_id)
    if year:
        articles = articles.filter(Q(created_at__year=year) | Q(updated_at__year=year) | Q(deleted_at__year=year))
    if month:
        articles = articles.filter(Q(created_at__month=month) | Q(updated_at__month=month) | Q(deleted_at__month=month))
    if day:
        articles = articles.filter(Q(created_at__day=day) | Q(updated_at__day=day) | Q(deleted_at__day=day))
    if hour:
        articles = articles.filter(Q(created_at__hour=hour) | Q(updated_at__hour=hour) | Q(deleted_at__hour=hour))

    context = {
        'categories': categories,
        'articles': articles,
    }

    return render(request, 'ecommerce/ordered_articles.html', context)

# Vues pour les différentes pages
def product_list(request):
    categories = Category.objects.prefetch_related('products').all()
    produit_image_5 = Product.objects.filter(id=1).first()
    article_categories = ArticleCategory.objects.prefetch_related('articles').all()
    try:
        product = Product.objects.get(id=1)
    except Product.DoesNotExist:
        product = None

    return render(request, 'ecommerce/product_list.html', {
        'categories': categories,
        'article_categories': article_categories,
        'produit_image_5': produit_image_5
    })

def shop(request):
    categories = Category.objects.prefetch_related('products').all()

    article_categories = ArticleCategory.objects.prefetch_related('articles').all()
    try:
        product = Product.objects.get(id=1)
    except Product.DoesNotExist:
        product = None

    return render(request, 'ecommerce/shop.html', {
        'categories': categories,
        'article_categories': article_categories,
    })

def about(request):
    return render(request, 'ecommerce/about.html')

def services(request):
    return render(request, 'ecommerce/services.html')

def blog(request):
    return render(request, 'ecommerce/blog.html')

def contact(request):
    return render(request, 'ecommerce/contact.html')
@csrf_exempt
def send_whatsapp_order(request):
    if request.method == "POST":
        data = request.POST
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        phone = data.get("phone")
        address = data.get("address")
        products = request.POST.getlist("products[]")

        if not all([first_name, last_name, phone, address, products]):
            return JsonResponse({"error": "Informations manquantes."}, status=400)

        message = f"🛍️ Nouvelle commande de {first_name} {last_name} :\n\n"
        message += f"📞 Téléphone : {phone}\n"
        message += f"🏠 Adresse : {address}\n\n"
        message += f"Détails des produits :\n"

        for p in products:
            try:
                pid, qty, name, price = p.split("|")
                total = int(qty) * float(price)
                # Mise en forme du total avec espaces comme séparateurs de milliers
                total_str = f"{int(total):,}".replace(",", " ")
                message += f"• {name} - {qty} x {price} CFA = {total_str} CFA\n"
            except ValueError:
                # Ignore les erreurs de parsing
                continue

        encoded_message = quote(message)
        whatsapp_number = settings.WHATSAPP_NUMBER  # Assure-toi que c’est bien défini dans settings.py
        whatsapp_url = f"https://wa.me/{whatsapp_number}?text={encoded_message}"

        return JsonResponse({"whatsapp_url": whatsapp_url})

    return JsonResponse({"error": "Méthode non autorisée."}, status=405)
@require_http_methods(["GET", "POST"])
def cart(request):
    # Initialiser ou récupérer le panier
    cart = request.session.get('cart', [])
    whatsapp_number = getattr(settings, 'WHATSAPP_NUMBER', None)
    # Gestion de l'ajout via ?add=ID&type=TYPE
    product_id_to_add = request.GET.get('add')
    type_to_add = request.GET.get('type')  # "available" ou "custom_order"
    if product_id_to_add and type_to_add:
        found = False
        for item in cart:
            if item['product_id'] == int(product_id_to_add) and item['type'] == type_to_add:
                item['quantity'] += 1
                found = True
                break
        if not found:
            cart.append({'product_id': int(product_id_to_add), 'type': type_to_add, 'quantity': 1})

        request.session['cart'] = cart
        return redirect('ecommerce:cart')

    # Gestion des actions POST : update / remove / validate
    if request.method == 'POST':
        if 'update' in request.POST:
            # Mettre à jour les quantités
            for item in cart:
                field_name = f"quantity_{item['product_id']}"
                if field_name in request.POST:
                    try:
                        qty = int(request.POST[field_name])
                        if qty > 0:
                            item['quantity'] = qty
                        else:
                            # Supprimer si quantité invalide
                            cart = [i for i in cart if not (i['product_id'] == item['product_id'] and i['type'] == item['type'])]
                    except ValueError:
                        continue
            messages.success(request, "Panier mis à jour avec succès.")

        elif 'remove' in request.POST:
            product_id_to_remove = int(request.POST['remove'])
            # On enlève uniquement l'élément exact (disponible ou sur commande)
            cart = [i for i in cart if i['product_id'] != product_id_to_remove]

            messages.success(request, "Produit retiré du panier.")

        elif 'validate' in request.POST:
            # Tu peux ici rediriger vers une vue de paiement, commande, etc.
            messages.success(request, "Commande validée !")
            # Tu peux aussi vider le panier si tu veux :
            # request.session['cart'] = []
            return redirect('ecommerce:checkout')  # à adapter selon ta logique

        request.session['cart'] = cart
        return redirect('ecommerce:cart')

    # Récupération des objets produits/articles pour affichage
    product_ids = [item['product_id'] for item in cart if item['type'] == 'available']
    article_ids = [item['product_id'] for item in cart if item['type'] == 'custom_order']
    products = Product.objects.filter(id__in=product_ids)
    articles = Article.objects.filter(id__in=article_ids)

    cart_items = []
    for item in cart:
        obj = None
        if item['type'] == 'available':
            obj = products.filter(id=item['product_id']).first()
        elif item['type'] == 'custom_order':
            obj = articles.filter(id=item['product_id']).first()
        if obj:
            cart_items.append({
                'product': obj,
                'quantity': item['quantity'],
                'type': item['type'],
                'total_price': obj.price * item['quantity']
            })

    available_products = [ci for ci in cart_items if ci['type'] == 'available']
    custom_order_products = [ci for ci in cart_items if ci['type'] == 'custom_order']

    context = {
        'cart': {
            'available_products': available_products,
            'custom_order_products': custom_order_products,
        },
        'whatsapp_number': whatsapp_number,
        'user_is_authenticated': request.user.is_authenticated,
    }

    return render(request, 'ecommerce/cart.html', context)

class PasswordResetView(View):
    def get(self, request):
        return render(request, 'ecommerce/password_reset_form.html')

    def post(self, request):
        username = request.POST.get('username')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return render(request, 'ecommerce/password_reset_form.html')

        try:
            user = EcommerceUser.objects.get(username=username)
            user.password = make_password(new_password)
            user.save()
            messages.success(request, "Votre mot de passe a été mis à jour avec succès.")
            return redirect('ecommerce:ecommerce_login')  # Redirigez vers la page de connexion
        except CustomUser.DoesNotExist:
            messages.error(request, "Utilisateur non trouvé.")
            return render(request, 'ecommerce/password_reset_form.html')