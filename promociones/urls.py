from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PromocionViewSet, DevolucionProductoViewSet

router = DefaultRouter()
router.register(r'promociones', PromocionViewSet, basename='promocion')
router.register(r'devoluciones', DevolucionProductoViewSet, basename='devolucion')

urlpatterns = [
    path('', include(router.urls)),
]
