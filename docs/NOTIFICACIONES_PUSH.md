# 📱 Notificaciones Push - SmartSales365

## 🎯 Casos de Uso

### 1. Confirmación de Compra Exitosa ✅
Cuando el pago se completa exitosamente (vía Stripe o método directo).

**Trigger:** Compra marcada como pagada  
**Endpoint Backend:** `POST /api/compra/compras/{id}/pay/`  
**Notificación:**
- Título: "🎉 ¡Compra realizada con éxito!"
- Mensaje: "Tu pedido #{id} por ${total} ha sido confirmado."
- Click: Redirige a `/mis-pedidos/{id}`

### 2. Cambio de Estado de Pedido 📦
Cuando el estado del pedido cambia (pagado → enviado → completado).

**Trigger:** Actualización del modelo Compra  
**Estados:**
- **Pagado:** "✅ Pago confirmado"
- **Enviado:** "📦 Pedido enviado - ¡Pronto lo recibirás!"
- **Completado:** "🎁 Pedido completado - ¡Gracias por tu compra!"

---

## 🔧 Configuración Backend

### 1. Generar Claves VAPID

```bash
python manage.py generate_vapid_keys --email admin@tudominio.com
```

Esto generará output como:

```env
VAPID_PRIVATE_KEY=abc123...
VAPID_PUBLIC_KEY=xyz789...
VAPID_ADMIN_EMAIL=admin@tudominio.com
```

### 2. Agregar a `.env`

```env
# Notificaciones Push
VAPID_PRIVATE_KEY=tu_clave_privada_aqui
VAPID_PUBLIC_KEY=tu_clave_publica_aqui
VAPID_ADMIN_EMAIL=admin@smartsales365.com
```

⚠️ **IMPORTANTE:** 
- La clave PRIVADA debe mantenerse SECRETA
- NUNCA subas las claves a Git
- Usa claves diferentes para dev y producción

### 3. Migrar Base de Datos

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 🌐 Configuración Frontend (React + Vite)

### 1. Crear Service Worker

Archivo: `public/sw.js`

```javascript
// Service Worker para notificaciones push
self.addEventListener('push', event => {
  if (event.data) {
    const data = event.data.json();
    const options = {
      body: data.body,
      icon: data.icon || '/icon-192x192.png',
      badge: data.badge || '/badge-72x72.png',
      vibrate: [100, 50, 100],
      data: data.data,
      actions: [
        { action: 'open', title: 'Ver detalles' },
        { action: 'close', title: 'Cerrar' }
      ]
    };
    
    event.waitUntil(
      self.registration.showNotification(data.title, options)
    );
  }
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  
  if (event.action === 'open' || !event.action) {
    // Abrir la URL especificada en la notificación
    const urlToOpen = event.notification.data.url || '/';
    event.waitUntil(
      clients.openWindow(urlToOpen)
    );
  }
});
```

### 2. Registrar Service Worker

Archivo: `src/utils/pushNotifications.ts`

```typescript
// Configuración de notificaciones push
const BACKEND_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// 1. Obtener clave pública VAPID del servidor
export async function getVapidPublicKey(): Promise<string> {
  const response = await fetch(`${BACKEND_URL}/api/notificaciones/vapid-public-key/`);
  const data = await response.json();
  return data.public_key;
}

// 2. Convertir clave VAPID a formato Uint8Array
function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/\-/g, '+')
    .replace(/_/g, '/');
  
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

// 3. Solicitar permiso y suscribir
export async function subscribeToPushNotifications(token: string): Promise<void> {
  // Verificar soporte del navegador
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
    console.warn('Push notifications no soportadas en este navegador');
    return;
  }
  
  try {
    // Registrar service worker
    const registration = await navigator.serviceWorker.register('/sw.js');
    console.log('Service Worker registrado');
    
    // Solicitar permiso
    const permission = await Notification.requestPermission();
    if (permission !== 'granted') {
      console.log('Permiso de notificaciones denegado');
      return;
    }
    
    // Obtener clave pública
    const vapidPublicKey = await getVapidPublicKey();
    const convertedVapidKey = urlBase64ToUint8Array(vapidPublicKey);
    
    // Suscribirse a push
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: convertedVapidKey
    });
    
    // Enviar suscripción al backend
    await fetch(`${BACKEND_URL}/api/notificaciones/subscriptions/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${token}`
      },
      body: JSON.stringify({
        endpoint: subscription.endpoint,
        p256dh: arrayBufferToBase64(subscription.getKey('p256dh')),
        auth: arrayBufferToBase64(subscription.getKey('auth')),
        user_agent: navigator.userAgent
      })
    });
    
    console.log('✅ Suscrito a notificaciones push');
    
  } catch (error) {
    console.error('Error al suscribirse a notificaciones:', error);
  }
}

// 4. Desuscribirse
export async function unsubscribeFromPushNotifications(token: string): Promise<void> {
  try {
    const registration = await navigator.serviceWorker.getRegistration();
    if (!registration) return;
    
    const subscription = await registration.pushManager.getSubscription();
    if (!subscription) return;
    
    // Desuscribirse localmente
    await subscription.unsubscribe();
    
    // Informar al backend (opcional, se puede solo desactivar)
    // El backend automáticamente desactiva suscripciones expiradas
    
    console.log('✅ Desuscrito de notificaciones push');
  } catch (error) {
    console.error('Error al desuscribirse:', error);
  }
}

// Helper: Convertir ArrayBuffer a Base64
function arrayBufferToBase64(buffer: ArrayBuffer | null): string {
  if (!buffer) return '';
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return window.btoa(binary);
}
```

### 3. Integrar en tu App

```typescript
// src/App.tsx o donde manejes la autenticación
import { useEffect } from 'react';
import { subscribeToPushNotifications } from './utils/pushNotifications';

function App() {
  const token = localStorage.getItem('token'); // Tu token de autenticación
  
  useEffect(() => {
    // Suscribirse automáticamente al iniciar sesión
    if (token) {
      subscribeToPushNotifications(token);
    }
  }, [token]);
  
  return (
    // Tu app...
  );
}
```

### 4. Componente de Configuración (Opcional)

```typescript
// src/components/NotificationSettings.tsx
import { useState } from 'react';
import { subscribeToPushNotifications, unsubscribeFromPushNotifications } from '../utils/pushNotifications';

export function NotificationSettings() {
  const [enabled, setEnabled] = useState(
    Notification.permission === 'granted'
  );
  const token = localStorage.getItem('token')!;
  
  const handleToggle = async () => {
    if (enabled) {
      await unsubscribeFromPushNotifications(token);
      setEnabled(false);
    } else {
      await subscribeToPushNotifications(token);
      setEnabled(Notification.permission === 'granted');
    }
  };
  
  return (
    <div className="notification-settings">
      <h3>Notificaciones Push</h3>
      <label>
        <input
          type="checkbox"
          checked={enabled}
          onChange={handleToggle}
        />
        Recibir notificaciones de pedidos
      </label>
      <p className="help-text">
        Te notificaremos cuando tu pago sea confirmado y cuando tu pedido cambie de estado.
      </p>
    </div>
  );
}
```

---

## 🔐 Seguridad y HTTPS

### Desarrollo Local

**Opción 1: Usar HTTPS local (Recomendado)**

```bash
# Con mkcert (más fácil)
brew install mkcert  # macOS
# o instalar desde: https://github.com/FiloSottile/mkcert

mkcert -install
mkcert localhost 127.0.0.1 ::1

# En Vite (vite.config.ts)
export default defineConfig({
  server: {
    https: {
      key: fs.readFileSync('./localhost-key.pem'),
      cert: fs.readFileSync('./localhost.pem'),
    },
    port: 5173
  }
})
```

**Opción 2: ngrok (para testing)**

```bash
ngrok http 8000  # Para Django
ngrok http 5173  # Para Vite
```

### Producción

Las notificaciones push **SOLO funcionan con HTTPS**. Opciones:

1. **Vercel (Frontend)** - Ya tiene HTTPS automático ✅
2. **Django en EC2 con nginx + Let's Encrypt:**

```nginx
# /etc/nginx/sites-available/smartsales365
server {
    listen 80;
    server_name api.tudominio.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.tudominio.com;
    
    ssl_certificate /etc/letsencrypt/live/api.tudominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.tudominio.com/privkey.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# Instalar certificado
sudo certbot --nginx -d api.tudominio.com
```

---

## 📡 Endpoints API

### 1. Obtener clave pública VAPID
```http
GET /api/notificaciones/vapid-public-key/
```

**Response:**
```json
{
  "public_key": "BEl62iUYgUivxIkv69yViEuiBIa..."
}
```

### 2. Suscribirse
```http
POST /api/notificaciones/subscriptions/
Authorization: Token <tu_token>
Content-Type: application/json

{
  "endpoint": "https://fcm.googleapis.com/fcm/send/...",
  "p256dh": "base64_encoded_key",
  "auth": "base64_encoded_auth",
  "user_agent": "Mozilla/5.0..."
}
```

### 3. Ver mis suscripciones
```http
GET /api/notificaciones/subscriptions/
Authorization: Token <tu_token>
```

### 4. Desactivar suscripción
```http
POST /api/notificaciones/subscriptions/{id}/desactivar/
Authorization: Token <tu_token>
```

### 5. Ver historial de notificaciones
```http
GET /api/notificaciones/historial/
Authorization: Token <tu_token>
```

---

## 🧪 Testing

### 1. Probar desde Django Admin

```bash
python manage.py shell
```

```python
from notificaciones.push_service import push_service
from usuarios.models import Usuario
from compra.models import Compra

# Obtener usuario
usuario = Usuario.objects.first()

# Enviar notificación de prueba
push_service.send_notification(
    usuario=usuario,
    titulo='🧪 Notificación de Prueba',
    mensaje='Si ves esto, ¡las notificaciones funcionan!',
    tipo='otro',
    url='/test'
)
```

### 2. Probar flujo completo

1. **Frontend:** Suscribirse a notificaciones
2. **Backend:** Crear una compra (checkout)
3. **Verificar:** Deberías recibir notificación de carrito confirmado
4. **Backend:** Marcar como pagada
5. **Verificar:** Deberías recibir notificación de pago exitoso

---

## 🐛 Troubleshooting

### "Push notifications no soportadas"
- **Causa:** Navegador viejo o HTTPS no configurado
- **Solución:** Usar Chrome/Firefox moderno + HTTPS

### "Permiso de notificaciones denegado"
- **Causa:** Usuario rechazó el permiso
- **Solución:** Instruir al usuario a habilitar en configuración del navegador

### "Service Worker no se registra"
- **Causa:** Archivo `sw.js` no está en `/public`
- **Solución:** Verificar ruta y que el servidor lo sirva

### "Error 410 Gone" en logs
- **Causa:** Suscripción expiró o fue desinstalada
- **Solución:** El backend automáticamente la desactiva

### "VAPID keys no configuradas"
- **Causa:** No corriste `generate_vapid_keys` o no están en `.env`
- **Solución:** Seguir pasos de configuración

---

## ✅ Checklist de Implementación

### Backend
- [x] Instalar dependencias (`py-vapid`, `pywebpush`)
- [x] Agregar app `notificaciones` a `INSTALLED_APPS`
- [x] Generar claves VAPID
- [x] Configurar variables en `.env`
- [x] Ejecutar migraciones
- [x] Integrar con flujo de compra

### Frontend
- [ ] Crear `public/sw.js`
- [ ] Crear `src/utils/pushNotifications.ts`
- [ ] Registrar Service Worker al login
- [ ] Solicitar permiso de notificaciones
- [ ] Probar en HTTPS (local o ngrok)

### Producción
- [ ] Configurar HTTPS en backend (nginx + Let's Encrypt)
- [ ] Verificar CORS permite tu dominio
- [ ] Generar nuevas claves VAPID para producción
- [ ] Probar flujo completo en producción

---

## 📚 Referencias

- [Web Push API (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Push_API)
- [Service Workers (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [VAPID Specification](https://datatracker.ietf.org/doc/html/rfc8292)
- [pywebpush Documentation](https://github.com/web-push-libs/pywebpush)

