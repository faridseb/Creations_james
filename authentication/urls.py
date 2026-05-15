from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from .views import (
    UserLoginView, user_logout, UserDashboardView,
    register_referral, transaction_history, edit_profile,
    view_referrals, view_wallet, setting, logout_user,
    referral_statistics, rewards, referral_codes, trends_and_charts,
    notifications, support,view_profile,edit_profile_picture,
    user_signup,userlink_signup,create_checkout_session, paypal_payment,
    stripe_payment_success,confirm_referral_payment,
    ConfirmReferralsView,confirm_payment_ref,success,cancel
,error,create_checkout_session,mark_as_read,delete_notification,get_unread_messages_count,
initiate_payment_cinet, payment_success_cinet,payment_error_cinet,payment_notify,
    password_reset_request, password_reset_done, password_reset_confirm,donateurs_list,
    success_projet,create_checkout_session_projet,wallet_payment_success,
    verify_wallet_payment,cinetpay_webhook,retrait_view
)

app_name = 'authentication'

urlpatterns = [
    # Connexion et déconnexion des utilisateurs
    path('login/', UserLoginView.as_view(), name='user_login'),
    path('logout/', user_logout, name='user_logout'),
    path('create-checkout-session-projet/<int:projet_id>/', create_checkout_session_projet, name='create_checkout_session_projet'),  #
    path('success/', success, name='success'),  # Page de succès
    path('success-projet/', success_projet, name='success_projet'),  # Page de succès
    path('cancel/', cancel, name='cancel'),    # Page d'annulation
    path('error/', error, name='error'),
    #path('mot-de-passe-oublie/', PasswordResetView.as_view(), name='password_reset'),
    # Tableaux de bord

    path('wallet/payment/', wallet_payment_success, name='payment'),
    path('wallet/payment/success/', wallet_payment_success, name='wallet_payment_success'),
    path('projet-don/', donateurs_list, name='projet_don'),
    path('user_dashboard/', UserDashboardView.as_view(), name='user_dashboard'),
    path('unread_messages_count/', get_unread_messages_count, name='unread_messages_count'),
    # Inscription d'un filleul
    path('register_referral/', register_referral, name='register_referral'),
    path('user_signup/', user_signup, name='user_signup'),
    path('userlink_signup/', userlink_signup, name='userlink_signup'),
    path('confirm-payment-ref/<uuid:referral_uuid>/', confirm_payment_ref, name='confirmation_inscription_ref'),
    path('confirm-referrals/', ConfirmReferralsView.as_view(), name='confirm_referrals'),
    path('confirm-payment/', confirm_referral_payment, name='confirm_referral_payment'),
    # Effectuer un paiement
    path("initiate_payment_cinet/", initiate_payment_cinet, name="initiate_payment_cinet"),
    path("payment_success_cinet/", payment_success_cinet, name="payment_success_cinet"),
    path("payment-error-cinet/", payment_error_cinet, name="payment_error_cinet"),
    path('payment-notify/', payment_notify, name='payment_notify'),
   # Sélection du moyen de paiement
    path('create-checkout-session/', create_checkout_session, name='create_checkout_session'),  # Stripe session
    path('paypal/payment/', paypal_payment, name='paypal_payment'),  # Paiement via PayPal
    path("webhook/cinetpay/", cinetpay_webhook, name="cinetpay_webhook"),
    path('payment/success/', stripe_payment_success, name='stripe_payment_success'),
    path('cancel/', TemplateView.as_view(template_name='authentication/error.html'), name='error'),
    path('logout/', logout_user, name='logout'),
    path('retrait/', retrait_view, name='retrait'),
    # Historique des transactions
    path('transaction_history/', transaction_history, name='transaction_history'),

    # Modification du profil
    path('edit_profile/', edit_profile, name='edit_profile'),

    # Voir les filleuls
    path('view_referrals/', view_referrals, name='view_referrals'),

    # Voir le portefeuille
    path('view_wallet/', view_wallet, name='view_wallet'),

    # Paramètres
    path('settings/', setting, name='settings'),
    path('payment/', create_checkout_session, name='payment'),
    # Nouvelles vues
    path('referral_statistics/', referral_statistics, name='referral_statistics'),
    path('rewards/', rewards, name='rewards'),
    path('referral_codes/', referral_codes, name='referral_codes'),
    path('trends_and_charts/', trends_and_charts, name='trends_and_charts'),
    path('notifications/', notifications, name='notifications'),
    path('notifications/mark_as_read/<uuid:notification_uuid>/', mark_as_read, name='mark_as_read'),
    path('notifications/delete/<uuid:notification_uuid>/', delete_notification, name='delete_notification'),
    path('support/', support, name='support'),
    path('view_profile/', view_profile, name='view_profile'),
    path('edit-profile-picture/', edit_profile_picture, name='edit_profile_picture'),
    path('mot-de-passe-oublie/', password_reset_request, name='password_reset_form'),
    path('mot-de-passe-oublie/envoye/', password_reset_done, name='password_reset_done'),
    path('mot-de-passe-oublie/<uidb64>/<token>/', password_reset_confirm, name='password_reset_confirm'),

]
# Servir les fichiers statiques pendant le développement
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)