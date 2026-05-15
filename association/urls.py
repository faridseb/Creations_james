
from django.urls import path,include
from . import views
from .views import (association_signup, association_login,association_dashboard,creer_association,
                    lister_associations, creer_membre, lister_membres,creer_cotisation,
     lister_cotisations,lister_penalites,
    accueil,connexion_association,
        homepage_association,association_dashboard,comite_dashboard,mes_information,autre_detail
,update_member,update_heritier,situation,objectif6mois,penalite_caisse
,penalite_pret,demande_assistance, demande_pret, inbox,mettre_en_attente_message,
                    accepter_message,rejeter_message,completer_lettre,message_envoye,message_envoye_comite,
                    message_recu_comite,gestion_remboursements,valider_remboursement,loan_payments_view,completed_loans_view
                 ,comptabilite_view  ,custom_logout,send_welcome_sms )
app_name = 'association'
urlpatterns = [

    path('dashboard/comite/', comite_dashboard, name='comite_dashboard'),
    path('mes_information/', mes_information, name='mes_information'),
    path('update_member/', update_member, name='update_member'),
    path('update_heritier/', update_heritier, name='update_heritier'),
    path('autre_detail/', autre_detail, name='autre_detail'),
    path('demande_assistance/', demande_assistance, name='demande_assistance'),
    path('demande_pret/', demande_pret, name='demande_pret'),
    path('loan_payments/', loan_payments_view, name='loan_payments'),
    path('completed_loans/', completed_loans_view, name='completed_loans'),
    path('inbox/', inbox, name='inbox'),
    path('accepter_message/<int:message_id>/', accepter_message, name='accepter_message'),
    path('rejeter_message/<int:message_id>/', rejeter_message, name='rejeter_message'),
    path('mettre_en_attente_message/<int:message_id>/', mettre_en_attente_message,
         name='mettre_en_attente_message'),
    path('gestion_remboursements/', gestion_remboursements, name='gestion_remboursement'),
    path('valider_remboursement/<int:remboursement_id>/', valider_remboursement, name='valider_remboursement'),
    path('message_envoye/', message_envoye, name='message_envoye'),
    path('message_envoye_comite/', message_envoye_comite, name='message_envoye_comite'),
    path('message_recu_comite/', message_recu_comite, name='message_recu_comite'),
    path('completer_lettre/<int:message_id>/', completer_lettre, name='completer_lettre'),
    path('dashboard/association/', association_dashboard, name='association_dashboard'),
    path('associations/<uuid:assoc_uuid>/connexion/', connexion_association, name='connexion_association'),
    # Connexion à l'association
    path('association/<uuid:assoc_uuid>/', homepage_association, name='homepage_association'),
    path('acceuil', accueil, name='accueil'),
    path('association_signup/', association_signup, name='association_signup'),
    path('association_login/', association_login, name='association_login'),
    # Ajoute d'autres URL pour le tableau de bord ou d'autres vues ici
    path('dashboard/', association_dashboard, name='dashboard'),  # Exemple de route pour le tableau de bord
    path('association/<int:association_id>/cotisation/', creer_cotisation, name='creer_cotisation'),
    path('associations/creer/', creer_association, name='creer_association'),
    path('associations/', lister_associations, name='liste_associations'),
    path('membres/creer/', creer_membre, name='creer_membre'),
    path('membres/', lister_membres, name='liste_membres'),
    path('logout/', custom_logout, name='homepage_association'),
    path('cotisations/', lister_cotisations, name='liste_cotisations'),
    path('penalites/', lister_penalites, name='liste_penalites'),
    path('comptabilite/', comptabilite_view, name='comptabilite'),
    path('situation/', situation, name='situation'),
    path('objectif6mois/', objectif6mois, name='objectif6mois'),
    path('penalite_caisse/', penalite_caisse, name='penalite_caisse'),
    path('penalite_pret/', penalite_pret, name='penalite_pret'),
    path('send-welcome-sms/', send_welcome_sms, name='send_welcome_sms'),
]
