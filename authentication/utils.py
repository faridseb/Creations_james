# authentication/utils.py
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import Wallet, Stage, Referral as ReferralModel
from collections import defaultdict
from datetime import datetime
from collections import deque
from .models import Notification
User = get_user_model()
from django.core.mail import send_mail


def send_notification(user, message):
    subject = 'Nouvelle notification'
    message = f'Bonjour {user.username},\n\n{message}'
    send_mail(subject, message, 'from@example.com', [user.email])

class ReferralNode:
    def __init__(self, id, date_joined, parent=None):
        self.id = id
        self.date_joined = date_joined
        self.parent = parent
        self.children = []

def generate_referral_tree():
    all_referrals = ReferralModel.objects.all().order_by('date_joined')

    rows = [
        [None],  # Ligne 1: 1 case pour le parrain principal
        [None] * 10,  # Ligne 2: 10 cases pour les filleuls directs
        [None] * 19,  # Ligne 3: 19 cases
        [None] * 28,  # Ligne 4: 28 cases
        [None] * 37,  # Ligne 5: 37 cases
        [None] * 46,  # Ligne 6: 46 cases
        [None] * 55  # Ligne 7: 55 cases
    ]

    placed_users = set()

    def find_referrer_index(referrer):
        for row_index in range(len(rows)):
            if referrer in rows[row_index]:
                return row_index, rows[row_index].index(referrer)
        return None, None

    def place_user(referral_user):
        if referral_user in placed_users:
            return False

        for row_index in range(1, len(rows)):
            referrer_row_index, referrer_index = find_referrer_index(referral_user.referrer)
            if referrer_row_index is not None and row_index >= referrer_row_index + 1:
                segment_start = referrer_index * (row_index - referrer_row_index)
                segment_end = segment_start + 10

                if segment_end > len(rows[row_index]):
                    segment_end = len(rows[row_index])

                placed = False
                while segment_start < len(rows[row_index]):
                    for col_index in range(segment_start, segment_end):
                        if rows[row_index][col_index] is None:
                            rows[row_index][col_index] = referral_user
                            placed_users.add(referral_user)
                            placed = True
                            break

                    if placed:
                        return True

                    row_index += 1
                    segment_start = 0
                    segment_end = 10
                    if row_index >= len(rows):
                        break

        return False

    primary_referral = all_referrals.first().referrer
    rows[0][0] = primary_referral
    placed_users.add(primary_referral)

    direct_referrals = ReferralModel.objects.filter(referrer=primary_referral).order_by('date_joined')
    direct_referral_users = [referral.referred_user for referral in direct_referrals if referral.referred_user]

    for i, referral_user in enumerate(direct_referral_users[:10]):
        rows[1][i] = referral_user
        placed_users.add(referral_user)

    def get_remaining_referrals(start_row_index):
        remaining_referrals = []
        for row_index in range(start_row_index):
            for user in rows[row_index]:
                if user:
                    remaining_referrals.extend(
                        ReferralModel.objects.filter(referrer=user).order_by('date_joined')
                    )
        return remaining_referrals

    for row_index in range(2, len(rows)):
        remaining_referrals = get_remaining_referrals(row_index)

        all_referrals_to_place = sorted(
            [referral.referred_user for referral in remaining_referrals if
             referral.referred_user and referral.referred_user not in placed_users],
            key=lambda x: x.date_joined
        )

        grandchildren_queue = deque(all_referrals_to_place)

        while grandchildren_queue:
            referral_user = grandchildren_queue.popleft()
            if not place_user(referral_user):
                print(f"Erreur de placement pour {referral_user}")

    return rows
def calculate_field_of_action(parent_index, current_index):
    return (parent_index * 10, parent_index * 10 + 10)

def place_referrals(referrals):
    placement = defaultdict(lambda: [None] * 100)  # Initialisation avec une grande liste de slots
    sorted_referrals = sorted(referrals, key=lambda r: r.date_joined)

    for ref in sorted_referrals:
        if ref.parent:
            parent_index = len([r for r in placement[ref.parent] if r])  # Compte des enfants déjà placés
            field_of_action = calculate_field_of_action(parent_index, len(placement[ref.parent]))

            placed = False
            for i in range(field_of_action[0], field_of_action[1]):
                if i >= len(placement[ref.parent]):
                    placement[ref.parent].append(None)
                if not placement[ref.parent][i]:
                    placement[ref.parent][i] = ref
                    placed = True
                    break

            if not placed:
                print(f"Unable to place referral {ref.id} within the field of action.")

    return placement

def update_grand_parrain_reward(user):
    try:
        stage = Stage.objects.get(user=user)
        # Votre logique pour mettre à jour la récompense du grand parrain
    except Stage.DoesNotExist:
        pass  # Gérez le cas où le Stage n'existe pas pour cet utilisateur

def get_grand_parrain(user):
    """
    Récupère le grand parrain de l'utilisateur.
    """
    try:
        # Obtention du parrain de l'utilisateur
        referral = ReferralModel.objects.get(referred=user)
        # Obtention du grand parrain à partir du parrain
        grand_parrain = ReferralModel.objects.get(referred=referral.referrer).referrer
        return grand_parrain
    except ReferralModel.DoesNotExist:
        return None

def get_stage_reward(stage):
    """
    Récupère le montant de la récompense pour un stage donné.
    """
    rewards = {
        1: 1500,
        2: 5100,
        3: 15300,
        4: 45900,
        5: 137700,
        6: 413100,
        7: 1229300,
        8: 3717700,
        9: 11133700,
        10: 33461100,
    }
    return rewards.get(stage, 0)

def process_payment(user, amount, payment_method):
    """
    Traite un paiement pour l'utilisateur et met à jour la grande caisse.
    """
    if payment_method not in ['moov_money', 'tmoney', 'bank']:
        raise ValueError("Méthode de paiement invalide")

    # Enregistrez le paiement dans la grande caisse
    try:
        caisse = Wallet.objects.get(
            user=User.objects.get(id=settings.SUPER_USER_ID))  # Utilisez l'ID de la grande caisse configurée
    except Wallet.DoesNotExist:
        raise ValueError("Le portefeuille de la grande caisse n'existe pas")

    caisse.balance += amount
    caisse.save()

    # Ajoutez également le montant au portefeuille de l'utilisateur si nécessaire
    try:
        user_wallet = Wallet.objects.get(user=user)
    except Wallet.DoesNotExist:
        raise ValueError("Le portefeuille de l'utilisateur n'existe pas")

    user_wallet.balance += amount
    user_wallet.save()

def build_referral_tree():
    User = get_user_model()
    all_referrals = ReferralModel.objects.all().order_by('date_joined')

    rows = [
        [None],  # Ligne 1: 1 case pour le parrain principal
        [None] * 10,  # Ligne 2: 10 cases pour les filleuls directs
        [None] * 19,  # Ligne 3: 19 cases
        [None] * 28,  # Ligne 4: 28 cases
        [None] * 37,  # Ligne 5: 37 cases
        [None] * 46,  # Ligne 6: 46 cases
        [None] * 55  # Ligne 7: 55 cases
    ]

    placed_users = set()

    def find_referrer_index(referrer):
        for row_index in range(len(rows)):
            if referrer in rows[row_index]:
                return row_index, rows[row_index].index(referrer)
        return None, None

    def place_user(referral_user):
        if referral_user in placed_users:
            return False

        for row_index in range(1, len(rows)):
            referrer_row_index, referrer_index = find_referrer_index(referral_user.referrer)
            if referrer_row_index is not None and row_index >= referrer_row_index + 1:
                segment_start = referrer_index * (row_index - referrer_row_index)
                segment_end = segment_start + 10

                if segment_end > len(rows[row_index]):
                    segment_end = len(rows[row_index])

                placed = False
                while segment_start < len(rows[row_index]):
                    for col_index in range(segment_start, segment_end):
                        if rows[row_index][col_index] is None:
                            rows[row_index][col_index] = referral_user
                            placed_users.add(referral_user)
                            placed = True
                            break

                    if placed:
                        return True

                    row_index += 1
                    segment_start = 0
                    segment_end = 10
                    if row_index >= len(rows):
                        break

        return False

    primary_referral = all_referrals.first().referrer
    rows[0][0] = primary_referral
    placed_users.add(primary_referral)

    direct_referrals = ReferralModel.objects.filter(referrer=primary_referral).order_by('date_joined')
    direct_referral_users = [referral.referred_user for referral in direct_referrals if referral.referred_user]

    for i, referral_user in enumerate(direct_referral_users[:10]):
        rows[1][i] = referral_user
        placed_users.add(referral_user)

    def get_remaining_referrals(start_row_index):
        remaining_referrals = []
        for row_index in range(start_row_index):
            for user in rows[row_index]:
                if user:
                    remaining_referrals.extend(
                        ReferralModel.objects.filter(referrer=user).order_by('date_joined')
                    )
        return remaining_referrals

    for row_index in range(2, len(rows)):
        remaining_referrals = get_remaining_referrals(row_index)

        all_referrals_to_place = sorted(
            [referral.referred_user for referral in remaining_referrals if
             referral.referred_user and referral.referred_user not in placed_users],
            key=lambda x: x.date_joined
        )

        grandchildren_queue = deque(all_referrals_to_place)

        while grandchildren_queue:
            referral_user = grandchildren_queue.popleft()
            if not place_user(referral_user):
                print(f"Erreur de placement pour {referral_user}")

    return rows


def calculate_slots(rows):
    """
    Calcule le nombre de cases pleines et vides dans les lignes données.
    """
    filled_slots = 0
    empty_slots = 0
    for row in rows:
        filled_slots += sum(1 for slot in row if slot is not None)
        empty_slots += sum(1 for slot in row if slot is None)
    return filled_slots, empty_slots

def check_and_notify_user(user):
    referral_tree = generate_referral_tree()
    filled_slots, empty_slots = calculate_slots(referral_tree)

    total_slots = 20  # Total des slots à vérifier, ajustez si nécessaire

    if filled_slots >= total_slots:
        # Envoyer la notification
        message = "Félicitations ! Vous avez rempli toutes les cases disponibles et allez passer au stade suivant."
        Notification.objects.create(user=user, message=message)

        # Logique pour passer au stade suivant
        try:
            stage = Stage.objects.get(user=user)
            stage.current_stage += 1  # Assurez-vous d'avoir une logique pour passer au stade suivant
            stage.save()
        except Stage.DoesNotExist:
            pass  # Gérez le cas où le Stage n'existe pas pour cet utilisateur

    return filled_slots, empty_slots

def create_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(user=instance)

def check_and_update_stage(user_profile_id):
    user_profile = get_object_or_404(UserProfile, id=user_profile_id)
    current_stage = user_profile.stage
    next_stage = Stage.objects.filter(id__gt=current_stage.id).order_by('id').first()

    # Vérifiez si le nombre de slots remplis a atteint le seuil pour passer au stade supérieur
    if user_profile.filled_slots >= current_stage.total_slots:
        if next_stage:
            user_profile.stage = next_stage
            user_profile.save()

            # Création de la notification
            Notification.objects.create(
                user=user_profile.user,
                message=f"Félicitations! Vous avez atteint le stade {next_stage.name}."
            )
def create_notification(user, message):
    Notification.objects.create(user=user, message=message)