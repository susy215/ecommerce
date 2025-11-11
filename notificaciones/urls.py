"""
URLs para el módulo de notificaciones push.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PushSubscriptionViewSet,
    VAPIDPublicKeyView,
    NotificacionHistorialViewSet
)

router = DefaultRouter()
router.register(r'subscriptions', PushSubscriptionViewSet, basename='push-subscription')
router.register(r'historial', NotificacionHistorialViewSet, basename='notificacion-historial')

urlpatterns = [
    path('', include(router.urls)),
    path('vapid-public-key/', VAPIDPublicKeyView.as_view(), name='vapid-public-key'),
]

