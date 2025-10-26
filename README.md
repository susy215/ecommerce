# SmartSales365 - Sistema de Gestión de Ventas

Sistema de gestión de ventas e-commerce desarrollado con Django REST Framework y PostgreSQL.

## 🚀 Características

- ✅ Autenticación con Token (DRF)
- ✅ Gestión de productos y categorías
- ✅ Sistema de compras con carrito
- ✅ Integración con Stripe para pagos
- ✅ Gestión de clientes
- ✅ Reportes y estadísticas
- ✅ Generación de comprobantes PDF
- ✅ API RESTful documentada con Swagger
- ✅ Validación de stock automática
- ✅ Webhooks de Stripe

## 📋 Requisitos Previos

- Python 3.10+
- PostgreSQL 13+
- pip y virtualenv

## 🔧 Instalación

### 1. Clonar el repositorio

```bash
git clone <tu-repositorio>
cd smartsales365
```

### 2. Crear entorno virtual

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Instalar dependencias

```powershell
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copia el archivo `.env.example` a `.env` y configura tus credenciales:

```powershell
Copy-Item .env.example .env
```

Edita `.env` con tus valores:

```env
# Django
DJANGO_SECRET_KEY=tu-clave-secreta-aqui
DJANGO_DEBUG=True

# Base de datos
DB_NAME=smartsales_db
DB_USER=postgres
DB_PASSWORD=tu-password
DB_HOST=localhost
DB_PORT=5432

# Stripe (opcional)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### 5. Crear base de datos

```sql
-- En PostgreSQL
CREATE DATABASE smartsales_db;
```

### 6. Ejecutar migraciones

```powershell
python manage.py migrate
```

### 7. Crear superusuario

```powershell
python manage.py createsuperuser
```

### 8. Datos de prueba (opcional)

```powershell
python manage.py seed_demo
```

### 9. Ejecutar servidor

```powershell
python manage.py runserver
```

## 📚 Documentación de la API

Una vez que el servidor esté corriendo, accede a:

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/schema/
- **Admin**: http://localhost:8000/admin/

## 🔑 Endpoints Principales

### Autenticación

```http
POST /api/usuarios/register/
POST /api/usuarios/token/
GET  /api/usuarios/me/
```

### Productos

```http
GET    /api/productos/productos/
POST   /api/productos/productos/
GET    /api/productos/productos/{id}/
PUT    /api/productos/productos/{id}/
DELETE /api/productos/productos/{id}/
```

### Compras

```http
GET  /api/compra/compras/
POST /api/compra/compras/checkout/
POST /api/compra/compras/{id}/pay/
POST /api/compra/compras/{id}/stripe_session/
GET  /api/compra/compras/{id}/receipt/
```

### Clientes

```http
GET    /api/clientes/clientes/
POST   /api/clientes/clientes/
GET    /api/clientes/clientes/{id}/
PUT    /api/clientes/clientes/{id}/
DELETE /api/clientes/clientes/{id}/
```

## 🛠️ Tecnologías

- **Backend**: Django 5.2, Django REST Framework 3.16
- **Base de datos**: PostgreSQL
- **Autenticación**: Token Authentication
- **Documentación**: drf-spectacular (OpenAPI 3.0)
- **Pagos**: Stripe
- **PDFs**: ReportLab
- **CORS**: django-cors-headers

## 📁 Estructura del Proyecto

```
smartsales365/
├── core/                 # Configuración principal
├── usuarios/            # Gestión de usuarios
├── productos/           # Gestión de productos
├── clientes/            # Gestión de clientes
├── compra/              # Sistema de compras
├── reportes/            # Reportes y estadísticas
├── ia/                  # Predicciones (futuro)
├── logs/                # Archivos de log
├── manage.py
├── requirements.txt
└── README.md
```

## 🔒 Seguridad

- ⚠️ Nunca subas el archivo `.env` a Git
- ⚠️ Cambia `SECRET_KEY` en producción
- ⚠️ Configura `DEBUG=False` en producción
- ⚠️ Define `ALLOWED_HOSTS` correctamente
- ⚠️ Usa HTTPS en producción
- ⚠️ Configura CORS apropiadamente

## 🧪 Testing

```powershell
python manage.py test
```

## 📝 Migraciones

```powershell
# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Ver estado de migraciones
python manage.py showmigrations
```

## 🚀 Deploy

Para producción, considera:

1. Usar Gunicorn o uWSGI
2. Configurar Nginx como reverse proxy
3. Usar PostgreSQL en servidor separado
4. Configurar variables de entorno de producción
5. Habilitar HTTPS con Let's Encrypt
6. Configurar backup de base de datos
7. Monitorear logs con herramientas como Sentry

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

## 📄 Licencia

Este proyecto es de uso educativo.

## ✨ Mejoras Recientes

- ✅ Validación de stock automática en checkout
- ✅ Reducción de stock transaccional
- ✅ Logging estructurado para producción
- ✅ Índices de base de datos optimizados
- ✅ Validadores en modelos
- ✅ Serializers mejorados con campos anidados
- ✅ Mejor manejo de errores
- ✅ Stripe integrado correctamente
- ✅ Comprobantes PDF mejorados

## 📧 Contacto

Para preguntas o soporte, contacta al equipo de desarrollo.
