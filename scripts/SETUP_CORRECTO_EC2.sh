#!/bin/bash
# Script correcto para setup en EC2
# Ejecutar DESPUÉS de conectarte

set -e

echo "🚀 Configurando SmartSales365 en EC2..."
echo ""

# ===== PASO 1: Limpiar y Preparar Directorio =====
echo "1️⃣ Preparando directorio..."
cd /var/www
sudo rm -rf smartsales365  # Eliminar si existe
sudo mkdir -p smartsales365
sudo chown -R ubuntu:ubuntu smartsales365
cd smartsales365

# ===== PASO 2: Clonar Repositorio =====
echo "2️⃣ Clonando repositorio..."
git clone https://github.com/susy215/ecommerce.git .
echo "✅ Repositorio clonado"
echo ""

# ===== PASO 3: Verificar Contenido =====
echo "3️⃣ Verificando contenido..."
ls -la
echo ""

# ===== PASO 4: Crear Entorno Virtual =====
echo "4️⃣ Creando entorno virtual..."
python3 -m venv venv
source venv/bin/activate
echo "✅ Entorno virtual creado"
echo ""

# ===== PASO 5: Instalar Dependencias =====
echo "5️⃣ Instalando dependencias Python..."
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
echo "✅ Dependencias instaladas"
echo ""

# ===== RESUMEN =====
echo ""
echo "═══════════════════════════════════════════════════════"
echo "✅ SETUP COMPLETADO"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "📋 Siguiente paso: Configurar .env"
echo ""








