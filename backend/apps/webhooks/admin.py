from django.contrib import admin
from .models import Notificacion, WebhookEvent

admin.site.register(Notificacion)
admin.site.register(WebhookEvent)
