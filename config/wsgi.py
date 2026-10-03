"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/stable/howto/deployment/wsgi/
"""

import os

# Keep bytecode out of the repo; must happen before Django is imported.
os.environ.setdefault(
    "PYTHONPYCACHEPREFIX",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".cache", "python"),
)

from django.core.wsgi import get_wsgi_application  # noqa: E402

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
