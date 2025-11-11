# 🔍 Verificar Conexión a EC2 - Checklist

## 📋 Checklist Rápido

### ✅ 1. Verificar tu IP Pública

```powershell
# En PowerShell
Invoke-RestMethod -Uri "https://api.ipify.org?format=json"
```

**Guarda esta IP** (ejemplo: `201.123.45.67`)

---

### ✅ 2. Verificar Estado de EC2

1. Ve a: https://console.aws.amazon.com/ec2/
2. Click en **Instances**
3. Verifica que tu instancia esté:
   - **State**: ✅ Running (verde)
   - **Status checks**: ✅ 2/2 checks passed

**Si está Stopped:**
- Selecciónala → **Instance state** → **Start instance**

---

### ✅ 3. Verificar Security Group

1. Selecciona tu instancia
2. Abajo, pestaña **Security**
3. Click en el **Security Group** (ej: `sg-0123456789abcdef0`)
4. Click en **Edit inbound rules**
5. **Verifica que exista una regla:**
   - **Type**: SSH
   - **Port**: 22
   - **Source**: Tu IP o `My IP` o `0.0.0.0/0` (temporal)

**Si NO existe:**
- Click **Add rule**
- Type: SSH
- Port: 22
- Source: **My IP** (botón) o pega tu IP manualmente
- Save rules

---

### ✅ 4. Verificar IP Pública de EC2

1. Selecciona tu instancia
2. Abajo, pestaña **Details**
3. Busca **Public IPv4 address**
4. **Copia esta IP** (ejemplo: `18.188.65.153`)

**⚠️ IMPORTANTE:** 
- Si reinicias la instancia, esta IP puede cambiar
- Para IP fija, necesitas **Elastic IP** (configuración avanzada)

---

### ✅ 5. Intentar Conectar

```powershell
# Reemplaza con tu IP real
ssh -i "C:\Users\httpReen\Desktop\CALIDAD\smartsales365\ventas_reportes.pem" ec2-user@18.188.65.153
```

**Si usas Ubuntu:**
```powershell
ssh -i "C:\Users\httpReen\Desktop\CALIDAD\smartsales365\ventas_reportes.pem" ubuntu@18.188.65.153
```

---

## 🐛 Errores Comunes

### ❌ "Connection timed out"
**Causa:** Security Group no permite SSH desde tu IP
**Solución:** Configura Security Group (ver arriba)

### ❌ "Permission denied (publickey)"
**Causa:** Archivo PEM con permisos incorrectos o usuario incorrecto
**Solución:** 
- Verifica permisos: `icacls` ya ejecutado ✅
- Verifica usuario: `ec2-user` (Amazon Linux) o `ubuntu` (Ubuntu)

### ❌ "Host key verification failed"
**Causa:** IP cambió o primera conexión
**Solución:**
```powershell
# Eliminar clave conocida
ssh-keygen -R 18.188.65.153
# Intentar de nuevo
```

---

## 🎯 Orden de Verificación

1. ✅ Tu IP pública → Configurar Security Group
2. ✅ Estado EC2 → Debe estar Running
3. ✅ Security Group → Debe permitir SSH desde tu IP
4. ✅ IP Pública EC2 → Usar esta IP para conectar
5. ✅ Conectar → Probar SSH

---

**Sigue estos pasos en orden y avísame en qué paso estás!** 🚀








