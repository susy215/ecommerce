#!/bin/bash
# Script completo de setup para EC2
# Ejecutar DESPUÉS de conectarte a EC2

set -e  # Salir si hay error

echo "🚀 Iniciando setup completo de SmartSales365 en EC2..."
echo ""

# Detectar sistema operativo
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "❌ No se pudo detectar el sistema operativo"
    exit 1
fi

echo "📦 Sistema detectado: $OS"
echo ""

# ===== PASO 1: Actualizar Sistema =====
echo "1️⃣ Actualizando sistema..."
if [ "$OS" == "amzn" ] || [ "$OS" == "amazon" ]; then
    sudo dnf update -y
elif [ "$OS" == "ubuntu" ]; then
    sudo apt update -y
    sudo apt upgrade -y
else
    echo "❌ Sistema operativo no soportado"
    exit 1
fi
echo "✅ Sistema actualizado"
echo ""

# ===== PASO 2: Instalar Dependencias =====
echo "2️⃣ Instalando dependencias..."
if [ "$OS" == "amzn" ] || [ "$OS" == "amazon" ]; then
    sudo dnf install -y python3 python3-pip python3-devel postgresql15 git nginx certbot python3-certbot-nginx
elif [ "$OS" == "ubuntu" ]; then
    sudo apt install -y python3 python3-pip python3-venv postgresql-client git nginx certbot python3-certbot-nginx
fi
echo "✅ Dependencias instaladas"
echo ""

# ===== PASO 3: Crear Directorios =====
echo "3️⃣ Creando directorios..."
sudo mkdir -p /var/www/smartsales365/static
sudo mkdir -p /var/www/smartsales365/media
sudo mkdir -p /var/log/smartsales365
sudo chown -R $USER:$USER /var/www/smartsales365
sudo chown -R $USER:$USER /var/log/smartsales365
echo "✅ Directorios creados"
echo ""

# ===== PASO 4: Clonar Repositorio =====
echo "4️⃣ Clonando repositorio..."
cd /var/www
if [ -d "smartsales365" ]; then
    echo "⚠️ El directorio ya existe. ¿Sobrescribir? (s/n)"
    read -r respuesta
    if [ "$respuesta" == "s" ] || [ "$respuesta" == "S" ]; then
        rm -rf smartsales365
    else
        echo "Saltando clonación..."
        cd smartsales365
    fi
fi

if [ ! -d "smartsales365" ]; then
    git clone https://github.com/susy215/ecommerce.git smartsales365
    cd smartsales365
else
    cd smartsales365
    git pull  # Actualizar si ya existe
fi
echo "✅ Repositorio clonado"
echo ""

# ===== PASO 5: Crear Entorno Virtual =====
echo "5️⃣ Creando entorno virtual..."
python3 -m venv venv
source venv/bin/activate
echo "✅ Entorno virtual creado"
echo ""

# ===== PASO 6: Instalar Dependencias Python =====
echo "6️⃣ Instalando dependencias Python..."
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
echo "✅ Dependencias Python instaladas"
echo ""

# ===== PASO 7: Crear Archivo .env =====
echo "7️⃣ Configurando archivo .env..."
if [ ! -f ".env" ]; then
    echo "📝 Creando archivo .env desde plantilla..."
    if [ -f "docs/ENV_PRODUCTION_TEMPLATE.txt" ]; then
        cp docs/ENV_PRODUCTION_TEMPLATE.txt .env
        echo "⚠️ IMPORTANTE: Edita el archivo .env con tus valores reales"
        echo "   Ejecuta: nano .env"
    else
        echo "⚠️ Plantilla no encontrada. Creando .env básico..."
        cat > .env << EOF
DJANGO_SECRET_KEY=GENERA-UNA-CLAVE-SEGURA-AQUI
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com
DB_NAME=smartsales365
DB_USER=postgres
DB_PASSWORD=
DB_HOST=
DB_PORT=5432
EOF
    fi
else
    echo "⚠️ El archivo .env ya existe. No se sobrescribirá."
fi
echo "✅ Archivo .env configurado"
echo ""

# ===== RESUMEN =====
echo ""
echo "═══════════════════════════════════════════════════════"
echo "✅ SETUP COMPLETADO"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "📋 Próximos pasos:"
echo ""
echo "1. Edita el archivo .env con tus valores:"
echo "   nano /var/www/smartsales365/.env"
echo ""
echo "2. Ejecuta migraciones:"
echo "   cd /var/www/smartsales365"
echo "   source venv/bin/activate"
echo "   export DJANGO_SETTINGS_MODULE=core.settings_production"
echo "   python manage.py migrate"
echo ""
echo "3. Recolecta archivos estáticos:"
echo "   python manage.py collectstatic --noinput"
echo ""
echo "4. Crea superusuario (opcional):"
echo "   python manage.py createsuperuser"
echo ""
echo "5. Configura Nginx (ver docs/DEPLOY_AWS_PASO_A_PASO.md)"
echo ""
echo "═══════════════════════════════════════════════════════"

