# 🔑 Solucionar "Permission denied (publickey)"

## 🔍 Diagnóstico

El error significa que:
- ✅ La conexión SSH funciona (no hay timeout)
- ❌ La clave PEM no está siendo aceptada

---

## ✅ Soluciones a Probar

### Solución 1: Verificar Usuario Correcto

Depende del sistema operativo de tu EC2:

**Amazon Linux 2023:** `ec2-user`
**Ubuntu:** `ubuntu`
**Debian:** `admin`

**Prueba con Ubuntu:**

```powershell
ssh -i "C:\Users\httpReen\Desktop\CALIDAD\smartsales365\ventas_reportes.pem" ubuntu@18.188.65.153
```

---

### Solución 2: Verificar Permisos del Archivo PEM

```powershell
# Verificar permisos actuales
icacls "C:\Users\httpReen\Desktop\CALIDAD\smartsales365\ventas_reportes.pem"

# Si no ves tu usuario con permisos de lectura, ejecuta:
icacls "C:\Users\httpReen\Desktop\CALIDAD\smartsales365\ventas_reportes.pem" /inheritance:r
icacls "C:\Users\httpReen\Desktop\CALIDAD\smartsales365\ventas_reportes.pem" /grant:r "$($env:USERNAME):R"
```

---

### Solución 3: Verificar que el PEM es Correcto

1. **Ve a AWS Console** → **EC2** → **Instances**
2. **Selecciona tu instancia**
3. **Click en "Connect"** (botón arriba)
4. **En la pestaña "SSH client"**, verifica:
   - ¿Qué Key pair name muestra?
   - ¿Coincide con `ventas_reportes`?

**Si NO coincide:**
- Necesitas usar el archivo PEM correcto que descargaste cuando creaste la instancia

---

### Solución 4: Usar WSL (Si lo tienes instalado)

WSL maneja mejor las claves SSH:

```bash
# En WSL Bash
chmod 400 /mnt/c/Users/httpReen/Desktop/CALIDAD/smartsales365/ventas_reportes.pem
ssh -i /mnt/c/Users/httpReen/Desktop/CALIDAD/smartsales365/ventas_reportes.pem ec2-user@18.188.65.153

# O probar con ubuntu
ssh -i /mnt/c/Users/httpReen/Desktop/CALIDAD/smartsales365/ventas_reportes.pem ubuntu@18.188.65.153
```

---

### Solución 5: Verificar Sistema Operativo de EC2

1. **AWS Console** → **EC2** → **Instances**
2. Selecciona tu instancia
3. Abajo, pestaña **Details**
4. Busca **Platform** o **AMI**
5. Si dice **Ubuntu**, usa usuario `ubuntu`
6. Si dice **Amazon Linux**, usa usuario `ec2-user`

---

### Solución 6: Crear Nueva Key Pair (Última Opción)

Si nada funciona, puedes crear una nueva key pair:

1. **EC2** → **Key Pairs** → **Create key pair**
2. Nombre: `nueva-clave-ec2`
3. Tipo: RSA
4. Formato: `.pem`
5. **Create** y descarga
6. **Stop** tu instancia
7. **Actions** → **Instance settings** → **Edit user data** (si aplica)
8. O mejor: **Launch a new instance** con la nueva clave
9. **Start** la instancia
10. Prueba conectar con la nueva clave

---

## 🎯 Prueba en Este Orden

### 1. Probar con usuario `ubuntu`:

```powershell
ssh -i "C:\Users\httpReen\Desktop\CALIDAD\smartsales365\ventas_reportes.pem" ubuntu@18.188.65.153
```

### 2. Si no funciona, verificar sistema operativo en AWS Console

### 3. Si sigue sin funcionar, usar WSL

### 4. Como último recurso, crear nueva key pair

---

## 🔍 Comando de Diagnóstico

```powershell
# Ver detalles del archivo PEM
Get-Item "C:\Users\httpReen\Desktop\CALIDAD\smartsales365\ventas_reportes.pem" | Select-Object Name, Length, LastWriteTime

# Verificar que el archivo existe y tiene contenido
Get-Content "C:\Users\httpReen\Desktop\CALIDAD\smartsales365\ventas_reportes.pem" | Select-Object -First 5
```

Deberías ver algo como:
```
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
```

---

**Empieza probando con `ubuntu` en lugar de `ec2-user` y avísame qué pasa!** 🔑








