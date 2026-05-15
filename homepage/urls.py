# homepage/urls.py
from django.urls import path,include
from . import views
app_name = 'homepage'
urlpatterns = [
    path('', views.home, name='home'),
    path('bibliographie/', views.bibliographie, name='bibliographie'),
    path('formation/', views.formation, name='formation'),
    path('oeuvreSocial/', views.oeuvreSocial, name='oeuvreSocial'),
    path('search/', views.search, name='search'),
    path('educationEconomie/', views.educationEconomie, name='educationEconomie'),
    path('artisEntrep/', views.artisEntrep, name='artisEntrep'),
    path('politique/', views.politique, name='politique'),
    path('login/', views.connexion, name='login'),
    path('adherer/', views.adherer, name='adherer'),
    path('sante/', views.sante, name='sante'),
    path('leadershipMF/', views.leadershipMF, name='leadershipMF'),
    # Ajoutez cette ligne si ce n'est pas déjà fait
    path('donateurs/', views.donateurs_list, name='donateurs_list'),
    path('sponsors/', views.sponsors_list, name='sponsors_list'),
    path("whatsapp/", views.whatsapp_redirect, name="whatsapp_redirect"),
    path('bienfaiteurs/', views.bienfaiteurs_list, name='bienfaiteurs_list'),
    path('torpilleurs/', views.torpilleurs_list, name='torpilleurs_list'),

 path("connection/", views.user_login, name="connection"),
    path("register/", views.user_register, name="inscription"),
    path("logout/", views.user_logout, name="logout"),

    path('dashboard/', views.user_dashboard, name='user_dashboard'),

    # URL pour faire un don
    path('faire-un-don/<int:projet_id>/', views.faire_un_don, name='faire_un_don'),

    # URL pour sponsoriser un projet
    path('sponsoriser-un-projet/<int:projet_id>/', views.sponsoriser_un_projet, name='sponsoriser_un_projet'),

    # URL pour être bienfaiteur d'un projet
    path('etre-bienfaiteur/<int:projet_id>/', views.etre_bienfaiteur, name='etre_bienfaiteur'),


]
