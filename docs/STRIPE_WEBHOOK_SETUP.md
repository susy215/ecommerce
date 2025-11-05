# 🔔 Configuración de Webhooks de Stripe

## 🚨 Problema Resuelto

Los pagos con Stripe se procesaban correctamente, pero los pedidos quedaban como "Pendientes" porque el backend nunca recibía la notificación de que el pago fue exitoso.

**✅ SOLUCIÓN:** Configurar webhooks de Stripe para notificar automáticamente al backend cuando un pago se completa.

---

## 📋 Checklist de Configuración

- [x] Endpoint `/api/compra/stripe/webhook/` que recibe POST
- [x] Verificación de firma de Stripe con `STRIPE_WEBHOOK_SECRET`
- [x] Actualización de `pagado_en` cuando el pago es exitoso
- [x] Inclusión de `metadata.compra_id` en la sesión de Stripe
- [ ] **Configurar webhook en Stripe Dashboard** (PASO MANUAL)
- [ ] **Agregar `STRIPE_WEBHOOK_SECRET` a variables de entorno**

---

## 🔧 Paso 1: Verificar el Código Backend

El código ya está implementado correctamente:

### ✅ Endpoint del Webhook

**URL:** `POST /api/compra/stripe/webhook/`

**Ubicación:** `compra/views.py` → `StripeWebhookView`

**Características:**
- ✅ Exento de CSRF (requerido para webhooks externos)
- ✅ Sin autenticación (Stripe verifica con firma)
- ✅ Verifica firma del webhook con `STRIPE_WEBHOOK_SECRET`
- ✅ Procesa evento `checkout.session.completed`
- ✅ Actualiza `pagado_en` automáticamente
- ✅ Envía notificación push al cliente

### ✅ Metadata en Sesión de Stripe

Cuando se crea una sesión de Stripe (en `stripe_session`), se incluye:

```python
session = stripe.checkout.Session.create(
    mode='payment',
    line_items=line_items,
    metadata={'compra_id': str(compra.id)},  # ✅ Incluido
    payment_intent_data={'metadata': {'compra_id': str(compra.id)}},
)
```

---

## 🌐 Paso 2: Configurar Webhook en Stripe Dashboard

### A. Acceder a Stripe Dashboard

1. Ve a [https://dashboard.stripe.com](https://dashboard.stripe.com)
2. Inicia sesión con tu cuenta de Stripe
3. Selecciona el entorno correcto:
   - **Test mode** para desarrollo
   - **Live mode** para producción

### B. Crear Endpoint de Webhook

1. En el menú lateral, ve a **Developers** → **Webhooks**
2. Haz clic en **Add endpoint**
3. Completa el formulario:

   **Endpoint URL:**
   ```
   https://tu-backend.com/api/compra/stripe/webhook/
   ```
   
   ⚠️ **IMPORTANTE:** 
   - En producción usa tu dominio real (ej: `https://api.smartsales365.com`)
   - En desarrollo local, usa [Stripe CLI](https://stripe.com/docs/stripe-cli) o un túnel (ngrok, localtunnel)

   **Eventos a escuchar:**
   - Selecciona **Send test webhook** para probar
   - O selecciona manualmente: `checkout.session.completed`

4. Haz clic en **Add endpoint**

### C. Obtener el Signing Secret

Después de crear el endpoint:

1. Haz clic en el endpoint creado
2. En la sección **Signing secret**, haz clic en **Reveal**
3. **Copia el secreto** (empieza con `whsec_...`)

   ⚠️ **IMPORTANTE:** Guarda este secreto de forma segura. No lo compartas públicamente.

---

## 🔐 Paso 3: Configurar Variable de Entorno

### En desarrollo (`.env`)

Agrega la siguiente línea a tu archivo `.env`:

```env
STRIPE_WEBHOOK_SECRET=whsec_tu_secreto_aqui
```

### En producción

Agrega la variable de entorno en tu plataforma de hosting:

**Heroku:**
```bash
heroku config:set STRIPE_WEBHOOK_SECRET=whsec_tu_secreto_aqui
```

**Railway:**
```bash
railway variables set STRIPE_WEBHOOK_SECRET=whsec_tu_secreto_aqui
```

**DigitalOcean:**
```bash
# En el panel de control → App Settings → Environment Variables
STRIPE_WEBHOOK_SECRET=whsec_tu_secreto_aqui
```

**Otros servicios:**
Consulta la documentación de tu proveedor sobre cómo agregar variables de entorno.

---

## 🧪 Paso 4: Probar el Webhook

### Opción A: Usar Stripe CLI (Recomendado para desarrollo local)

1. **Instalar Stripe CLI:**
   ```bash
   # Windows (con Chocolatey)
   choco install stripe
   
   # macOS
   brew install stripe/stripe-cli/stripe
   
   # Linux
   # Descargar desde https://github.com/stripe/stripe-cli/releases
   ```

2. **Autenticarse:**
   ```bash
   stripe login
   ```

3. **Hacer túnel al webhook local:**
   ```bash
   stripe listen --forward-to http://localhost:8000/api/compra/stripe/webhook/
   ```

4. **En otra terminal, activar el webhook secret:**
   ```bash
   stripe trigger checkout.session.completed
   ```

   Esto generará un evento de prueba que se enviará a tu endpoint local.

### Opción B: Usar ngrok (Alternativa)

1. **Instalar ngrok:**
   ```bash
   # Descargar desde https://ngrok.com/download
   ```

2. **Crear túnel:**
   ```bash
   ngrok http 8000
   ```

3. **Copiar la URL HTTPS** (ej: `https://abc123.ngrok.io`)

4. **En Stripe Dashboard:**
   - Crear webhook con URL: `https://abc123.ngrok.io/api/compra/stripe/webhook/`
   - Obtener el signing secret
   - Agregarlo a `.env`

5. **Probar manualmente:**
   - En Stripe Dashboard → Webhooks → Tu endpoint → **Send test webhook**
   - Selecciona evento: `checkout.session.completed`

### Opción C: Probar con pago real (en Test Mode)

1. Crear una compra desde el frontend
2. Pagar con tarjeta de prueba: `4242 4242 4242 4242`
3. Verificar en los logs del backend que el webhook fue recibido
4. Verificar que la compra se marcó como pagada

---

## 📊 Verificar que Funciona

### En los Logs del Backend

Deberías ver algo como:

```
INFO: Webhook verificado: checkout.session.completed
INFO: ✅ Compra #123 pagada via Stripe webhook. Payment Intent: pi_xxx, Total: $150.00
INFO: Notificación push enviada para compra #123
```

### En la Base de Datos

Verifica que la compra tenga:
- `pagado_en` != NULL
- `pago_referencia` = Payment Intent ID
- `stripe_payment_intent` = Payment Intent ID

### En Stripe Dashboard

1. Ve a **Payments** → Selecciona un pago
2. En la sección **Webhooks**, deberías ver que el evento fue entregado exitosamente

---

## 🐛 Solución de Problemas

### ❌ Error: "Firma inválida"

**Causa:** El `STRIPE_WEBHOOK_SECRET` no coincide con el secreto del endpoint en Stripe.

**Solución:**
1. Verifica que copiaste el secreto completo (incluye `whsec_`)
2. Verifica que no hay espacios extra
3. Regenera el secreto en Stripe Dashboard si es necesario

### ❌ Error: "No se encontró compra_id en metadata"

**Causa:** La sesión de Stripe no tiene `metadata.compra_id`.

**Solución:**
1. Verifica que el código en `stripe_session` incluye `metadata={'compra_id': str(compra.id)}`
2. Verifica que estás usando la versión más reciente del código

### ❌ Error: "Compra X no encontrada"

**Causa:** El `compra_id` en metadata no existe en la base de datos.

**Solución:**
1. Verifica que la compra existe antes de crear la sesión de Stripe
2. Verifica que no hay un error de conversión de tipo (debe ser int)

### ❌ Webhook no se recibe en producción

**Causa:** El endpoint no es accesible públicamente o hay problemas de firewall.

**Solución:**
1. Verifica que tu servidor tiene HTTPS configurado
2. Verifica que el endpoint está accesible desde internet:
   ```bash
   curl https://tu-backend.com/api/compra/stripe/webhook/ -X POST
   ```
3. Verifica logs del servidor/firewall
4. En Stripe Dashboard, revisa los intentos de entrega del webhook

### ❌ CSRF Token Error

**Causa:** El middleware CSRF está bloqueando el webhook.

**Solución:**
El código ya incluye `csrf_exempt` en el webhook. Si aún tienes problemas:
1. Verifica que estás usando la versión más reciente del código
2. Reinicia el servidor Django

---

## 🔄 Flujo Completo

```
1. Cliente hace checkout
   ↓
2. Backend crea sesión de Stripe con metadata.compra_id
   ↓
3. Cliente paga en Stripe Checkout
   ↓
4. Stripe procesa el pago
   ↓
5. Stripe envía webhook checkout.session.completed
   ↓
6. Backend verifica firma del webhook
   ↓
7. Backend extrae compra_id de metadata
   ↓
8. Backend actualiza compra.pagado_en = now()
   ↓
9. Backend envía notificación push al cliente
   ↓
10. ✅ Cliente recibe confirmación de pago
```

---

## 📝 Variables de Entorno Requeridas

```env
# Stripe
STRIPE_SECRET_KEY=sk_test_...              # Clave secreta de Stripe
STRIPE_PUBLISHABLE_KEY=pk_test_...          # Clave pública (para frontend)
STRIPE_WEBHOOK_SECRET=whsec_...            # ⚠️ CRÍTICO para webhooks
STRIPE_CURRENCY=usd                         # Moneda (opcional, default: usd)

# Frontend
FRONTEND_URL=http://localhost:5173          # URL del frontend (para redirects)
```

---

## ✅ Checklist Final

- [ ] Webhook creado en Stripe Dashboard
- [ ] `STRIPE_WEBHOOK_SECRET` agregado a variables de entorno
- [ ] Endpoint accesible públicamente (HTTPS en producción)
- [ ] Probar con Stripe CLI o pago de prueba
- [ ] Verificar logs del backend
- [ ] Verificar que compras se marcan como pagadas
- [ ] Verificar que notificaciones push se envían

---

## 📚 Recursos Adicionales

- [Documentación de Webhooks de Stripe](https://stripe.com/docs/webhooks)
- [Stripe CLI](https://stripe.com/docs/stripe-cli)
- [Testing Webhooks Localmente](https://stripe.com/docs/webhooks/test)
- [Best Practices de Webhooks](https://stripe.com/docs/webhooks/best-practices)

---

**🎉 ¡Listo!** Una vez configurado, los pagos con Stripe actualizarán automáticamente el estado de las compras en tu sistema.

