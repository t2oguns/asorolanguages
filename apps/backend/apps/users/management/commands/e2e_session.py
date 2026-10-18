from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.test import Client
from apps.users.models import User, UserProfile

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("email")

    def handle(self, *args, email, **opts):
        if not settings.DEBUG:
            raise CommandError("Refusing to run outside DEBUG")
        user, _ = User.objects.get_or_create(email=email)
        UserProfile.objects.get_or_create(user=user, defaults={"display_name": "E2E User"})
        c = Client()
        c.force_login(user)
        self.stdout.write(c.cookies["sessionid"].value)