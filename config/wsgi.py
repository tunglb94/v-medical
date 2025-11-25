"""
WSGI config for crm_clinic_system project.
"""

import os

from django.core.wsgi import get_wsgi_application

# Trỏ về file cài đặt settings của chúng ta
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()