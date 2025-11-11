# 🚀 Guía Rápida: Conectar a EC2 y Configurar HTTPS

## 📍 Tu Información
- **IP EC2**: `18.188.65.153`
- **Usuario**: `ubuntu`
- **Archivo PEM**: `C:\Users\httpReen\Desktop\CALIDAD\smartsales365\ventas_reportes.pem`

---

## 🎯 OPCIÓN 1: Automático (Recomendado)

### Paso 1: Arreglar Permisos y Conectar

Abre PowerShell **como Administrador** y ejecuta:

```powershell
cd C:\Users\httpReen\Desktop\CALIDAD\smartsales365
.\scripts\conectar_ec2.ps1
```

### Paso 2: Una Vez Conectado a EC2

```bash
# Ir al directorio del proyecto
cd /var/www/smartsales365

# Ejecutar script de SSL (si ya tienes el proyecto en EC2)
bash scripts/setup_ssl.sh
```

---

## 🎯 OPCIÓN 2: Manual

### Paso 1: Arreglar Permisos del PEM

En PowerShell:

```powershell
# Eliminar herencia
icacls "C:\Users\httpReen\Desktop\CALIDAD\smartsales365\ventas_reportes.pem" /inheritance:r

# Dar permisos solo a tu usuario
icacls "C:\Users\httpReen\Desktop\CALIDAD\smartsales365\ventas_reportes.pem" /grant:r "$($env:USERNAME):R"
```

### Paso 2: Conectar a EC2

```powershell
ssh -i "C:\Users\httpReen\Desktop\CALIDAD\smartsales365\ventas_reportes.pem" ubuntu@18.188.65.153
```

### Paso 3: Generar Certificado SSL (En EC2)

```bash
# Crear directorio para certificados
sudo mkdir -p /etc/nginx/ssl

# Generar certificado autofirmado (válido 1 año)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/smartsales365.key \
  -out /etc/nginx/ssl/smartsales365.crt \
  -subj "/C=US/ST=Ohio/L=Columbus/O=SmartSales365/CN=smartsales365.com"

# Configurar permisos
sudo chmod 600 /etc/nginx/ssl/smartsales365.key
sudo chmod 644 /etc/nginx/ssl/smartsales365.crt

# Verificar
ls -lh /etc/nginx/ssl/
```

### Paso 4: Configurar Nginx (En EC2)

```bash
# Crear/editar configuración
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

    # Configuración SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Headers de seguridad
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;

    # Archivos estáticos
    location /static/ {
        alias /var/www/smartsales365/staticfiles/;
        expires 30d;
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
    }

    client_max_body_size 50M;
}
```

Guarda con `Ctrl+O`, Enter, `Ctrl+X`

### Paso 5: Activar y Reiniciar (En EC2)

```bash
# Activar sitio
sudo ln -sf /etc/nginx/sites-available/smartsales365 /etc/nginx/sites-enabled/

# Eliminar default
sudo rm -f /etc/nginx/sites-enabled/default

# Verificar configuración
sudo nginx -t

# Reiniciar Nginx
sudo systemctl restart nginx

# Verificar estado
sudo systemctl status nginx
```

---

## 🔥 Paso Final: Configurar Security Group en AWS

1. Ve a **AWS Console** → **EC2** → **Security Groups**
2. Selecciona el Security Group de tu instancia
3. **Inbound Rules** → **Edit inbound rules**
4. Asegúrate de tener estas reglas:

```
Type    | Protocol | Port | Source
--------|----------|------|----------
SSH     | TCP      | 22   | Tu IP (o 0.0.0.0/0)
HTTP    | TCP      | 80   | 0.0.0.0/0
HTTPS   | TCP      | 443  | 0.0.0.0/0
```

5. **Save rules**

---

## 🧪 Probar HTTPS

### Desde el navegador:

```
https://18.188.65.153
```

**⚠️ Advertencia**: Verás un aviso de seguridad (certificado autofirmado).

- **Chrome/Edge**: Click en "Advanced" → "Proceed to 18.188.65.153 (unsafe)"
- **Firefox**: "Advanced" → "Accept the Risk and Continue"

### Desde terminal (local):

```powershell
# Probar HTTPS (ignora certificado autofirmado)
curl -k https://18.188.65.153
```

### Desde EC2:

```bash
# Probar localmente
curl -k https://localhost
```

---

## 🐛 Solución de Problemas

### No puedo conectarme por SSH

```powershell
# Verificar permisos del PEM
icacls "C:\Users\httpReen\Desktop\CALIDAD\smartsales365\ventas_reportes.pem"

# Deberías ver solo tu usuario con permisos (R)
```

### Puerto 443 no responde

```bash
# En EC2, verificar que Nginx escucha en 443
sudo ss -tlnp | grep :443

# Verificar Security Group en AWS Console
```

### Error en Nginx

```bash
# Ver logs
sudo tail -f /var/log/nginx/error.log

# Verificar configuración
sudo nginx -t
```

### Certificado no válido

```bash
# Verificar que los archivos existen
ls -lh /etc/nginx/ssl/

# Ver detalles del certificado
openssl x509 -in /etc/nginx/ssl/smartsales365.crt -text -noout
```

---

## 📋 Comandos Útiles

```bash
# Reiniciar Nginx
sudo systemctl restart nginx

# Ver estado de Nginx
sudo systemctl status nginx

# Ver logs en tiempo real
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Verificar fecha de expiración del certificado
openssl x509 -in /etc/nginx/ssl/smartsales365.crt -noout -dates

# Renovar certificado (generar uno nuevo)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/smartsales365.key \
  -out /etc/nginx/ssl/smartsales365.crt \
  -subj "/C=US/ST=Ohio/L=Columbus/O=SmartSales365/CN=smartsales365.com"
sudo systemctl restart nginx
```

---

## 🔄 Actualizar Django (Opcional)

Para forzar HTTPS en Django, edita `settings_production.py`:

```python
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

Luego reinicia Gunicorn:

```bash
sudo systemctl restart smartsales365
```

---

## 🎯 Próximos Pasos (Producción Real)

Cuando tengas un dominio:

```bash
# Instalar Certbot
sudo apt update
sudo apt install -y certbot python3-certbot-nginx

# Obtener certificado REAL de Let's Encrypt
sudo certbot --nginx -d tudominio.com -d www.tudominio.com
```

---

## ✅ Checklist

- [ ] Conectado a EC2 exitosamente
- [ ] Certificado SSL creado en `/etc/nginx/ssl/`
- [ ] Nginx configurado para HTTPS
- [ ] Security Group permite puerto 443
- [ ] Sitio accesible por `https://18.188.65.153`
- [ ] (Opcional) Django configurado para forzar HTTPS

---

**¡Listo! Tu aplicación ahora corre con HTTPS.** 🔐

Para dudas o problemas, revisa `scripts/CREAR_CERTIFICADO_SSL_AUTOFIRMADO.md`

