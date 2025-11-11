"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# core/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.contrib.admin.views.decorators import staff_member_required
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('admin/', admin.site.urls),
    path('api/usuarios/', include('usuarios.urls')),
    path('api/clientes/', include('clientes.urls')),
    path('api/productos/', include('productos.urls')),
    # Nuevo flujo de compras (reemplaza a ventas en los endpoints)
    path('api/compra/', include('compra.urls')),
    # path('api/ventas/', include('ventas.urls')),  # deshabilitado para evitar confusiones
    path('api/reportes/', include('reportes.urls')),
    path('api/ia/', include('ia.urls')),
    path('api/promociones/', include('promociones.urls')),
    path('api/notificaciones/', include('notificaciones.urls')),
    path('api/auth/', include('rest_framework.urls')),
    # API schema & docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # Swagger dentro del admin (solo staff)
    path('admin/api/schema/', staff_member_required(SpectacularAPIView.as_view()), name='admin-schema'),
    path('admin/api/docs/', staff_member_required(SpectacularSwaggerView.as_view(url_name='admin-schema')), name='admin-swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)