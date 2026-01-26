"""
ASGI config for VIMS Backend.
Enables async capabilities for better performance.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vims.settings')

application = get_asgi_application()





