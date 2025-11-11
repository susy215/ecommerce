#!/bin/bash
# Script para configurar SSL autofirmado en SmartSales365

set -e  # Salir si hay errores

echo "🔐 Configurando SSL autofirmado para SmartSales365..."
echo ""

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Paso 1: Crear directorio para certificados
echo "📁 Creando directorio para certificados..."
sudo mkdir -p /etc/nginx/ssl

# Paso 2: Generar certificado autofirmado
echo "🔑 Generando certificado autofirmado (válido por 365 días)..."
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/smartsales365.key \
  -out /etc/nginx/ssl/smartsales365.crt \
  -subj "/C=US/ST=Ohio/L=Columbus/O=SmartSales365/CN=smartsales365.com" \
  2>/dev/null

# Paso 3: Configurar permisos
echo "🔒 Configurando permisos..."
sudo chmod 600 /etc/nginx/ssl/smartsales365.key
sudo chmod 644 /etc/nginx/ssl/smartsales365.crt

# Verificar que se crearon
if [ -f /etc/nginx/ssl/smartsales365.crt ] && [ -f /etc/nginx/ssl/smartsales365.key ]; then
    echo -e "${GREEN}✅ Certificados creados exitosamente${NC}"
    ls -lh /etc/nginx/ssl/
else
    echo -e "${RED}❌ Error: No se pudieron crear los certificados${NC}"
    exit 1
fi

echo ""

# Paso 4: Crear configuración de Nginx
echo "⚙️  Creando configuración de Nginx..."

sudo tee /etc/nginx/sites-available/smartsales365 > /dev/null <<'EOF'
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
EOF

# Paso 5: Activar configuración
echo "🔗 Activando configuración..."
sudo ln -sf /etc/nginx/sites-available/smartsales365 /etc/nginx/sites-enabled/

# Eliminar default si existe
if [ -f /etc/nginx/sites-enabled/default ]; then
    echo "🗑️  Eliminando configuración default..."
    sudo rm -f /etc/nginx/sites-enabled/default
fi

# Paso 6: Verificar configuración
echo "✅ Verificando configuración de Nginx..."
if sudo nginx -t; then
    echo -e "${GREEN}✅ Configuración de Nginx válida${NC}"
else
    echo -e "${RED}❌ Error en la configuración de Nginx${NC}"
    exit 1
fi

echo ""

# Paso 7: Reiniciar Nginx
echo "🔄 Reiniciando Nginx..."
sudo systemctl restart nginx

if sudo systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✅ Nginx reiniciado exitosamente${NC}"
else
    echo -e "${RED}❌ Error: Nginx no está corriendo${NC}"
    sudo systemctl status nginx
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ SSL configurado exitosamente!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Detalles del certificado:"
openssl x509 -in /etc/nginx/ssl/smartsales365.crt -noout -dates
echo ""
echo "🌐 Accede a tu sitio:"
echo "   https://18.188.65.153"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANTE:${NC}"
echo "   1. Asegúrate que el Security Group permita puerto 443"
echo "   2. El navegador mostrará advertencia (certificado autofirmado)"
echo "   3. Click en 'Advanced' → 'Proceed' para acceder"
echo ""
echo "🧪 Probar desde terminal:"
echo "   curl -k https://18.188.65.153"
echo ""
echo "📝 Ver logs de Nginx:"
echo "   sudo tail -f /var/log/nginx/error.log"
echo ""
EOF

chmod +x scripts/setup_ssl.sh

