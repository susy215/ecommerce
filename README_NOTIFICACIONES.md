# 📱 Notificaciones Push - Implementación Completa

## 🎯 Resumen

Se implementó un sistema completo de **notificaciones push web** usando Web Push API (estándar W3C) sin dependencias externas como Firebase.

### Casos de Uso Implementados

1. **🎉 Compra Exitosa** - Cuando el pago se confirma
2. **📦 Cambio de Estado** - Cuando el pedido cambia de estado

---

## 📦 Archivos Creados

### Backend
```
notificaciones/
├── __init__.py
├── apps.py
├── models.py                    # PushSubscription, NotificacionEnviada
├── serializers.py               # Serializers REST
├── views.py                     # ViewSets y endpoints
├── urls.py                      # Rutas API
├── admin.py                     # Django Admin
├── tests.py
├── push_service.py              # ⭐ Servicio principal de push
└── management/
    └── commands/
        └── generate_vapid_keys.py  # ⭐ Generar claves VAPID
```

### Documentación
```
docs/
└── NOTIFICACIONES_PUSH.md       # 📚 Guía completa con código frontend

.env.example                      # Variables de entorno actualizadas
NOTIFICACIONES_SETUP.md          # 🚀 Guía de setup rápido
README_NOTIFICACIONES.md         # Este archivo
```

---

## 🔧 Modificaciones en Código Existente

### 1. `requirements.txt`
```diff
+ py-vapid==1.9.1
+ pywebpush==1.14.1
```

### 2. `core/settings.py`
```python
INSTALLED_APPS = [
    # ...
+   'notificaciones',
]

# Notificaciones Push (VAPID - Web Push)
VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY', '')
VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY', '')
VAPID_CLAIMS = {
    "sub": f"mailto:{os.environ.get('VAPID_ADMIN_EMAIL', 'admin@smartsales365.com')}"
}
```

### 3. `core/urls.py`
```python
urlpatterns = [
    # ...
+   path('api/notificaciones/', include('notificaciones.urls')),
]
```

### 4. `compra/views.py`
Integrado en 3 lugares:

**a) Después del checkout (línea ~192)**
```python
# ✅ Enviar notificación push de compra creada
try:
    from notificaciones.push_service import push_service
    push_service.send_notification(
        usuario=user,
        titulo='🛒 Carrito confirmado',
        mensaje=f'Tu pedido #{compra.id} ha sido creado...',
        tipo='otro',
        datos_extra={'compra_id': compra.id, 'total': float(compra.total)},
        url=f'/mis-pedidos/{compra.id}'
    )
except Exception as e:
    logger.warning(f'No se pudo enviar notificación push: {str(e)}')
```

**b) Al marcar como pagada (línea ~263)**
```python
# ✅ Enviar notificación push de pago confirmado
try:
    from notificaciones.push_service import push_service
    push_service.send_compra_exitosa(compra)
except Exception as e:
    logger.warning(f'No se pudo enviar notificación push: {str(e)}')
```

**c) En webhook de Stripe (línea ~413)**
```python
# ✅ Enviar notificación push de pago confirmado vía Stripe
try:
    from notificaciones.push_service import push_service
    push_service.send_compra_exitosa(compra)
except Exception as e:
    logger.warning(f'No se pudo enviar notificación push: {str(e)}')
```

---

## 🚀 Inicio Rápido

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Generar claves VAPID
```bash
python manage.py generate_vapid_keys --email admin@tudominio.com
```

Copiar output a `.env`:
```env
VAPID_PRIVATE_KEY=abc123...
VAPID_PUBLIC_KEY=xyz789...
VAPID_ADMIN_EMAIL=admin@tudominio.com
```

### 3. Migrar base de datos
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Iniciar servidor
```bash
python manage.py runserver
```

---

## 📡 Endpoints API Disponibles

| Endpoint | Método | Auth | Descripción |
|----------|--------|------|-------------|
| `/api/notificaciones/vapid-public-key/` | GET | No | Obtener clave pública VAPID |
| `/api/notificaciones/subscriptions/` | GET | Sí | Listar mis suscripciones |
| `/api/notificaciones/subscriptions/` | POST | Sí | Crear nueva suscripción |
| `/api/notificaciones/subscriptions/{id}/` | GET | Sí | Detalle de suscripción |
| `/api/notificaciones/subscriptions/{id}/desactivar/` | POST | Sí | Desactivar suscripción |
| `/api/notificaciones/subscriptions/{id}/activar/` | POST | Sí | Activar suscripción |
| `/api/notificaciones/historial/` | GET | Sí | Ver historial de notificaciones |

Ver documentación completa en: **http://localhost:8000/api/docs/**

---

## 💻 Frontend (React + Vite)

### Archivos a Crear

1. **`public/sw.js`** - Service Worker para capturar notificaciones
2. **`src/utils/pushNotifications.ts`** - Utilidad de suscripción
3. Integrar en `App.tsx` al hacer login

### Código de Ejemplo

Ver `docs/NOTIFICACIONES_PUSH.md` para código completo copy-paste.

### HTTPS Requerido

```bash
# Opción 1: mkcert (Local)
brew install mkcert
mkcert -install
mkcert localhost 127.0.0.1

# Opción 2: ngrok (Testing)
ngrok http 5173
```

---

## 🔐 Seguridad

### Desarrollo Local
- ✅ Usa HTTPS (mkcert o ngrok)
- ✅ Claves VAPID de desarrollo en `.env`
- ✅ CORS configurado para `localhost`

### Producción
- ⚠️ **IMPORTANTE:** Generar nuevas claves VAPID
- ✅ Backend con nginx + Let's Encrypt
- ✅ Frontend en Vercel (HTTPS automático)
- ✅ Configurar CORS para dominio real

---

## 🧪 Testing

### Desde Django Shell
```python
python manage.py shell
```

```python
from notificaciones.push_service import push_service
from usuarios.models import Usuario

usuario = Usuario.objects.first()
resultado = push_service.send_notification(
    usuario=usuario,
    titulo='🧪 Test',
    mensaje='¡Funciona!',
    tipo='otro',
    url='/test'
)
print(resultado)
```

### Flujo Completo
1. Login en frontend → Se suscribe automáticamente
2. Hacer checkout → Recibe notificación
3. Confirmar pago → Recibe notificación
4. Verificar en Admin Django

---

## 📊 Django Admin

Acceder a: **http://localhost:8000/admin/**

### Sección "Notificaciones Push"
- **Suscripciones Push** - Ver/gestionar suscripciones de usuarios
- **Notificaciones Enviadas** - Historial completo con estados

Filtros disponibles:
- Por usuario
- Por tipo de notificación
- Por estado (exitoso/fallido)
- Por fecha

---

## 🐛 Troubleshooting

| Problema | Solución |
|----------|----------|
| "VAPID keys no configuradas" | Ejecutar `generate_vapid_keys` |
| "Push notifications no soportadas" | Usar HTTPS + navegador moderno |
| "Service Worker no se registra" | Verificar `sw.js` en `/public` |
| "Error 410 Gone" | Suscripción expiró (se desactiva automáticamente) |
| "Permiso denegado" | Usuario rechazó, habilitar en configuración del navegador |

---

## 📚 Recursos Adicionales

- **Documentación Completa:** `docs/NOTIFICACIONES_PUSH.md`
- **Setup Rápido:** `NOTIFICACIONES_SETUP.md`
- **API Docs:** http://localhost:8000/api/docs/
- **Swagger JSON:** http://localhost:8000/api/schema/

---

## ✅ Lo que Ya Funciona

### Backend ✅
- [x] Modelos de suscripción y historial
- [x] Servicio de envío de notificaciones
- [x] Integración en flujo de compra
- [x] Endpoints REST completos
- [x] Django Admin configurado
- [x] Management command para VAPID keys
- [x] Manejo automático de suscripciones expiradas
- [x] Logging y error handling

### Por Implementar (Frontend)
- [ ] Service Worker (`sw.js`)
- [ ] Utilidad de suscripción
- [ ] Integración en componente de login
- [ ] UI para gestión de notificaciones

---

## 🎯 Características

- ✅ **Sin dependencias externas** (no Firebase, no OneSignal)
- ✅ **Web Push API estándar** (funciona en todos los navegadores modernos)
- ✅ **Encriptación end-to-end** (VAPID)
- ✅ **Multi-dispositivo** (cada usuario puede tener múltiples suscripciones)
- ✅ **Gestión automática** (desactiva suscripciones expiradas)
- ✅ **Historial completo** (auditoría y debugging)
- ✅ **Try-catch en todas las integraciones** (no afecta flujo principal si falla)

---

## 🚀 Próximos Pasos

1. **Implementar frontend** siguiendo `docs/NOTIFICACIONES_PUSH.md`
2. **Configurar HTTPS local** (mkcert recomendado)
3. **Probar flujo completo** (suscripción → compra → notificación)
4. **Para producción:**
   - Configurar nginx + Let's Encrypt en EC2
   - Generar nuevas claves VAPID
   - Configurar CORS para dominio real
   - Probar en ambiente de staging

---

**¿Necesitas ayuda?** Revisa `docs/NOTIFICACIONES_PUSH.md` para código completo del frontend y solución de problemas comunes.

