#parti/urls.py
from django.urls import path,include
from . import views
from .views import parti_signup, parti_login,politique,payment_success,parti_dashboard,payment_failed
app_name = 'parti'
urlpatterns = [
    path('politique/', politique, name='politique'),
    path('parti_signup/', parti_signup, name='parti_signup'),
    path('login/', parti_login, name='login'),
    path('payment_success/', payment_success, name='payment_success'),
    path('initiate/', views.initiate_payment, name='initiate_payment'),
    path('dashboard/', parti_dashboard, name='parti_dashboard'),  # Exemple de route pour le tableau de bord
    path('payment/failed/', payment_failed, name='payment_failed')

]
