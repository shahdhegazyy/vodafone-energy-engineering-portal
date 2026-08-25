import os
import sys

# Add your project directory to the sys.path
project_home = '/home/PowerDesignHub/vodafone-energy-engineering-portal'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables for production
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
os.environ['DJANGO_SECRET_KEY'] = '*6eutupdr%w+g)w+$!=_+ubm4kz1v1zk0oqxn+5#&64ey+tu%8'
os.environ['DJANGO_DEBUG'] = 'False'
os.environ['DJANGO_ALLOWED_HOSTS'] = 'PowerDesignHub.pythonanywhere.com'

# Serve Django via WSGI
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()