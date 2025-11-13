from django.urls import path
from . import views

urlpatterns = [
    path('avanzados/', views.ReportesDinamicosAvanzadosView.as_view(), name='reportes-dinamicos-avanzados'),
]
