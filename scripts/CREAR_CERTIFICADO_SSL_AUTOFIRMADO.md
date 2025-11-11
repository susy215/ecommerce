# 🔐 Crear Certificado SSL Autofirmado para HTTPS

## 📋 Requisitos

- Ya estar conectado a EC2
- Nginx instalado
- Proyecto SmartSales365 funcionando

---

## 🔑 Paso 1: Generar Certificado Autofirmado

Ejecuta este script en tu EC2:

```bash
# Crear directorio para certificados
sudo mkdir -p /etc/nginx/ssl
cd /etc/nginx/ssl

# Generar certificado autofirmado (válido por 365 días)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/smartsales365.key \
  -out /etc/nginx/ssl/smartsales365.crt \
  -subj "/C=US/ST=State/L=City/O=SmartSales365/CN=smartsales365.com"

# Verificar permisos
sudo chmod 600 /etc/nginx/ssl/smartsales365.key
sudo chmod 644 /etc/nginx/ssl/smartsales365.crt

# Verificar que se crearon
ls -lh /etc/nginx/ssl/
```

---

## ⚙️ Paso 2: Configurar Nginx para HTTPS

### Opción A: Configuración Completa (HTTP + HTTPS con Redirección)

```bash
sudo nano /etc/nginx/sites-available/smartsales365
```

Pega esta configuración:

```nginx
# Redirigir HTTP a HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name _;
    
    return 301 https://$host$request_uri;
}

# Servidor HTTPS
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name _;

    # Certificados SSL
    ssl_certificate /etc/nginx/ssl/smartsales365.crt;
    ssl_certificate_key /etc/nginx/ssl/smartsales365.key;

    # Configuración SSL segura
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Headers de seguridad
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Archivos estáticos
    location /static/ {
        alias /var/www/smartsales365/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/smartsales365/media/;
        expires 7d;
    }

    # Proxy a Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Tamaño máximo de archivos
    client_max_body_size 50M;
}
```

### Opción B: Solo HTTPS (Sin Redirección)

Si prefieres mantener ambos HTTP y HTTPS activos:

```nginx
# HTTP
server {
    listen 80;
    listen [::]:80;
    server_name _;

    location /static/ {
        alias /var/www/smartsales365/staticfiles/;
    }

    location /media/ {
        alias /var/www/smartsales365/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    client_max_body_size 50M;
}

# HTTPS
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name _;

    ssl_certificate /etc/nginx/ssl/smartsales365.crt;
    ssl_certificate_key /etc/nginx/ssl/smartsales365.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location /static/ {
        alias /var/www/smartsales365/staticfiles/;
    }

    location /media/ {
        alias /var/www/smartsales365/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }

    client_max_body_size 50M;
}
```

---

## ✅ Paso 3: Activar Configuración

```bash
# Crear symlink si no existe
sudo ln -sf /etc/nginx/sites-available/smartsales365 /etc/nginx/sites-enabled/

# Eliminar configuración default si existe
sudo rm -f /etc/nginx/sites-enabled/default

# Verificar configuración
sudo nginx -t

# Si todo está OK, reiniciar
sudo systemctl restart nginx
sudo systemctl status nginx
```

---

## 🔥 Paso 4: Actualizar Security Group de AWS

Ve a AWS Console y asegúrate que tu Security Group permita:

```
Inbound Rules:
- Type: HTTP  | Port: 80   | Source: 0.0.0.0/0
- Type: HTTPS | Port: 443  | Source: 0.0.0.0/0
- Type: SSH   | Port: 22   | Source: Tu IP
```

---

## 🧪 Paso 5: Probar HTTPS

### Desde el navegador:

```
https://18.188.65.153
```

**⚠️ Nota:** Verás una advertencia de seguridad porque es un certificado autofirmado.

- **Chrome**: Click en "Advanced" → "Proceed to ... (unsafe)"
- **Firefox**: Click en "Advanced" → "Accept the Risk and Continue"
- **Edge**: Click en "Advanced" → "Continue to ... (unsafe)"

### Desde terminal (local):

```bash
# Probar HTTP (debería redirigir a HTTPS si configuraste redirección)
curl http://18.188.65.153

# Probar HTTPS (con -k para ignorar certificado autofirmado)
curl -k https://18.188.65.153
```

### Desde EC2:

```bash
# Probar localmente
curl -k https://localhost
curl -k https://127.0.0.1
```

---

## 🔍 Verificar Certificado

```bash
# Ver detalles del certificado
openssl x509 -in /etc/nginx/ssl/smartsales365.crt -text -noout

# Verificar fecha de expiración
openssl x509 -in /etc/nginx/ssl/smartsales365.crt -noout -dates

# Probar conexión SSL
openssl s_client -connect localhost:443 -showcerts
```

---

## 🐛 Troubleshooting

### Error: "SSL certificate problem"

```bash
# Verificar que los archivos existen
ls -lh /etc/nginx/ssl/

# Deberías ver:
# -rw-r--r-- smartsales365.crt
# -rw------- smartsales365.key
```

### Error: "nginx: [emerg] SSL: error"

```bash
# Verificar sintaxis
sudo nginx -t

# Ver logs
sudo tail -f /var/log/nginx/error.log
```

### Puerto 443 no responde

```bash
# Verificar que nginx escucha en 443
sudo netstat -tlnp | grep :443

# O con ss
sudo ss -tlnp | grep :443

# Deberías ver nginx escuchando
```

### Security Group

```bash
# Verificar desde EC2 que puedes conectarte localmente
curl -k https://localhost

# Si funciona localmente pero no desde afuera, es el Security Group
```

---

## 📋 Comandos Útiles

```bash
# Reiniciar Nginx
sudo systemctl restart nginx

# Ver estado
sudo systemctl status nginx

# Ver logs en tiempo real
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Renovar certificado (crear uno nuevo por otro año)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/smartsales365.key \
  -out /etc/nginx/ssl/smartsales365.crt \
  -subj "/C=US/ST=State/L=City/O=SmartSales365/CN=smartsales365.com"

sudo systemctl restart nginx
```

---

## 🎯 Actualizar Django Settings

Asegúrate que en tu `settings_production.py` tengas:

```python
# Security settings
SECURE_SSL_REDIRECT = True  # Redirigir HTTP a HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

Luego reinicia Gunicorn:

```bash
sudo systemctl restart smartsales365
```

---

## 🚀 Próximos Pasos (Opcional)

### Migrar a Let's Encrypt (Certificado REAL)

Cuando tengas un dominio apuntando a tu EC2:

```bash
# Instalar Certbot
sudo apt update
sudo apt install -y certbot python3-certbot-nginx

# Obtener certificado (reemplaza tu-dominio.com)
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com

# Certbot configurará automáticamente Nginx y renovará el certificado cada 90 días
```

---

## ✅ Checklist Final

- [ ] Certificado creado en `/etc/nginx/ssl/`
- [ ] Nginx configurado para HTTPS
- [ ] Security Group permite puerto 443
- [ ] Sitio accesible por HTTPS (con advertencia de certificado)
- [ ] Django settings actualizados
- [ ] Gunicorn reiniciado

---

**¡Listo! Ahora tu aplicación está corriendo con HTTPS usando un certificado autofirmado.** 🔐

Para producción real, usa Let's Encrypt cuando tengas un dominio.

