"""
Vistas principales para la aplicación SmartSales365
"""
from django.shortcuts import render
from django.conf import settings


def home_view(request):
    """
    Página de inicio corporativa minimalista
    """
    context = {
        'titulo': 'SmartSales365',
        'subtitulo': 'Sistema Integral de Gestión Comercial',
        'descripcion': 'Plataforma completa para la gestión de ventas, inventario, clientes y reportes con IA avanzada.',

        # Características principales
        'caracteristicas': [
            {
                'icono': '🛒',
                'titulo': 'Gestión de Ventas',
                'descripcion': 'Sistema completo para procesar pedidos, pagos con Stripe y seguimiento de envíos.'
            },
            {
                'icono': '📦',
                'titulo': 'Inventario Inteligente',
                'descripcion': 'Control automático de stock, alertas de faltantes y optimización de existencias.'
            },
            {
                'icono': '👥',
                'titulo': 'CRM Avanzado',
                'descripcion': 'Gestión de clientes con historial completo y segmentación automática.'
            },
            {
                'icono': '📊',
                'titulo': 'Reportes con IA',
                'descripcion': 'Genera reportes avanzados mediante comandos de voz naturales.'
            },
            {
                'icono': '📱',
                'titulo': 'Apps Móviles',
                'descripcion': 'Aplicaciones nativas para clientes y administradores con notificaciones push.'
            },
            {
                'icono': '🔄',
                'titulo': 'Tiempo Real',
                'descripcion': 'WebSockets para notificaciones instantáneas y dashboard en vivo.'
            }
        ],

        # API Endpoints principales
        'apis': [
            {'endpoint': '/api/productos/', 'descripcion': 'Gestión de productos'},
            {'endpoint': '/api/compras/', 'descripcion': 'Procesamiento de compras'},
            {'endpoint': '/api/clientes/', 'descripcion': 'Administración de clientes'},
            {'endpoint': '/api/ia/consulta/', 'descripcion': 'Reportes con IA'},
            {'endpoint': '/api/notificaciones/', 'descripcion': 'Sistema de notificaciones'},
            {'endpoint': '/admin/', 'descripcion': 'Panel de administración'},
        ]
    }

    return render(request, 'core/home.html', context)