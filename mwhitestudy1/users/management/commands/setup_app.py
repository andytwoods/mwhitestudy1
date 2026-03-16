from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string

User = get_user_model()


class Command(BaseCommand):
    help = "Idempotent production setup: create superuser and bootstrap study."

    def handle(self, *args, **kwargs):
        self._create_superuser()
        self._bootstrap_study()

    def _create_superuser(self):
        email = "andytwoods@gmail.com"
        new_password = get_random_string(10)
        try:
            if not User.objects.filter(is_superuser=True).exists():
                self.stdout.write("No superusers found, creating one")
                User.objects.create_superuser(email=email, password=new_password)
                self.stdout.write("=======================")
                self.stdout.write("A superuser has been created")
                self.stdout.write(f"Email: {email}")
                self.stdout.write(f"Password: {new_password}")
                self.stdout.write("=======================")
            else:
                self.stdout.write("A superuser exists in the database. Skipping.")
        except Exception as e:
            self.stderr.write(f"There was an error creating superuser: {e}")

    def _bootstrap_study(self):
        """Run bootstrap_study to create Study, Conditions, and Questions."""
        try:
            call_command("bootstrap_study", verbosity=1)
        except Exception as e:
            self.stderr.write(f"There was an error bootstrapping the study: {e}")
