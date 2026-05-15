from celery import shared_task
from django.core.mail import send_mail
from django.utils.timezone import now
from .models import CustomUser

@shared_task
def send_reminder_email(user_id, days_left):
    try:
        user = CustomUser.objects.get(id=user_id)
        if not user.is_confirmed:  # Envoyer seulement si non confirmé
            send_mail(
                'Rappel de confirmation',
                f'Bonjour {user.username},\n'
                f'Il vous reste {days_left} jours pour confirmer votre compte. '
                f'Si vous ne confirmez pas votre compte d\'ici {days_left} jours, il sera supprimé.',
                'noreply@votreapp.com',
                [user.email],
            )
    except CustomUser.DoesNotExist:
        pass  # L'utilisateur a peut-être déjà été supprimé

@shared_task
def delete_unconfirmed_account(user_id):
    try:
        user = CustomUser.objects.get(id=user_id)
        if not user.is_confirmed:  # Supprimer seulement si non confirmé
            user.delete()
    except CustomUser.DoesNotExist:
        pass  # L'utilisateur a peut-être déjà été supprimé
