from django.urls import path
from .views import HealthView, ConsultaIAView

urlpatterns = [
	path('health/', HealthView.as_view(), name='ia-health'),
	path('consulta/', ConsultaIAView.as_view(), name='ia-consulta'),
]
