# 🎯 Deploy AWS EC2 - Paso a Paso Visual

## 📊 Arquitectura Simple

```
┌─────────────────┐
│   Internet      │
│   (Usuarios)    │
└────────┬────────┘
         │ HTTPS (443)
         │ HTTP (80)
         ▼
┌─────────────────┐
│   Nginx         │  ← Reverse Proxy + SSL
│   (Puerto 80/443)│
└────────┬────────┘
         │
         │ Proxy
         ▼
┌─────────────────┐
│   Gunicorn      │  ← Servidor Django
│   (Puerto 8000) │
└────────┬────────┘
         │
         │ Consultas SQL
         ▼
┌─────────────────┐
│   RDS PostgreSQL│  ← Base de Datos
│   (Puerto 5432) │
└─────────────────┘
```

---

## 🚀 Proceso en 10 Pasos

### PASO 1: Crear EC2 (5 min)

1. Ve a **EC2 Console** → **Launch Instance**
2. Selecciona **Amazon Linux 2023**
3. Elige **t3.micro** (Free Tier)
4. Configura Security Group:
   - SSH (22) - Solo tu IP
   - HTTP (80) - 0.0.0.0/0
   - HTTPS (443) - 0.0.0.0/0
5. Crea Key Pair y descarga `.pem`
6. **Launch Instance**

✅ **Resultado:** Tienes una IP pública (ej: 54.123.45.67)

---

### PASO 2: Crear RDS (10 min)

1. Ve a **RDS Console** → **Create database**
2. Selecciona **PostgreSQL 15**
3. Template: **Free tier**
4. Configura:
   - DB instance: `smartsales365-db`
   - Username: `smartsales365_admin`
   - Password: **GUÁRDALA BIEN**
   - Instance class: `db.t3.micro`
5. Storage: 20 GB
6. Security Group: Crea uno nuevo que permita PostgreSQL (5432) desde el Security Group de tu EC2
7. **Create database**

✅ **Resultado:** Tienes un endpoint (ej: `smartsales365-db.xxxxx.us-east-1.rds.amazonaws.com`)

---

### PASO 3: Configurar DNS (5 min)

En tu proveedor de dominio (GoDaddy, Namecheap, etc.):

1. Crea **A Record**:
   - Nombre: `@` o `tu-dominio.com`
   - Valor: IP pública de EC2
2. Crea otro **A Record**:
   - Nombre: `www`
   - Valor: IP pública de EC2

✅ **Resultado:** Tu dominio apunta a EC2 (puede tardar unos minutos)

---

### PASO 4: Conectar a EC2 (2 min)

**Windows (PowerShell):**
```powershell
ssh -i ruta\a\tu-archivo.pem ec2-user@tu-ip-publica
```

**Mac/Linux:**
```bash
chmod 400 tu-archivo.pem
ssh -i tu-archivo.pem ec2-user@tu-ip-publica
```

✅ **Resultado:** Estás dentro de tu servidor EC2

---

### PASO 5: Instalar Dependencias (5 min)

Dentro de EC2, ejecuta:

```bash
# Ejecutar script de setup (lo subirás después)
bash scripts/setup_ec2.sh

# O manualmente:
sudo dnf update -y
sudo dnf install -y python3 python3-pip python3-devel postgresql15 git nginx certbot python3-certbot-nginx
```

✅ **Resultado:** Todas las herramientas instaladas

---

### PASO 6: Subir Código (5 min)

**Opción A: Git (Recomendado)**
```bash
cd /var/www
sudo mkdir smartsales365
sudo chown ec2-user:ec2-user smartsales365
cd smartsales365
git clone https://github.com/tu-usuario/smartsales365.git .
```

**Opción B: SCP (desde tu máquina local)**
```powershell
# Desde PowerShell en tu máquina
scp -i archivo.pem -r C:\ruta\a\tu\proyecto ec2-user@tu-ip:/var/www/smartsales365
```

✅ **Resultado:** Tu código está en `/var/www/smartsales365`

---

### PASO 7: Configurar Python y Django (10 min)

```bash
cd /var/www/smartsales365

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn psycopg2-binary

# Crear directorios
sudo mkdir -p static media /var/log/smartsales365
sudo chown -R ec2-user:ec2-user /var/www/smartsales365 /var/log/smartsales365

# Crear archivo .env
nano .env
# (Pega el contenido de docs/ENV_PRODUCTION_TEMPLATE.txt y completa)
```

**En `.env` debes poner:**
- `DB_HOST` = endpoint de RDS
- `DB_PASSWORD` = password de RDS
- `DJANGO_SECRET_KEY` = genera una clave segura
- `DJANGO_ALLOWED_HOSTS` = tu-dominio.com,www.tu-dominio.com
- Todas las demás variables

```bash
# Migraciones
export DJANGO_SETTINGS_MODULE=core.settings_production
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser  # Opcional
```

✅ **Resultado:** Django configurado y base de datos lista

---

### PASO 8: Configurar Nginx (5 min)

```bash
sudo nano /etc/nginx/conf.d/smartsales365.conf
```

**Pega esto (ajusta `tu-dominio.com`):**

```nginx
server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/smartsales365/static/;
    }

    location /media/ {
        alias /var/www/smartsales365/media/;
    }
}
```

```bash
sudo nginx -t  # Verificar que está bien
sudo systemctl start nginx
sudo systemctl enable nginx
```

✅ **Resultado:** Nginx corriendo (HTTP funcionando)

---

### PASO 9: Obtener Certificado SSL (5 min)

```bash
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com
```

**Sigue las instrucciones:**
- Email: tu email
- Acepta términos
- Certbot modificará Nginx automáticamente

✅ **Resultado:** HTTPS funcionando con certificado válido

---

### PASO 10: Configurar Gunicorn como Servicio (5 min)

**1. Crear configuración de Gunicorn:**

```bash
nano /var/www/smartsales365/gunicorn_config.py
```

**Contenido:**
```python
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
timeout = 120
accesslog = "/var/log/smartsales365/gunicorn_access.log"
errorlog = "/var/log/smartsales365/gunicorn_error.log"
loglevel = "info"
```

**2. Crear servicio systemd:**

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
Environment="DJANGO_SETTINGS_MODULE=core.settings_production"
ExecStart=/var/www/smartsales365/venv/bin/gunicorn \
    --config /var/www/smartsales365/gunicorn_config.py \
    core.wsgi:application

Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

**3. Activar servicio:**

```bash
sudo systemctl daemon-reload
sudo systemctl start smartsales365
sudo systemctl enable smartsales365
sudo systemctl status smartsales365  # Verificar que está corriendo
```

✅ **Resultado:** Tu aplicación está corriendo y se reinicia automáticamente

---

## 🎉 ¡LISTO!

Visita: `https://tu-dominio.com`

Deberías ver tu aplicación funcionando con HTTPS ✅

---

## 🔄 Actualizar Código en el Futuro

```bash
cd /var/www/smartsales365
source venv/bin/activate
git pull  # Si usas Git
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart smartsales365
```

O simplemente ejecuta:
```bash
bash scripts/deploy.sh
```

---

## 🆘 Si Algo Sale Mal

### Ver logs de Django:
```bash
tail -f /var/log/smartsales365/django.log
```

### Ver logs de Gunicorn:
```bash
tail -f /var/log/smartsales365/gunicorn_error.log
```

### Ver estado del servicio:
```bash
sudo systemctl status smartsales365
```

### Reiniciar todo:
```bash
sudo systemctl restart smartsales365
sudo systemctl restart nginx
```

---

## 📝 Resumen de Archivos Clave

| Archivo | Ubicación | Propósito |
|---------|-----------|-----------|
| `.env` | `/var/www/smartsales365/` | Variables de entorno |
| `gunicorn_config.py` | `/var/www/smartsales365/` | Configuración Gunicorn |
| `smartsales365.service` | `/etc/systemd/system/` | Servicio systemd |
| `smartsales365.conf` | `/etc/nginx/conf.d/` | Configuración Nginx |

---

**Tiempo total: ~1 hora** ⏱️

**¡Mucha suerte con tu deploy!** 🚀

