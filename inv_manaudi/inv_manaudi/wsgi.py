import os
import sys

# Añadir la ruta de tu proyecto al sys.path
project_home = '/home/rolansor/inventariosmanaudi/inv_manaudi'
if project_home not in sys.path:
    sys.path.append(project_home)

# Establecer el módulo de configuración de Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'inv_manaudi.settings'

# Obtener la aplicación WSGI de Django
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
