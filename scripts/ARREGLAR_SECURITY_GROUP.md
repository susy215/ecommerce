# 🔒 Arreglar Security Group - Connection Timed Out

## ⚠️ Problema

El error `Connection timed out` significa que el Security Group de tu EC2 **no permite conexiones SSH desde tu IP**.

---

## ✅ Solución: Configurar Security Group

### Paso 1: Obtener tu IP Pública

**Opción A: Desde PowerShell**
```powershell
# Ver tu IP pública
Invoke-RestMethod -Uri "https://api.ipify.org?format=json"
```

**Opción B: Desde navegador**
- Ve a: https://www.whatismyip.com/
- Copia tu IP pública

---

### Paso 2: Configurar Security Group en AWS

1. **Ve a AWS Console** → **EC2** → **Instances**
2. **Selecciona tu instancia**
3. Abajo, en la pestaña **Security**, haz click en el **Security Group** (ej: `sg-xxxxx`)
4. Click en **Edit inbound rules**
5. Click en **Add rule**
6. Configura:
   - **Type**: SSH
   - **Protocol**: TCP
   - **Port**: 22
   - **Source**: **My IP** (botón) o **Custom** y pega tu IP pública
   - **Description**: "SSH desde mi máquina"
7. Click en **Save rules**

---

### Paso 3: Verificar que la Instancia está Running

1. En la lista de instancias, verifica que el estado sea **Running**
2. Si está **Stopped**, selecciónala y click en **Start instance**

---

### Paso 4: Verificar IP Pública

1. Selecciona tu instancia
2. Abajo, en **Details**, verifica la **Public IPv4 address**
3. Asegúrate de que sea `18.188.65.153` (o la que estés usando)

**⚠️ IMPORTANTE:** Si detienes y reinicias la instancia, la IP pública puede cambiar (a menos que tengas Elastic IP configurada).

---

### Paso 5: Intentar Conectar Nuevamente

Después de configurar el Security Group, espera 10-30 segundos y prueba:

```powershell
ssh -i "C:\Users\httpReen\Desktop\CALIDAD\smartsales365\ventas_reportes.pem" ec2-user@18.188.65.153
```

---

## 🔍 Verificación Paso a Paso

### 1. Verificar tu IP
```powershell
Invoke-RestMethod -Uri "https://api.ipify.org?format=json"
```

### 2. Verificar que EC2 está Running
- AWS Console → EC2 → Instances → Estado debe ser "Running"

### 3. Verificar Security Group
- Instancia → Security → Security Group → Inbound rules debe tener SSH (22) desde tu IP

### 4. Verificar IP Pública de EC2
- Instancia → Details → Public IPv4 address

---

## 🆘 Si Aún No Funciona

### Opción 1: Permitir SSH desde Cualquier IP (Temporal - NO RECOMENDADO para producción)

1. Security Group → Edit inbound rules
2. Cambia la regla SSH:
   - **Source**: `0.0.0.0/0` (cualquier IP)
3. **⚠️ ADVERTENCIA:** Esto es inseguro. Solo para pruebas.
4. **Recuerda cambiarlo después** a solo tu IP.

### Opción 2: Verificar Firewall de Windows

```powershell
# Verificar que Windows Firewall no esté bloqueando
Get-NetFirewallRule | Where-Object {$_.DisplayName -like "*SSH*"}
```

### Opción 3: Usar Session Manager (Alternativa)

Si SSH sigue sin funcionar, puedes usar AWS Systems Manager Session Manager:

1. Instala AWS CLI: https://aws.amazon.com/cli/
2. Instala Session Manager Plugin: https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html
3. Conecta:
```powershell
aws ssm start-session --target i-xxxxxxxxxxxxx
```

---

## ✅ Checklist

- [ ] Mi IP pública obtenida
- [ ] Security Group configurado con SSH (22) desde mi IP
- [ ] Instancia EC2 está en estado "Running"
- [ ] IP pública de EC2 verificada
- [ ] Intentado conectar nuevamente

---

**Configura el Security Group y avísame si funciona!** 🔒








