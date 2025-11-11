"""
Vistas principales para la aplicación SmartSales365
"""
from django.shortcuts import render
from django.conf import settings


def home_view(request):
    """
    Página de inicio corporativa elegante
    """
    context = {
        'titulo': 'SmartSales365',
        'subtitulo': 'Sistema Integral de Gestión Comercial',
        'descripcion': 'Plataforma completa para la gestión de ventas, inventario, clientes y reportes con IA avanzada.',

        # Documentación organizada por categorías
        'documentacion': {
            'despliegue': [
                {'titulo': 'Deploy AWS EC2', 'archivo': 'docs/DEPLOY_AWS_EC2.md', 'icono': '🚀'},
                {'titulo': 'Deploy Paso a Paso', 'archivo': 'docs/DEPLOY_AWS_PASO_A_PASO.md', 'icono': '📋'},
                {'titulo': 'Resumen Deploy', 'archivo': 'docs/RESUMEN_DEPLOY_AWS.md', 'icono': '✅'},
                {'titulo': 'Configuración SSL', 'archivo': 'scripts/GUIA_RAPIDA_SSL.md', 'icono': '🔒'},
            ],
            'frontend': [
                {'titulo': 'Frontend Cliente Completo', 'archivo': 'docs/FRONTEND_CLIENTE_COMPLETO.md', 'icono': '📱'},
                {'titulo': 'API Frontend Cliente', 'archivo': 'docs/FRONTEND_CLIENTE_API.md', 'icono': '🔗'},
                {'titulo': 'Dashboard Flutter Admin', 'archivo': 'docs/FLUTTER_ADMIN_DASHBOARD.md', 'icono': '🖥️'},
                {'titulo': 'Reportes Voz Flutter', 'archivo': 'docs/FLUTTER_REPORTES_VOZ.md', 'icono': '🎤'},
            ],
            'backend': [
                {'titulo': 'API Backend', 'archivo': 'SmartSales365 API.yaml', 'icono': '📊'},
                {'titulo': 'Setup Stripe Webhook', 'archivo': 'docs/STRIPE_WEBHOOK_SETUP.md', 'icono': '💳'},
                {'titulo': 'Notificaciones Push', 'archivo': 'docs/NOTIFICACIONES_PUSH.md', 'icono': '📢'},
                {'titulo': 'Promociones y Devoluciones', 'archivo': 'docs/PROMOCIONES_DEVOLUCIONES.md', 'icono': '🏷️'},
            ],
            'flutter': [
                {'titulo': 'Guía Completa Flutter Voz', 'archivo': 'FLUTTER_REPORTES_VOZ_GUIA_COMPLETA.md', 'icono': '📱'},
                {'titulo': 'IA Flutter Voz', 'archivo': 'docs/FLUTTER_IA_VOZ.md', 'icono': '🤖'},
            ],
            'reportes': [
                {'titulo': 'Resumen Reportes', 'archivo': 'docs/RESUMEN_REVISION_REPORTES.md', 'icono': '📈'},
                {'titulo': 'Auditoría Técnica', 'archivo': 'INFORME_AUDITORIA_TECNICA.md', 'icono': '🔍'},
            ],
            'scripts': [
                {'titulo': 'Comandos EC2', 'archivo': 'scripts/COMANDOS_EC2_PASO_A_PASO.sh', 'icono': '⚙️'},
                {'titulo': 'Setup EC2 Completo', 'archivo': 'scripts/SETUP_COMPLETO_EC2.sh', 'icono': '🛠️'},
                {'titulo': 'Verificar Conexión', 'archivo': 'scripts/VERIFICAR_CONEXION.md', 'icono': '🔌'},
                {'titulo': 'Actualizar Imágenes', 'archivo': 'scripts/ACTUALIZAR_IMAGENES_PRODUCTOS.md', 'icono': '🖼️'},
            ]
        },

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
        ],

        # Guía rápida de Flutter
        'flutter_guia': {
            'titulo': '🚀 Guía Rápida: Usar Flutter con Reportes',
            'pasos': [
                {
                    'titulo': '1. Configurar dependencias',
                    'codigo': '''dependencies:
  speech_to_text: ^6.1.1
  dio: ^5.3.2
  path_provider: ^2.1.1
  open_filex: ^4.3.4''',
                    'descripcion': 'Instala las dependencias necesarias para voz y archivos.'
                },
                {
                    'titulo': '2. Inicializar reconocimiento de voz',
                    'codigo': '''final speech = stt.SpeechToText();
await speech.initialize();

final command = await speech.listenForCommand(
  prompt: 'Di tu comando de reporte',
  timeout: const Duration(seconds: 8),
);''',
                    'descripcion': 'Configura el reconocimiento de voz para comandos.'
                },
                {
                    'titulo': '3. Enviar comando a API',
                    'codigo': '''final response = await dio.post(
  '/api/ia/consulta/',
  data: {
    'prompt': command,
    'formato': 'pdf'
  }
);

if (response.data['archivo_url'] != null) {
  // Descargar y abrir archivo
  await openFile(response.data['archivo_url']);
}''',
                    'descripcion': 'Envía el comando de voz a la API y procesa la respuesta.'
                },
                {
                    'titulo': '4. Conectar WebSocket para notificaciones',
                    'codigo': '''final channel = IOWebSocketChannel.connect(
  'ws://tu-servidor/ws/admin/notifications/',
);

channel.stream.listen((message) {
  final data = json.decode(message);
  if (data['type'] == 'notification') {
    showNotification(data['titulo'], data['mensaje']);
  }
});''',
                    'descripcion': 'Conecta al WebSocket para recibir notificaciones en tiempo real.'
                }
            ],
            'ejemplos_comandos': [
                '"Ventas del mes de septiembre en PDF"',
                '"Top 3 productos más vendidos"',
                '"Clientes que más han comprado este año"',
                '"Inventario actual en Excel"'
            ]
        }
    }

    return render(request, 'core/home.html', context)
