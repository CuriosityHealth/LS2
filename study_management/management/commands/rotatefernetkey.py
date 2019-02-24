from django.core.management.base import BaseCommand, CommandError
from study_management.models import Datapoint

class Command(BaseCommand):
    help = 'Rotates the Fernet key to the latest for each Datapoint'

    def handle(self, *args, **options):

        datapoint_encrypted_fields = ['body', 'metadata']

        self.stdout.write(self.style.SUCCESS('Roating %s datapoints' % Datapoint.objects.all().count()))
        
        i = 0
        for datapoint in Datapoint.objects.all():
            datapoint.save(update_fields=datapoint_encrypted_fields, force_update=True)
            i = i + 1

        self.stdout.write(self.style.SUCCESS('Successfully rotated %s datapoints' % i))