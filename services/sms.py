from django.conf import settings
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from phonenumber_field.phonenumber import PhoneNumber

# Récupérer les informations Twilio depuis settings.py
account_sid = settings.TWILIO_ACCOUNT_SID
auth_token = settings.TWILIO_AUTH_TOKEN
phone_number = settings.TWILIO_PHONE_NUMBER

client = Client(account_sid, auth_token)


def send_sms(to, message):
    try:
        # Si `to` est un objet PhoneNumber, le convertir en chaîne avec `as_e164`
        if isinstance(to, PhoneNumber):
            to = str(to.as_e164)  # Convertir le numéro de téléphone en chaîne de caractères

        # Validation du numéro de téléphone (exemple simple)
        if not to.startswith('+'):
            raise ValueError("Le numéro de téléphone doit être au format international, commençant par '+'.")

        # Envoi du message via Twilio
        message = client.messages.create(
            body=message,
            from_=phone_number,  # Le numéro Twilio que vous avez acheté
            to=to  # Le numéro du destinataire
        )
        return message.sid
    except TwilioRestException as e:
        print(f"Erreur Twilio : {e}")
        return None
    except ValueError as e:
        print(f"Erreur de validation : {e}")
        return None
