# virtual_teacher_project/asgi.py

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import teacher_app.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'virtual_teacher_project.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            teacher_app.routing.websocket_urlpatterns
        )
    ),
})