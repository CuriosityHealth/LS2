from django.core.management.base import BaseCommand, CommandError
from study_management.models import Datapoint
from cryptography.fernet import Fernet
import base64

class Command(BaseCommand):
    help = 'Generates a new Fernet key'

    def handle(self, *args, **options):

        key = Fernet.generate_key()
        self.stdout.write(self.style.SUCCESS(key))