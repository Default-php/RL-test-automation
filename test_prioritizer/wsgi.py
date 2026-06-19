"""WSGI entry point for the Django application."""
import os

from django.core.wsgi import get_wsgi_application


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_prioritizer.settings")

application = get_wsgi_application()
