from django.core.management.base import BaseCommand
from association.models import AssociationUser, Carnet
from decimal import Decimal

class Command(BaseCommand):
    help = 'Met à jour les informations des carnets existants'

    def handle(self, *args, **kwargs):
        utilisateurs = AssociationUser.objects.all()
        for utilisateur in utilisateurs:
            self.mettre_a_jour_carnets(utilisateur)
        self.stdout.write(self.style.SUCCESS('Mise à jour des carnets terminée.'))

    def mettre_a_jour_carnets(self, utilisateur):
        carnets = Carnet.objects.filter(utilisateur=utilisateur).order_by('annee', 'semestre')

        previous_total_sociale = Decimal('0.00')
        previous_total_lucrative = Decimal('0.00')

        for carnet in carnets:
            total_cotisation = carnet.total_cotisation
            part_sociale = total_cotisation * Decimal('0.25')
            part_lucrative = total_cotisation * Decimal('0.75')

            ancien_total_sociale = previous_total_sociale
            ancien_total_lucrative = previous_total_lucrative
            nouveau_total_sociale = part_sociale
            nouveau_total_lucrative = part_lucrative

            total_sociale = ancien_total_sociale + nouveau_total_sociale
            total_lucrative = ancien_total_lucrative + nouveau_total_lucrative

            carnet.part_sociale = part_sociale
            carnet.part_lucrative = part_lucrative
            carnet.total_sociale = total_sociale
            carnet.total_lucrative = total_lucrative
            carnet.save()

            previous_total_sociale = total_sociale
            previous_total_lucrative = total_lucrative