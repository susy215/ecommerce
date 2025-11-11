# 🚀 Despliegue en AWS EC2 - Guía Completa y Simple

## 📋 Índice

1. [Preparación del Proyecto](#1-preparación-del-proyecto)
2. [Crear Instancia EC2](#2-crear-instancia-ec2)
3. [Configurar RDS PostgreSQL](#3-configurar-rds-postgresql)
4. [Conectar a EC2](#4-conectar-a-ec2)
5. [Instalar Dependencias](#5-instalar-dependencias)
6. [Configurar Base de Datos](#6-configurar-base-de-datos)
7. [Configurar Django](#7-configurar-django)
8. [Configurar Nginx](#8-configurar-nginx)
9. [Obtener Certificado SSL (Let's Encrypt)](#9-obtener-certificado-ssl-lets-encrypt)
10. [Configurar Gunicorn](#10-configurar-gunicorn)
11. [Configurar Servicio Systemd](#11-configurar-servicio-systemd)
12. [Variables de Entorno](#12-variables-de-entorno)
13. [Deploy Final](#13-deploy-final)

---

## 🎯 Requisitos Previos

- Cuenta de AWS activa
- Dominio apuntando a tu IP de EC2 (para Let's Encrypt)
- Conocimientos básicos de terminal

---

## 1. Preparación del Proyecto

### 1.1 Crear archivo de producción

Crea `core/settings_production.py`:

```python
# core/settings_production.py
from .settings import *
import os

# Seguridad
DEBUG = False
ALLOWED_HOSTS = ['tu-dominio.com', 'www.tu-dominio.com', 'tu-ip-publica']

# Base de datos RDS
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'smartsales365'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}

# Static files
STATIC_ROOT = '/var/www/smartsales365/static'
MEDIA_ROOT = '/var/www/smartsales365/media'

# HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/smartsales365/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### 1.2 Crear requirements_production.txt

```bash
# Copiar requirements.txt y agregar:
gunicorn==21.2.0
psycopg2-binary==2.9.9
```

---

## 2. Crear Instancia EC2

### Paso 1: Seleccionar AMI

1. Ve a **EC2** → **Launch Instance**
2. Selecciona **Amazon Linux 2023** (o Ubuntu 22.04 LTS)
3. Elige **t3.micro** (Free Tier) o **t3.small** (más rendimiento)

### Paso 2: Configurar Security Group

**Inbound Rules:**
- SSH (22) - Tu IP solamente
- HTTP (80) - 0.0.0.0/0
- HTTPS (443) - 0.0.0.0/0

**Outbound Rules:**
- Todo permitido (default)

### Paso 3: Crear Key Pair

1. Crea un nuevo key pair
2. Descarga el archivo `.pem`
3. Guárdalo en un lugar seguro

### Paso 4: Launch Instance

1. Revisa configuración
2. Click en **Launch Instance**
3. Espera a que esté en estado **Running**

---

## 3. Configurar RDS PostgreSQL

### Paso 1: Crear Base de Datos RDS

1. Ve a **RDS** → **Create database**
2. Selecciona **PostgreSQL**
3. Versión: **PostgreSQL 15.x** (o la más reciente)
4. Template: **Free tier** (si aplica) o **Production**
5. DB instance identifier: `smartsales365-db`
6. Master username: `smartsales365_admin`
7. Master password: **GUARDA ESTA CONTRASEÑA**
8. DB instance class: **db.t3.micro** (Free tier) o **db.t3.small**
9. Storage: 20 GB (suficiente para empezar)

### Paso 2: Configurar Security Group de RDS

1. Crea un nuevo Security Group: `rds-smartsales365`
2. **Inbound Rules:**
   - PostgreSQL (5432) - Solo desde el Security Group de tu EC2
3. **Asocia este Security Group a tu RDS**

### Paso 3: Obtener Endpoint

1. Espera a que RDS esté disponible
2. Copia el **Endpoint** (ej: `smartsales365-db.xxxxx.us-east-1.rds.amazonaws.com`)

---

## 4. Conectar a EC2

### Windows (PowerShell)

```powershell
# Cambiar permisos (solo primera vez)
icacls ruta\a\tu-archivo.pem /inheritance:r
icacls ruta\a\tu-archivo.pem /grant:r "%USERNAME%:R"

# Conectar
ssh -i ruta\a\tu-archivo.pem ec2-user@tu-ip-publica
```

### Mac/Linux

```bash
# Cambiar permisos
chmod 400 tu-archivo.pem

# Conectar
ssh -i tu-archivo.pem ec2-user@tu-ip-publica
```

**Nota:** Si usas Ubuntu, el usuario es `ubuntu` en lugar de `ec2-user`

---

## 5. Instalar Dependencias

### Actualizar sistema

```bash
# Amazon Linux 2023
sudo dnf update -y

# Ubuntu
sudo apt update && sudo apt upgrade -y
```

### Instalar Python y herramientas

```bash
# Amazon Linux 2023
sudo dnf install -y python3 python3-pip python3-devel postgresql15 git nginx

# Ubuntu
sudo apt install -y python3 python3-pip python3-venv postgresql-client git nginx
```

### Instalar Certbot (para Let's Encrypt)

```bash
# Amazon Linux 2023
sudo dnf install -y certbot python3-certbot-nginx

# Ubuntu
sudo apt install -y certbot python3-certbot-nginx
```

---

## 6. Configurar Base de Datos

### Conectar a RDS desde EC2

```bash
# Probar conexión (usa el endpoint de RDS)
psql -h smartsales365-db.xxxxx.us-east-1.rds.amazonaws.com -U smartsales365_admin -d postgres
```

Si pide contraseña, ingresa la que configuraste.

---

## 7. Configurar Django

### Crear directorio del proyecto

```bash
sudo mkdir -p /var/www/smartsales365
sudo chown ec2-user:ec2-user /var/www/smartsales365
cd /var/www/smartsales365
```

### Subir tu código

**Opción A: Git (Recomendado)**

```bash
# Clonar tu repositorio
git clone https://github.com/tu-usuario/smartsales365.git .
```

**Opción B: SCP (desde tu máquina local)**

```bash
# Desde tu máquina local (PowerShell)
scp -i tu-archivo.pem -r C:\ruta\a\tu\proyecto ec2-user@tu-ip:/var/www/smartsales365
```

### Crear entorno virtual

```bash
cd /var/www/smartsales365
python3 -m venv venv
source venv/bin/activate
```

### Instalar dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

### Crear directorios necesarios

```bash
sudo mkdir -p /var/www/smartsales365/static
sudo mkdir -p /var/www/smartsales365/media
sudo mkdir -p /var/log/smartsales365
sudo chown -R ec2-user:ec2-user /var/www/smartsales365
sudo chown -R ec2-user:ec2-user /var/log/smartsales365
```

---

## 8. Configurar Nginx

### Crear configuración de Nginx

```bash
sudo nano /etc/nginx/conf.d/smartsales365.conf
```

**Contenido:**

```nginx
server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;

    # Redirigir a HTTPS (se configurará después con Let's Encrypt)
    # Por ahora, comentar estas líneas:
    # return 301 https://$server_name$request_uri;

    # Por ahora, servir HTTP temporalmente
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static/ {
        alias /var/www/smartsales365/static/;
    }

    # Media files
    location /media/ {
        alias /var/www/smartsales365/media/;
    }
}
```

### Probar configuración

```bash
sudo nginx -t
```

### Iniciar Nginx

```bash
sudo systemctl start nginx
sudo systemctl enable nginx
```

---

## 9. Obtener Certificado SSL (Let's Encrypt)

### Paso 1: Verificar que tu dominio apunta a EC2

1. Configura DNS de tu dominio:
   - **A Record**: `tu-dominio.com` → IP pública de EC2
   - **A Record**: `www.tu-dominio.com` → IP pública de EC2

2. Espera a que DNS se propague (puede tardar hasta 24 horas, pero generalmente es rápido)

3. Verifica que funciona:
   ```bash
   ping tu-dominio.com
   ```

### Paso 2: Obtener certificado

```bash
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com
```

**Sigue las instrucciones:**
- Ingresa tu email
- Acepta términos
- Certbot modificará automáticamente Nginx

### Paso 3: Renovación automática

Let's Encrypt expira cada 90 días. Certbot configura renovación automática:

```bash
# Verificar que está configurado
sudo certbot renew --dry-run
```

---

## 10. Configurar Gunicorn

### Crear archivo de configuración

```bash
nano /var/www/smartsales365/gunicorn_config.py
```

**Contenido:**

```python
# gunicorn_config.py
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
accesslog = "/var/log/smartsales365/gunicorn_access.log"
errorlog = "/var/log/smartsales365/gunicorn_error.log"
loglevel = "info"
```

---

## 11. Configurar Servicio Systemd

### Crear servicio

```bash
sudo nano /etc/systemd/system/smartsales365.service
```

**Contenido:**

```ini
[Unit]
Description=SmartSales365 Gunicorn daemon
After=network.target

[Service]
User=ec2-user
Group=ec2-user
WorkingDirectory=/var/www/smartsales365
Environment="PATH=/var/www/smartsales365/venv/bin"
ExecStart=/var/www/smartsales365/venv/bin/gunicorn \
    --config /var/www/smartsales365/gunicorn_config.py \
    core.wsgi:application

Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### Activar servicio

```bash
sudo systemctl daemon-reload
sudo systemctl start smartsales365
sudo systemctl enable smartsales365
```

### Verificar estado

```bash
sudo systemctl status smartsales365
```

---

## 12. Variables de Entorno

### Crear archivo .env

```bash
nano /var/www/smartsales365/.env
```

**Contenido (AJUSTA CON TUS VALORES):**

```env
# Django
DJANGO_SECRET_KEY=tu-secret-key-muy-segura-aqui
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com

# Base de datos RDS
DB_NAME=smartsales365
DB_USER=smartsales365_admin
DB_PASSWORD=tu-password-de-rds
DB_HOST=smartsales365-db.xxxxx.us-east-1.rds.amazonaws.com
DB_PORT=5432

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_CURRENCY=usd

# Frontend
FRONTEND_URL=https://tu-frontend.com

# VAPID (Push Notifications)
VAPID_PRIVATE_KEY=tu-vapid-private-key
VAPID_PUBLIC_KEY=tu-vapid-public-key
VAPID_ADMIN_EMAIL=admin@tu-dominio.com

# CORS (si tienes frontend separado)
CORS_ALLOWED_ORIGINS=https://tu-frontend.com,https://www.tu-frontend.com
CSRF_TRUSTED_ORIGINS=https://tu-dominio.com,https://www.tu-dominio.com
```

### Proteger archivo .env

```bash
chmod 600 /var/www/smartsales365/.env
```

---

## 13. Deploy Final

### Configurar Django

```bash
cd /var/www/smartsales365
source venv/bin/activate

# Configurar settings
export DJANGO_SETTINGS_MODULE=core.settings_production

# Migraciones
python manage.py migrate

# Crear superusuario (opcional)
python manage.py createsuperuser

# Recolectar archivos estáticos
python manage.py collectstatic --noinput

# Generar VAPID keys (si no las tienes)
python manage.py generate_vapid_keys
```

### Reiniciar servicios

```bash
sudo systemctl restart smartsales365
sudo systemctl restart nginx
```

### Verificar logs

```bash
# Logs de Django
tail -f /var/log/smartsales365/django.log

# Logs de Gunicorn
tail -f /var/log/smartsales365/gunicorn_error.log

# Logs de Nginx
sudo tail -f /var/log/nginx/error.log
```

---

## ✅ Verificación Final

### 1. Verificar que el sitio funciona

Visita: `https://tu-dominio.com`

### 2. Verificar HTTPS

El navegador debe mostrar un candado verde ✅

### 3. Verificar API

```bash
curl https://tu-dominio.com/api/ia/health/
```

---

## 🔧 Comandos Útiles

### Reiniciar aplicación

```bash
sudo systemctl restart smartsales365
```

### Ver estado

```bash
sudo systemctl status smartsales365
```

### Ver logs en tiempo real

```bash
sudo journalctl -u smartsales365 -f
```

### Actualizar código

```bash
cd /var/www/smartsales365
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart smartsales365
```

---

## 🐛 Solución de Problemas

### Error: No se puede conectar a RDS

1. Verifica Security Group de RDS permite conexiones desde EC2
2. Verifica que el endpoint de RDS sea correcto
3. Verifica credenciales en `.env`

### Error: 502 Bad Gateway

1. Verifica que Gunicorn esté corriendo: `sudo systemctl status smartsales365`
2. Verifica logs: `sudo journalctl -u smartsales365 -n 50`
3. Verifica que el puerto 8000 esté escuchando: `netstat -tlnp | grep 8000`

### Error: SSL Certificate

1. Verifica que tu dominio apunta a la IP correcta
2. Renueva certificado: `sudo certbot renew`

---

## 📝 Checklist Final

- [ ] EC2 creada y corriendo
- [ ] RDS PostgreSQL creado y accesible
- [ ] Código subido a EC2
- [ ] Variables de entorno configuradas
- [ ] Migraciones ejecutadas
- [ ] Nginx configurado
- [ ] Certificado SSL obtenido
- [ ] Gunicorn corriendo como servicio
- [ ] Sitio accesible por HTTPS
- [ ] Push notifications funcionando (requiere HTTPS)

---

**¡Listo! Tu aplicación debería estar funcionando en producción.** 🎉

