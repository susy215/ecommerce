# 🔌 Conectar a EC2 - Comandos Corregidos para PowerShell

## 🔑 Paso 1: Ajustar Permisos del Archivo PEM

### En PowerShell, ejecuta estos comandos:

```powershell
# Obtener tu nombre de usuario
$usuario = $env:USERNAME

# Quitar herencia de permisos
icacls "C:\Users\httpReen\Desktop\CALIDAD\smartsales365\ventas_reportes.pem" /inheritance:r

# Dar permisos de lectura solo a tu usuario
icacls "C:\Users\httpReen\Desktop\CALIDAD\smartsales365\ventas_reportes.pem" /grant:r "${usuario}:R"
```

**O más simple, ejecuta directamente:**

```powershell
icacls "C:\Users\httpReen\Desktop\CALIDAD\smartsales365\ventas_reportes.pem" /inheritance:r
icacls "C:\Users\httpReen\Desktop\CALIDAD\smartsales365\ventas_reportes.pem" /grant:r "$($env:USERNAME):R"
```

---

## 🔌 Paso 2: Obtener tu IP Pública de EC2

1. Ve a [AWS Console](https://console.aws.amazon.com/ec2/)
2. Click en **EC2** → **Instances**
3. Selecciona tu instancia
4. Copia la **IPv4 Public IP** (ejemplo: `54.123.45.67`)

---

## 🔌 Paso 3: Conectarte a EC2

### En PowerShell, ejecuta:

```powershell
# Reemplaza TU-IP-PUBLICA con tu IP real
ssh -i "C:\Users\httpReen\Desktop\CALIDAD\smartsales365\ventas_reportes.pem" ec2-user@TU-IP-PUBLICA
```

**Si usas Ubuntu**, cambia `ec2-user` por `ubuntu`:

```powershell
ssh -i "C:\Users\httpReen\Desktop\CALIDAD\smartsales365\ventas_reportes.pem" ubuntu@TU-IP-PUBLICA
```

---

## ✅ Ejemplo Completo

```powershell
# 1. Ajustar permisos
icacls "C:\Users\httpReen\Desktop\CALIDAD\smartsales365\ventas_reportes.pem" /inheritance:r
icacls "C:\Users\httpReen\Desktop\CALIDAD\smartsales365\ventas_reportes.pem" /grant:r "$($env:USERNAME):R"

# 2. Conectar (reemplaza 54.123.45.67 con tu IP real)
ssh -i "C:\Users\httpReen\Desktop\CALIDAD\smartsales365\ventas_reportes.pem" ec2-user@54.123.45.67
```

---

## 🚀 Una Vez Conectado

Cuando te conectes exitosamente, verás algo como:

```
       __|  __|_  )
       _|  (     /   Amazon Linux 2023 AMI
      ___|\___|___|

[ec2-user@ip-xxx-xxx-xxx-xxx ~]$
```

**Entonces ejecuta:**

```bash
# Clonar repositorio
cd /var/www
sudo mkdir -p smartsales365
sudo chown ec2-user:ec2-user smartsales365
cd smartsales365
git clone https://github.com/susy215/ecommerce.git .

# Ejecutar setup
bash scripts/SETUP_COMPLETO_EC2.sh
```

---

## ❓ Si Aún Tienes Problemas

### Opción Alternativa: Usar WSL (Windows Subsystem for Linux)

Si tienes WSL instalado, es más fácil:

```bash
# En WSL Bash
chmod 400 /mnt/c/Users/httpReen/Desktop/CALIDAD/smartsales365/ventas_reportes.pem
ssh -i /mnt/c/Users/httpReen/Desktop/CALIDAD/smartsales365/ventas_reportes.pem ec2-user@TU-IP-PUBLICA
```

---

**¡Prueba el comando corregido y avísame si funciona!** 🚀

