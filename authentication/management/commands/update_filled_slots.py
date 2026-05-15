from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from authentication.models import Referral
from django.utils import timezone

class Command(BaseCommand):
    help = "Génère les arbres pour chaque stage et met à jour les slots et stages"

    def handle(self, *args, **options):
        User = get_user_model()
        # 🔁 Étape 1 : Réinitialiser les filled_slots à 0
        User.objects.update(filled_slots=0)
        Referral.objects.update(filled_slots=0)
        self.stdout.write(self.style.WARNING("✅ Tous les 'filled_slots' ont été réinitialisés à 0."))

        stages = {
            1: 17,
            2: 10,
            3: 12,
            4: 14,
            5: 16,
            6: 18,
            7: 20,
            8: 22,
            9: 24,
            10: 26
        }

        for stage, num_lignes in stages.items():
            self.stdout.write(f"🔄 Traitement du stage {stage}...")

            rows = []
            for i in range(num_lignes):
                num_cases = 1 if i == 0 else 10 + (i - 1) * 9
                rows.append([None] * num_cases)

            if stage == 1:
                self.handle_stage_1(rows, User)
            else:
                self.handle_stage_n(rows, stage, User)

    def handle_stage_1(self, rows, User):
        first_user = User.objects.exclude(is_superuser=True).order_by('date_joined').first()
        if first_user:
            rows[0][0] = first_user

        referrals = Referral.objects.all().order_by('date_joined')

        for referral in referrals:
            user = referral.referred
            referrer = referral.referrer

            referrer_position = self.find_user_position(rows, referrer)
            if not referrer_position:
                continue

            row_index, col_index = referrer_position
            placed = False
            for i in range(row_index + 1, len(rows)):
                start = col_index
                end = min(start + 10, len(rows[i]))
                for j in range(start, end):
                    if rows[i][j] is None:
                        rows[i][j] = user
                        placed = True
                        break
                if placed:
                    break

        self.update_filled_slots(rows, stage=1)

    def handle_stage_n(self, rows, stage, User):
        threshold = 20 * (stage - 1)
        referrals = Referral.objects.filter(filled_slots__gte=threshold)

        for referral in referrals:
            user = referral.referred_user
            if user:
                self.place_user_stage_n(rows, user)

        self.update_filled_slots(rows, stage)

    def place_user_stage_n(self, rows, user):
        try:
            referral = Referral.objects.get(referred=user)
            sponsor = referral.referrer
        except Referral.DoesNotExist:
            sponsor = None

        sponsor_position = self.find_user_position(rows, sponsor)
        if sponsor_position:
            row_index, col_index = sponsor_position
            for i in range(row_index + 1, len(rows)):
                start = col_index if i == row_index + 1 else 0
                end = min(start + 10, len(rows[i]))
                for j in range(start, end):
                    if rows[i][j] is None:
                        rows[i][j] = user
                        return

        for row in rows:
            for i in range(len(row)):
                if row[i] is None:
                    row[i] = user
                    return

    def find_user_position(self, rows, user):
        for row_index, row in enumerate(rows):
            for col_index, val in enumerate(row):
                if val == user:
                    return (row_index, col_index)
        return None

    def update_filled_slots(self, rows, stage):
        thresholds = {
            1: 20,
            2: 40,
            3: 60,
            4: 80,
            5: 100,
            6: 120,
            7: 140,
            8: 160,
            9: 180,
            10: 200
        }

        for row_index, row in enumerate(rows):
            for col_index, user in enumerate(row):
                if not user:
                    continue

                slots_below = []
                for offset in range(1, 3):
                    next_row = row_index + offset
                    if next_row < len(rows):
                        start = col_index
                        end = min(start + 10, len(rows[next_row]))
                        slots_below.extend(rows[next_row][start:end])

                filled = sum(1 for u in slots_below if u)

                try:
                    referral = Referral.objects.get(referred=user)
                    referral.filled_slots += filled
                    referral.save()

                    user.filled_slots += filled
                    user.save()

                    if stage in thresholds and filled >= thresholds[stage]:
                        referral.stage = stage + 1
                        referral.save()
                        self.stdout.write(self.style.SUCCESS(f"✅ {user} passe au stage {stage + 1}"))
                    else:
                        self.stdout.write(f"ℹ️ {user} a {filled} slots.")
                except Referral.DoesNotExist:
                    continue
