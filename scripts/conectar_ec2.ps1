# Script PowerShell para conectar a EC2 y configurar SSL

$PEM_FILE = "C:\Users\httpReen\Desktop\CALIDAD\smartsales365\ventas_reportes.pem"
$EC2_IP = "18.188.65.153"
$EC2_USER = "ubuntu"

Write-Host "🔌 Conectando a EC2..." -ForegroundColor Cyan
Write-Host ""

# Verificar que el archivo PEM existe
if (-not (Test-Path $PEM_FILE)) {
    Write-Host "❌ Error: No se encuentra el archivo PEM" -ForegroundColor Red
    Write-Host "   Ruta: $PEM_FILE" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Archivo PEM encontrado" -ForegroundColor Green
Write-Host ""

# Configurar permisos del archivo PEM
Write-Host "🔑 Configurando permisos del archivo PEM..." -ForegroundColor Cyan

try {
    # Eliminar herencia de permisos
    icacls $PEM_FILE /inheritance:r | Out-Null
    
    # Dar permisos de solo lectura al usuario actual
    icacls $PEM_FILE /grant:r "$($env:USERNAME):R" | Out-Null
    
    Write-Host "✅ Permisos configurados correctamente" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "⚠️  No se pudieron cambiar los permisos automáticamente" -ForegroundColor Yellow
    Write-Host "   Ejecuta estos comandos manualmente:" -ForegroundColor Yellow
    Write-Host "   icacls `"$PEM_FILE`" /inheritance:r" -ForegroundColor White
    Write-Host "   icacls `"$PEM_FILE`" /grant:r `"$($env:USERNAME):R`"" -ForegroundColor White
    Write-Host ""
}

# Conectar a EC2
Write-Host "🚀 Conectando a $EC2_USER@$EC2_IP..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Una vez conectado, ejecuta:" -ForegroundColor Yellow
Write-Host "  bash -c `"`$(curl -fsSL https://raw.githubusercontent.com/susy215/ecommerce/main/scripts/setup_ssl.sh)`"" -ForegroundColor White
Write-Host ""
Write-Host "O si tienes el archivo localmente:" -ForegroundColor Yellow  
Write-Host "  cd /var/www/smartsales365" -ForegroundColor White
Write-Host "  bash scripts/setup_ssl.sh" -ForegroundColor White
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan

# Intentar conectar
ssh -i $PEM_FILE "$EC2_USER@$EC2_IP"

