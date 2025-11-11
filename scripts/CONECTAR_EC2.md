# 🔌 Cómo Conectarte a EC2 - Paso a Paso

## 📍 Tu Información

- **Archivo PEM**: `C:\Users\httpReen\Desktop\CALIDAD\smartsales365\ventas_reportes.pem`
- **Repositorio Git**: `https://github.com/susy215/ecommerce.git`

---

## ⚠️ IMPORTANTE: Necesitas tu IP Pública de EC2

Primero necesitas obtener la **IP Pública** de tu instancia EC2:

1. Ve a **AWS Console** → **EC2** → **Instances**
2. Selecciona tu instancia
3. Copia la **IPv4 Public IP** (ejemplo: `54.123.45.67`)

---

## 🔑 Paso 1: Preparar el Archivo PEM (Solo Primera Vez)

### En PowerShell (Windows):

```powershell
# Cambiar permisos del archivo PEM
icacls "C:\Users\httpReen\Desktop\CALIDAD\smartsales365\ventas_reportes.pem" /inheritance:r
icacls "C:\Users\httpReen\Desktop\CALIDAD\smartsales365\ventas_reportes.pem" /grant:r "%USERNAME%:R"
```

---

## 🔌 Paso 2: Conectarte a EC2

### Opción A: PowerShell (Recomendado)

```powershell
# Conectar (reemplaza TU-IP-PUBLICA con tu IP real)
ssh -i "C:\Users\httpReen\Desktop\CALIDAD\smartsales365\ventas_reportes.pem" ec2-user@TU-IP-PUBLICA
```

**Nota:** 
- Si usas **Amazon Linux 2023**, el usuario es `ec2-user`
- Si usas **Ubuntu**, el usuario es `ubuntu`

### Opción B: Usar WSL (Windows Subsystem for Linux)

Si tienes WSL instalado:

```bash
# En WSL
chmod 400 /mnt/c/Users/httpReen/Desktop/CALIDAD/smartsales365/ventas_reportes.pem
ssh -i /mnt/c/Users/httpReen/Desktop/CALIDAD/smartsales365/ventas_reportes.pem ec2-user@TU-IP-PUBLICA
```

---

## ✅ Paso 3: Verificar que Estás Conectado

Cuando te conectes exitosamente, deberías ver algo como:

```
       __|  __|_  )
       _|  (     /   Amazon Linux 2023 AMI
      ___|\___|___|

https://aws.amazon.com/amazon-linux-2023/
[ec2-user@ip-xxx-xxx-xxx-xxx ~]$
```

---

## 📋 Siguiente Paso: Ejecutar Setup

Una vez conectado, ejecuta estos comandos **uno por uno**:

```bash
# 1. Actualizar sistema
sudo dnf update -y

# 2. Instalar dependencias básicas
sudo dnf install -y python3 python3-pip python3-devel postgresql15 git nginx certbot python3-certbot-nginx

# 3. Crear directorios
sudo mkdir -p /var/www/smartsales365/static
sudo mkdir -p /var/www/smartsales365/media
sudo mkdir -p /var/log/smartsales365
sudo chown -R ec2-user:ec2-user /var/www/smartsales365
sudo chown -R ec2-user:ec2-user /var/log/smartsales365
```

---

## 🚀 Después del Setup Inicial

Sigue los pasos de `docs/DEPLOY_AWS_PASO_A_PASO.md` desde el **Paso 6** en adelante.

---

## ❓ Si Tienes Problemas

### Error: "Permission denied (publickey)"

- Verifica que el archivo PEM tenga los permisos correctos
- Verifica que estés usando el usuario correcto (`ec2-user` o `ubuntu`)

### Error: "Connection timed out"

- Verifica que tu Security Group permita SSH (puerto 22) desde tu IP
- Verifica que la IP pública sea correcta

---

**¡Avísame cuando te hayas conectado y seguimos con el siguiente paso!** 🚀

