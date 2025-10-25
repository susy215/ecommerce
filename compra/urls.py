from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompraViewSet, StripeWebhookView, CompraReceiptView

router = DefaultRouter()
router.register(r'compras', CompraViewSet, basename='compra')

urlpatterns = [
    path('', include(router.urls)),
    path('stripe/webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path('compras/<int:pk>/receipt/', CompraReceiptView.as_view(), name='compra-receipt'),
]
