# 📋 Guía Rápida: Conectarte a EC2

## 🔑 Paso 1: Obtener IP Pública de EC2

1. Ve a [AWS Console](https://console.aws.amazon.com/ec2/)
2. Click en **EC2** → **Instances**
3. Selecciona tu instancia
4. Copia la **IPv4 Public IP** (ejemplo: `54.123.45.67`)

---

## 🔌 Paso 2: Conectarte desde PowerShell

Abre PowerShell y ejecuta:

```powershell
# Primero, ajustar permisos (solo primera vez)
icacls "C:\Users\httpReen\Desktop\CALIDAD\smartsales365\ventas_reportes.pem" /inheritance:r
icacls "C:\Users\httpReen\Desktop\CALIDAD\smartsales365\ventas_reportes.pem" /grant:r "%USERNAME%:R"

# Luego conectar (REEMPLAZA TU-IP-PUBLICA con tu IP real)
ssh -i "C:\Users\httpReen\Desktop\CALIDAD\smartsales365\ventas_reportes.pem" ec2-user@TU-IP-PUBLICA
```

**Si usas Ubuntu**, cambia `ec2-user` por `ubuntu`:

```powershell
ssh -i "C:\Users\httpReen\Desktop\CALIDAD\smartsales365\ventas_reportes.pem" ubuntu@TU-IP-PUBLICA
```

---

## ✅ Paso 3: Verificar Conexión

Cuando te conectes, deberías ver algo como:

```
       __|  __|_  )
       _|  (     /   Amazon Linux 2023 AMI
      ___|\___|___|

[ec2-user@ip-xxx-xxx-xxx-xxx ~]$
```

---

## 🚀 Paso 4: Ejecutar Setup Automático

Una vez conectado, ejecuta:

```bash
# Descargar y ejecutar script de setup
curl -o setup.sh https://raw.githubusercontent.com/susy215/ecommerce/main/scripts/SETUP_COMPLETO_EC2.sh
chmod +x setup.sh
bash setup.sh
```

**O manualmente**, copia y pega el contenido de `scripts/SETUP_COMPLETO_EC2.sh` y ejecútalo.

---

## 📝 Ejemplo Completo

```powershell
# En PowerShell (tu máquina Windows)
ssh -i "C:\Users\httpReen\Desktop\CALIDAD\smartsales365\ventas_reportes.pem" ec2-user@54.123.45.67

# Una vez conectado (dentro de EC2):
cd /var/www
git clone https://github.com/susy215/ecommerce.git smartsales365
cd smartsales365
bash scripts/SETUP_COMPLETO_EC2.sh
```

---

## ❓ Problemas Comunes

### "Permission denied"
- Verifica permisos del PEM con `icacls`
- Verifica que Security Group permita SSH desde tu IP

### "Connection timed out"
- Verifica que la IP sea correcta
- Verifica Security Group en AWS Console

---

**¡Avísame cuando te hayas conectado!** 🚀

