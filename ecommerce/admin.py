from django.contrib import admin
from .models import Category, Product, ArticleCategory, Article, ArticleAction, Statistic,EcommerceUser, Referral
from .forms import EcommerceSignupForm
@admin.register(EcommerceUser)
class EcommerceUserAdmin(admin.ModelAdmin):
    form = EcommerceSignupForm
    model = EcommerceUser
    list_display = ('email', 'username', 'shipping_address', 'billing_address', 'loyalty_points', 'preferred_payment_method', 'referrer')
    search_fields = ('email', 'username')
    list_filter = ('loyalty_points', 'referrer')
    ordering = ('email',)
    list_per_page = 20

@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ('referrer', 'referred', 'date_referred', 'reward_earned')
    search_fields = ('referrer__email', 'referred__email')
    list_filter = ('date_referred',)
    ordering = ('-date_referred',)
    list_per_page = 20
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'created_at', 'updated_at', 'is_sold', 'is_ordered')
    search_fields = ('name', 'description', 'category__name')
    list_filter = ('category', 'is_sold', 'is_ordered')
    readonly_fields = ('created_at', 'updated_at', 'deleted_at')

@admin.register(ArticleCategory)
class ArticleCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'created_at', 'updated_at', 'is_sold', 'is_ordered')
    search_fields = ('name', 'description', 'category__name')
    list_filter = ('category', 'is_sold', 'is_ordered')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ArticleAction)
class ArticleActionAdmin(admin.ModelAdmin):
    list_display = ('product', 'action', 'timestamp', 'validated')
    search_fields = ('product__name', 'action')
    list_filter = ('action', 'validated')
    readonly_fields = ('timestamp',)

@admin.register(Statistic)
class StatisticAdmin(admin.ModelAdmin):
    list_display = ('data',)
    search_fields = ('data',)
