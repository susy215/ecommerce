from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VentaViewSet, VentaItemViewSet

router = DefaultRouter()
router.register(r'ventas', VentaViewSet, basename='venta')
router.register(r'items', VentaItemViewSet, basename='ventaitem')

urlpatterns = [
	path('', include(router.urls)),
]
