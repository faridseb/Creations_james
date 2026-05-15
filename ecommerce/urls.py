from django.urls import path
from . import views
from .views import SellProductView
app_name = 'ecommerce'
urlpatterns = [
    # Auth
#    path('admin/login/', views.EcommerceAdminLoginView.as_view(), name='admin_login'),
 #   path('admin/logout/', views.admin_logout, name='admin_logout'),
    # Dashboard
    #path('admin/dashboard/', views.ecommerce_admin_dashboard, name='admin_dashboard'),
    # Products
    path('mot-de-passe-oublie/', views.PasswordResetView.as_view(), name='password_reset'),
    path('products/', views.product_list, name='product_list'),

   # path('admin/products/', views.admin_product_list, name='admin_product_list'),
    #path('admin/products/add/', views.admin_add_product, name='admin_add_product'),
    #path('admin/products/<int:product_id>/edit/', views.admin_edit_product, name='admin_edit_product'),
   # path('admin/products/<int:product_id>/delete/', views.admin_delete_product, name='admin_delete_product'),
    # Articles
  #  path('admin/articles/', views.admin_article_list, name='admin_article_list'),
   # path('admin/articles/add/', views.admin_add_article, name='admin_add_article'),
   # path('admin/articles/<int:article_id>/edit/', views.admin_edit_article, name='admin_edit_article'),
    #path('admin/articles/<int:article_id>/delete/', views.admin_delete_article, name='admin_delete_article'),
    # Categories
    # path('admin/categories/add/', views.admin_add_category, name='admin_add_category'),
    #path('admin/article-categories/add/', views.admin_add_article_category, name='admin_add_article_category'),
    # Stats
    #path('admin/stats/', views.stats_page, name='stats_page'),
    # Other URLs...
    path('shop/', views.shop, name='shop'),
    path('about/', views.about, name='about'),
    path('services/', views.services, name='services'),
    path('blog/', views.blog, name='blog'),
    path('contact/', views.contact, name='contact'),
    path('cart/', views.cart, name='cart'),
    path('ecommerce/sale/', views.SalePageView.as_view(), name='sale_page'),
    path('sell-product/', views.SellProductView.as_view(), name='sell_product'),
    path('order-product/<int:product_id>/', views.OrderProductView.as_view(), name='order_product'),
# Autres URL...
    path('sold_products/', views.sold_products, name='sold_products'),
    path('ordered_products/', views.ordered_products, name='ordered_products'),
    path('sold_articles/', views.sold_articles, name='sold_articles'),
    path('ordered_articles/', views.ordered_articles, name='ordered_articles'),
    # autres routes
    path('toggle_product_sold/<int:product_id>/', views.toggle_product_sold, name='toggle_product_sold'),
    path('toggle_product_ordered/<int:product_id>/', views.toggle_product_ordered, name='toggle_product_ordered'),
    path('toggle_article_sold/<int:article_id>/', views.toggle_article_sold, name='toggle_article_sold'),
    path('toggle_article_ordered/<int:article_id>/', views.toggle_article_ordered, name='toggle_article_ordered'),
    path('ecommerce_login/', views.ecommerce_login, name='ecommerce_login'),  # Assurez-vous que le nom est 'login'
    path('ecommerce_signup/', views.ecommerce_signup, name='ecommerce_signup'),
    path('dashboard/', views.ecommerce_dashboard, name='ecommerce_dashboard'),
    path('conditions/', views.conditions, name='conditions'),
    path('conditions/commande/', views.conditions_commande, name='conditions'),
    path('profile/', views.ecommerce_profile, name='profile'),
    path('rewards/', views.ecommerce_rewards, name='rewards'),
    path('referrals/', views.ecommerce_referrals, name='referrals'),
    path('notifications/', views.ecommerce_notifications, name='notifications'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path("envoyer-whatsapp/", views.send_whatsapp_order, name="send_whatsapp_order"),
]