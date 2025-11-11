#!/bin/bash
# Script de configuración inicial de EC2

set -e

echo "🔧 Configurando EC2 para SmartSales365..."

# Detectar sistema operativo
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "No se pudo detectar el sistema operativo"
    exit 1
fi

# Instalar dependencias según el OS
if [ "$OS" == "amzn" ] || [ "$OS" == "amazon" ]; then
    echo "📦 Instalando dependencias (Amazon Linux)..."
    sudo dnf update -y
    sudo dnf install -y python3 python3-pip python3-devel postgresql15 git nginx certbot python3-certbot-nginx
elif [ "$OS" == "ubuntu" ]; then
    echo "📦 Instalando dependencias (Ubuntu)..."
    sudo apt update -y
    sudo apt upgrade -y
    sudo apt install -y python3 python3-pip python3-venv postgresql-client git nginx certbot python3-certbot-nginx
else
    echo "Sistema operativo no soportado: $OS"
    exit 1
fi

# Crear directorios
echo "📁 Creando directorios..."
sudo mkdir -p /var/www/smartsales365/static
sudo mkdir -p /var/www/smartsales365/media
sudo mkdir -p /var/log/smartsales365
sudo chown -R $USER:$USER /var/www/smartsales365
sudo chown -R $USER:$USER /var/log/smartsales365

echo "✅ Configuración inicial completada!"
echo ""
echo "Siguiente paso: Sube tu código a /var/www/smartsales365"

