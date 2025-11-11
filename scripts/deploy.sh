#!/bin/bash
# Script de deployment simple para AWS EC2

set -e  # Salir si hay error

echo "🚀 Iniciando deployment..."

# Activar entorno virtual
source /var/www/smartsales365/venv/bin/activate

# Ir al directorio del proyecto
cd /var/www/smartsales365

# Configurar settings
export DJANGO_SETTINGS_MODULE=core.settings_production

# Actualizar código (si usas git)
if [ -d ".git" ]; then
    echo "📥 Actualizando código desde Git..."
    git pull
fi

# Instalar/actualizar dependencias
echo "📦 Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

# Ejecutar migraciones
echo "🗄️ Ejecutando migraciones..."
python manage.py migrate --noinput

# Recolectar archivos estáticos
echo "📁 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

# Reiniciar servicio
echo "🔄 Reiniciando servicio..."
sudo systemctl restart smartsales365

echo "✅ Deployment completado!"

