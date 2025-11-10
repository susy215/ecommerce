from django.urls import path
from .views import (
	HealthView, 
	ConsultaIAView, 
	DashboardPrediccionesView,
	EntrenarModeloView,
	HistorialConsultasView
)

urlpatterns = [
	path('health/', HealthView.as_view(), name='ia-health'),
	path('consulta/', ConsultaIAView.as_view(), name='ia-consulta'),
	path('historial/', HistorialConsultasView.as_view(), name='ia-historial'),
	path('dashboard/', DashboardPrediccionesView.as_view(), name='ia-dashboard'),
	path('entrenar-modelo/', EntrenarModeloView.as_view(), name='ia-entrenar-modelo'),
]
