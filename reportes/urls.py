from django.urls import path
from .views import (
    SummaryReportView,
    KPIReportView,
    VentasPorDiaView,
    VentasPorCategoriaView,
    VentasPorProductoView,
    TopClientesView,
    HealthReportView,
)

urlpatterns = [
    path('summary/', SummaryReportView.as_view(), name='report-summary'),
    path('kpis/', KPIReportView.as_view(), name='report-kpis'),
    path('series/ventas-por-dia/', VentasPorDiaView.as_view(), name='report-ventas-por-dia'),
    path('ventas/por-categoria/', VentasPorCategoriaView.as_view(), name='report-ventas-por-categoria'),
    path('ventas/por-producto/', VentasPorProductoView.as_view(), name='report-ventas-por-producto'),
    path('ventas/top-clientes/', TopClientesView.as_view(), name='report-top-clientes'),
    path('health/', HealthReportView.as_view(), name='report-health'),
]
