from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UsuarioViewSet, RegisterView, EmailOrUsernameTokenView

router = DefaultRouter()
router.register(r'', UsuarioViewSet, basename='usuario')

urlpatterns = [
	# Endpoints específicos primero para evitar colisión con lookup del router
	path('register/', RegisterView.as_view(), name='register'),
	path('token/', EmailOrUsernameTokenView.as_view(), name='token-obtain'),
	path('', include(router.urls)),
]
