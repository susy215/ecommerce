#!/bin/bash
# Script completo paso a paso para EC2
# Ejecutar DESPUÉS de conectarte a EC2

echo "🚀 Iniciando configuración de SmartSales365 en EC2..."
echo ""

# ===== PASO 1: Actualizar Sistema =====
echo "═══════════════════════════════════════════════════════"
echo "PASO 1/10: Actualizando sistema..."
echo "═══════════════════════════════════════════════════════"
sudo apt update
sudo apt upgrade -y
echo "✅ Sistema actualizado"
echo ""

# ===== PASO 2: Instalar Dependencias =====
echo "═══════════════════════════════════════════════════════"
echo "PASO 2/10: Instalando dependencias..."
echo "═══════════════════════════════════════════════════════"
sudo apt install -y python3 python3-pip python3-venv postgresql-client git nginx certbot python3-certbot-nginx
echo "✅ Dependencias instaladas"
echo ""

# ===== PASO 3: Crear Directorios =====
echo "═══════════════════════════════════════════════════════"
echo "PASO 3/10: Creando directorios..."
echo "═══════════════════════════════════════════════════════"
sudo mkdir -p /var/www/smartsales365/static
sudo mkdir -p /var/www/smartsales365/media
sudo mkdir -p /var/log/smartsales365
sudo chown -R ubuntu:ubuntu /var/www/smartsales365
sudo chown -R ubuntu:ubuntu /var/log/smartsales365
echo "✅ Directorios creados"
echo ""

# ===== PASO 4: Clonar Repositorio =====
echo "═══════════════════════════════════════════════════════"
echo "PASO 4/10: Clonando repositorio..."
echo "═══════════════════════════════════════════════════════"
cd /var/www
if [ -d "smartsales365" ]; then
    echo "⚠️ El directorio ya existe. Actualizando..."
    cd smartsales365
    git pull
else
    git clone https://github.com/susy215/ecommerce.git smartsales365
    cd smartsales365
fi
echo "✅ Repositorio clonado/actualizado"
echo ""

# ===== PASO 5: Crear Entorno Virtual =====
echo "═══════════════════════════════════════════════════════"
echo "PASO 5/10: Creando entorno virtual..."
echo "═══════════════════════════════════════════════════════"
python3 -m venv venv
source venv/bin/activate
echo "✅ Entorno virtual creado"
echo ""

# ===== PASO 6: Instalar Dependencias Python =====
echo "═══════════════════════════════════════════════════════"
echo "PASO 6/10: Instalando dependencias Python..."
echo "═══════════════════════════════════════════════════════"
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
echo "✅ Dependencias Python instaladas"
echo ""

# ===== RESUMEN =====
echo ""
echo "═══════════════════════════════════════════════════════"
echo "✅ CONFIGURACIÓN INICIAL COMPLETADA"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "📋 Próximos pasos manuales:"
echo ""
echo "1. Crear archivo .env:"
echo "   cd /var/www/smartsales365"
echo "   nano .env"
echo "   (Copia el contenido de docs/ENV_PRODUCTION_TEMPLATE.txt)"
echo ""
echo "2. Configurar variables de entorno en .env:"
echo "   - DB_HOST (endpoint de RDS)"
echo "   - DB_PASSWORD (password de RDS)"
echo "   - DJANGO_SECRET_KEY (genera una clave segura)"
echo "   - DJANGO_ALLOWED_HOSTS (tu dominio)"
echo ""
echo "3. Ejecutar migraciones:"
echo "   source venv/bin/activate"
echo "   export DJANGO_SETTINGS_MODULE=core.settings_production"
echo "   python manage.py migrate"
echo ""
echo "4. Recolectar archivos estáticos:"
echo "   python manage.py collectstatic --noinput"
echo ""
echo "═══════════════════════════════════════════════════════"








