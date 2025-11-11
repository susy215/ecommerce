# 🏠 Página de Inicio SmartSales365

## Descripción
Página corporativa elegante y minimalista que sirve como landing page principal del sistema SmartSales365.

## Características
- ✅ Diseño minimalista y moderno
- ✅ Colorimetría profesional (azul principal)
- ✅ Responsive design (móvil y desktop)
- ✅ Secciones organizadas por categorías
- ✅ Enlaces a toda la documentación
- ✅ Guía rápida de Flutter incluida
- ✅ Animaciones suaves de entrada

## URL de Acceso
- **Local:** http://localhost:8000/
- **Producción:** https://smartsales365.duckdns.org/

## Secciones Principales

### 1. Header
- Logo y descripción del sistema
- Gradiente azul profesional

### 2. Características
- Gestión de Ventas
- Inventario Inteligente
- CRM Avanzado
- Reportes con IA
- Apps Móviles
- Tiempo Real

### 3. Documentación
Organizada en categorías:
- 🚀 **Despliegue**: Guías de AWS, SSL, scripts
- 🎨 **Frontend**: PWA cliente, dashboard admin
- ⚙️ **Backend**: API, Stripe, notificaciones
- 📱 **Flutter**: Apps móviles y voz
- 📊 **Reportes**: IA y auditorías
- 🛠️ **Scripts**: Automatización y utilidades

### 4. Guía Flutter
- Tutorial paso a paso
- Ejemplos de código
- Comandos de voz comunes
- Integración con WebSocket

### 5. API Endpoints
- Lista de endpoints principales
- Descripciones funcionales

## Archivos de Configuración

### URLs (core/urls.py)
```python
urlpatterns = [
    path('', views.home_view, name='home'),  # ← Página de inicio
    path('admin/', admin.site.urls),
    # ... resto de URLs
]
```

### Templates (core/settings.py)
```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'core' / 'templates'],  # ← Directorio de templates
        'APP_DIRS': True,
        # ...
    },
]
```

### Archivos Estáticos
Los archivos de documentación se sirven desde `/media/docs/`:
- `FLUTTER_REPORTES_VOZ_GUIA_COMPLETA.md`
- `FLUTTER_ADMIN_DASHBOARD.md`
- `FRONTEND_CLIENTE_COMPLETO.md`
- `DEPLOY_AWS_EC2.md`

## Personalización

### Cambiar Colores
Modificar las variables CSS en `core/templates/core/home.html`:
```css
:root {
    --primary-color: #2563eb;    /* Azul principal */
    --accent-color: #f59e0b;     /* Amarillo accent */
    --success-color: #10b981;    /* Verde éxito */
}
```

### Agregar Nueva Documentación
1. Copiar archivo a `media/docs/`
2. Agregar entrada en `core/views.py` en la sección `documentacion`

### Modificar Características
Editar la lista `caracteristicas` en `core/views.py`

## Tecnologías Utilizadas
- **HTML5** semántico
- **CSS3** con variables y gradientes
- **JavaScript** vanilla para animaciones
- **Google Fonts** (Inter)
- **Responsive Grid** layout
- **Intersection Observer** para animaciones

## Navegadores Soportados
- ✅ Chrome/Chromium
- ✅ Firefox
- ✅ Safari
- ✅ Edge
- ✅ Mobile browsers

## Próximos Pasos
- [ ] Agregar sección de testimonios
- [ ] Implementar formulario de contacto
- [ ] Añadir galería de screenshots
- [ ] Integrar analytics
- [ ] SEO optimization
