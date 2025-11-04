# 🚀 Setup Rápido - Notificaciones Push

## ✅ Lo que se implementó

### Backend Django
1. **Nueva app `notificaciones`** con:
   - Modelos: `PushSubscription`, `NotificacionEnviada`
   - Service: `PushNotificationService` (Web Push API)
   - Endpoints REST para suscripción y historial
   - Admin Django integrado

2. **Integración automática** en flujo de compra:
   - ✅ Notificación al crear pedido (checkout)
   - ✅ Notificación al confirmar pago
   - ✅ Notificación en webhook de Stripe

3. **Management command** para generar claves VAPID

### Casos de Uso Implementados
1. **Compra Exitosa**: Cuando el pago se completa
2. **Cambio de Estado**: Cuando el pedido cambia de estado (pagado/enviado/completado)

---

## 📦 Paso 1: Instalar Dependencias

```bash
pip install -r requirements.txt
```

Nuevas dependencias agregadas:
- `py-vapid==1.9.1`
- `pywebpush==1.14.1`

---

## 🔑 Paso 2: Generar Claves VAPID

```bash
python manage.py generate_vapid_keys --email admin@tudominio.com
```

**Output:**
```
✅ Claves VAPID generadas exitosamente!

Agrega estas líneas a tu archivo .env:
--------------------------------------------------------------------------------
VAPID_PRIVATE_KEY=abc123def456...
VAPID_PUBLIC_KEY=xyz789ghi012...
VAPID_ADMIN_EMAIL=admin@tudominio.com
--------------------------------------------------------------------------------
```

Copia las claves y agrégalas a tu archivo `.env`.

---

## 🗄️ Paso 3: Migrar Base de Datos

```bash
python manage.py makemigrations
python manage.py migrate
```

Esto creará las tablas:
- `push_subscriptions`
- `notificaciones_enviadas`

---

## ✅ Paso 4: Verificar Configuración

El archivo `core/settings.py` ya está configurado con:

```python
INSTALLED_APPS = [
    # ...
    'notificaciones',
]

# VAPID Configuration
VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY', '')
VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY', '')
VAPID_CLAIMS = {
    "sub": f"mailto:{os.environ.get('VAPID_ADMIN_EMAIL', 'admin@smartsales365.com')}"
}
```

---

## 🌐 Paso 5: Endpoints Disponibles

### Para el Frontend

1. **Obtener clave pública VAPID** (sin autenticación)
   ```
   GET /api/notificaciones/vapid-public-key/
   ```

2. **Suscribirse a notificaciones** (requiere autenticación)
   ```
   POST /api/notificaciones/subscriptions/
   Headers: Authorization: Token <token>
   Body: {
     "endpoint": "https://...",
     "p256dh": "...",
     "auth": "...",
     "user_agent": "..."
   }
   ```

3. **Ver mis suscripciones**
   ```
   GET /api/notificaciones/subscriptions/
   ```

4. **Ver historial de notificaciones**
   ```
   GET /api/notificaciones/historial/
   ```

---

## 🧪 Paso 6: Probar Backend (Opcional)

```bash
python manage.py shell
```

```python
from notificaciones.push_service import push_service
from usuarios.models import Usuario

# Obtener un usuario de prueba
usuario = Usuario.objects.first()

# Enviar notificación de prueba
resultado = push_service.send_notification(
    usuario=usuario,
    titulo='🧪 Prueba de Notificaciones',
    mensaje='¡Las notificaciones funcionan correctamente!',
    tipo='otro',
    url='/test'
)

print(resultado)
# {'exitosos': 0, 'fallidos': 0, 'mensaje': 'Sin suscripciones activas'}
# Normal si aún no hay suscripciones desde el frontend
```

---

## 💻 Paso 7: Implementar en Frontend (React + Vite)

### 7.1 Crear Service Worker

Archivo: `public/sw.js`

```javascript
self.addEventListener('push', event => {
  if (event.data) {
    const data = event.data.json();
    const options = {
      body: data.body,
      icon: data.icon || '/icon-192x192.png',
      badge: data.badge || '/badge-72x72.png',
      vibrate: [100, 50, 100],
      data: data.data
    };
    
    event.waitUntil(
      self.registration.showNotification(data.title, options)
    );
  }
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  const urlToOpen = event.notification.data.url || '/';
  event.waitUntil(
    clients.openWindow(urlToOpen)
  );
});
```

### 7.2 Crear Utilidad de Push

Archivo: `src/utils/pushNotifications.ts`

Ver contenido completo en: `docs/NOTIFICACIONES_PUSH.md`

Código principal:
```typescript
export async function subscribeToPushNotifications(token: string) {
  // 1. Registrar service worker
  const registration = await navigator.serviceWorker.register('/sw.js');
  
  // 2. Solicitar permiso
  const permission = await Notification.requestPermission();
  if (permission !== 'granted') return;
  
  // 3. Obtener clave VAPID
  const vapidKey = await getVapidPublicKey();
  
  // 4. Suscribirse
  const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(vapidKey)
  });
  
  // 5. Enviar al backend
  await fetch(`${API_URL}/api/notificaciones/subscriptions/`, {
    method: 'POST',
    headers: {
      'Authorization': `Token ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      endpoint: subscription.endpoint,
      p256dh: arrayBufferToBase64(subscription.getKey('p256dh')),
      auth: arrayBufferToBase64(subscription.getKey('auth')),
      user_agent: navigator.userAgent
    })
  });
}
```

### 7.3 Integrar en App

```typescript
// src/App.tsx
import { useEffect } from 'react';
import { subscribeToPushNotifications } from './utils/pushNotifications';

function App() {
  const token = localStorage.getItem('token');
  
  useEffect(() => {
    if (token) {
      subscribeToPushNotifications(token).catch(console.error);
    }
  }, [token]);
  
  return <YourApp />;
}
```

---

## 🔐 Paso 8: HTTPS para Desarrollo Local

**Las notificaciones push SOLO funcionan con HTTPS.**

### Opción 1: mkcert (Recomendado)

```bash
# Instalar mkcert
brew install mkcert  # macOS
# o desde: https://github.com/FiloSottile/mkcert

# Generar certificados
mkcert -install
mkcert localhost 127.0.0.1 ::1

# Configurar Vite (vite.config.ts)
import fs from 'fs';

export default defineConfig({
  server: {
    https: {
      key: fs.readFileSync('./localhost-key.pem'),
      cert: fs.readFileSync('./localhost.pem'),
    },
    port: 5173
  }
});
```

### Opción 2: ngrok (Testing rápido)

```bash
# Terminal 1: Django
python manage.py runserver

# Terminal 2: Vite
npm run dev

# Terminal 3: Exponer con HTTPS
ngrok http 5173
# Usar la URL https://xxxxx.ngrok.io
```

---

## 🚀 Paso 9: Flujo Completo de Prueba

1. **Iniciar backend con HTTPS**
   ```bash
   python manage.py runserver
   ```

2. **Iniciar frontend con HTTPS**
   ```bash
   npm run dev
   ```

3. **Login en el frontend**
   - Automáticamente solicita permiso de notificaciones
   - Se suscribe al backend

4. **Hacer una compra de prueba**
   - Agregar productos al carrito
   - Hacer checkout → **Recibes notificación** 🛒
   - Pagar → **Recibes notificación** 🎉

5. **Verificar en Django Admin**
   - Ir a: `http://localhost:8000/admin/`
   - Sección "Notificaciones Push"
   - Ver suscripciones y historial

---

## 📋 Checklist Final

### Backend ✅
- [x] Dependencias instaladas (`pywebpush`, `py-vapid`)
- [x] App `notificaciones` agregada a `INSTALLED_APPS`
- [x] Claves VAPID generadas y en `.env`
- [x] Migraciones aplicadas
- [x] Integración en flujo de compra
- [x] Endpoints documentados

### Frontend (Tu tarea)
- [ ] Crear `public/sw.js`
- [ ] Crear `src/utils/pushNotifications.ts`
- [ ] Integrar en componente de login/app
- [ ] Configurar HTTPS local (mkcert o ngrok)
- [ ] Probar flujo completo

### Producción (Futuro)
- [ ] Backend en EC2 con nginx + Let's Encrypt
- [ ] Frontend en Vercel (ya tiene HTTPS)
- [ ] Generar claves VAPID nuevas para producción
- [ ] Configurar CORS correctamente
- [ ] Probar en ambiente real

---

## 🐛 Troubleshooting

### "VAPID keys no configuradas"
**Solución:** Ejecutar `python manage.py generate_vapid_keys` y agregar a `.env`

### "Push notifications no soportadas"
**Solución:** Usar HTTPS (mkcert o ngrok) + navegador moderno

### "Service Worker registration failed"
**Solución:** Verificar que `sw.js` está en `/public`

### "Permiso denegado"
**Solución:** Limpiar permisos del navegador o usar ventana de incógnito

### "No recibo notificaciones"
**Solución:** 
1. Verificar que hay una suscripción activa en admin
2. Revisar logs del backend
3. Verificar que el service worker está registrado (DevTools → Application → Service Workers)

---

## 📚 Documentación Completa

Ver `docs/NOTIFICACIONES_PUSH.md` para:
- Código completo del frontend
- Configuración de producción con nginx
- Ejemplos avanzados
- Referencias y recursos

---

## ✨ Características Implementadas

### Notificaciones Automáticas
- ✅ **Al crear pedido** (checkout)
- ✅ **Al confirmar pago** (manual o Stripe)
- ✅ **Webhook de Stripe** (pago confirmado)

### Gestión Inteligente
- ✅ Desactiva automáticamente suscripciones expiradas (410 Gone)
- ✅ Maneja múltiples dispositivos por usuario
- ✅ Historial completo en Django Admin
- ✅ Logging de errores

### Seguridad
- ✅ Encriptación end-to-end (VAPID)
- ✅ Solo funciona con HTTPS
- ✅ Autenticación requerida
- ✅ Validación de permisos

---

## 🎯 Casos de Uso Finales

### 1. Compra Exitosa
```
Título: 🎉 ¡Compra realizada con éxito!
Mensaje: Tu pedido #123 por $150.00 ha sido confirmado.
Click: Redirige a /mis-pedidos/123
```

### 2. Cambio de Estado
```
Título: 📦 Pedido enviado
Mensaje: Tu pedido #123 está en camino. ¡Pronto lo recibirás!
Click: Redirige a /mis-pedidos/123
```

---

**¡Listo!** 🎉 El backend está completamente configurado. Solo falta implementar el frontend siguiendo los pasos del 7 al 9.

