import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'charapp.settings')  # Must be FIRST
import django
django.setup()  # Explicit setup call

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from chat import routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter(routing.websocket_urlpatterns),
})