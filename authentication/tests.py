from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from .models import CustomUser, PaymentMethod

class PaymentSuccessCinetTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(username='testuser', password='12345', email='testuser@example.com')
        self.referrer = CustomUser.objects.create_user(username='referreruser', password='12345', email='referrer@example.com')
        self.client.login(username='testuser', password='12345')
        self.transaction_id = 'test_transaction_id'
        self.session = self.client.session
        self.session['form_data'] = {
            'username': 'newuser',
            'password': 'hashed_password',
            'contact': '+22899855971',
            'email': 'ninouschcababalima@gmail.com'  # Ajout de l'adresse email
        }
        self.session['referrer_username'] = 'referreruser'
        self.session.save()

    @patch('requests.post')
    def test_payment_success_cinet(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "status": "ACCEPTED",
                "amount": 5000,
                "payment_method": "MOBILE_MONEY"
            }
        }

        response = self.client.get(reverse('authentication:payment_success_cinet'), {'transaction_id': self.transaction_id})
        print(response.content.decode())  # Affiche le contenu de la réponse dans le terminal
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Paiement réussi et compte créé !")
        self.assertTrue(CustomUser.objects.filter(username='newuser').exists())
        self.assertTrue(PaymentMethod.objects.filter(user=self.user).exists())
