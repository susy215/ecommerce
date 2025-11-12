# 🔔 Notificaciones para Admin Web - Documentación Frontend

## 📋 **RESUMEN EJECUTIVO**

Este documento explica cómo integrar **notificaciones para administradores** en tu aplicación React/Vite. Similar a tus push notifications PWA, pero para el panel de administración web.

## 🎯 **LO QUE LOGRARÁS**

- ✅ **Notificaciones cada 30 segundos** (polling simple)
- ✅ **Mismo sistema de push** que tu PWA
- ✅ **Badge en tiempo real** con conteo de notificaciones no leídas
- ✅ **Lista de notificaciones** actualizada automáticamente
- ✅ **Sonido opcional** para alertas importantes
- ✅ **Sin configuración compleja** de WebSocket

## 🔧 **PRERREQUISITOS**

### Backend Configurado
- ✅ **Django REST Framework** instalado
- ✅ **Notificaciones admin** ya funcionando (envían automáticamente)
- ✅ **Endpoint de polling** creado (`/api/notificaciones/admin/polling/`)

### Frontend Dependencias
```bash
# Ninguna adicional - usa fetch() nativo
```

## 🌐 **URL DE LA API**

```javascript
// Endpoint para polling de notificaciones
const API_URL = '/api/notificaciones/admin/polling/';

// Endpoint para marcar como leída
const MARK_READ_URL = (id) => `/api/notificaciones/admin/${id}/`;
```

## 🔐 **AUTENTICACIÓN**

Usa **Bearer token** en headers (igual que tus otras APIs):

```javascript
// Headers de autenticación
const headers = {
  'Authorization': `Bearer ${localStorage.getItem('token')}`,
  'Content-Type': 'application/json',
};
```

## 📝 **IMPLEMENTACIÓN COMPLETA**

### **Hook personalizado: `useAdminNotificationsPolling.js`**

```javascript
/**
 * Hook simple para notificaciones de admin usando polling HTTP.
 * Similar a las push notifications PWA pero para web admin.
 *
 * Ventajas:
 * - ✅ Muy simple de implementar
 * - ✅ Usa tu backend actual
 * - ✅ No requiere configuración compleja
 * - ✅ Funciona igual que las push notifications
 */

import { useState, useEffect, useCallback } from 'react';

export const useAdminNotificationsPolling = () => {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [lastChecked, setLastChecked] = useState(null);
  const [error, setError] = useState(null);

  // Obtener headers de autenticación
  const getAuthHeaders = useCallback(() => {
    const token = localStorage.getItem('token') || localStorage.getItem('auth_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  }, []);

  // Verificar nuevas notificaciones
  const checkNotifications = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch('/api/notificaciones/admin/polling/', {
        method: 'GET',
        headers: getAuthHeaders(),
      });

      if (response.ok) {
        const data = await response.json();

        // Si hay nuevas notificaciones (comparar con las existentes)
        const currentIds = new Set(notifications.map(n => n.id));
        const newNotifications = data.notifications.filter(n => !currentIds.has(n.id));

        // Mostrar notificaciones push para las nuevas (igual que PWA)
        if (newNotifications.length > 0 && 'Notification' in window) {
          // Pedir permiso si no está concedido
          if (Notification.permission === 'default') {
            await Notification.requestPermission();
          }

          // Mostrar notificaciones si está permitido
          if (Notification.permission === 'granted') {
            newNotifications.forEach(notification => {
              new Notification(notification.titulo, {
                body: notification.mensaje,
                icon: '/admin-icon.png',
                badge: '/badge-72x72.png',
                tag: `admin-${notification.id}`, // Evita duplicados
                data: notification.datos,
              });
            });

            // Reproducir sonido opcional
            playNotificationSound();
          }
        }

        // Actualizar estado
        setNotifications(data.notifications);
        setUnreadCount(data.unread_count);
        setLastChecked(new Date());

      } else if (response.status === 401) {
        setError('No autorizado - verifica tu sesión');
      } else if (response.status === 403) {
        setError('No tienes permisos de administrador');
      } else {
        setError(`Error del servidor: ${response.status}`);
      }

    } catch (error) {
      console.error('Error checking notifications:', error);
      setError('Error de conexión');
    } finally {
      setIsLoading(false);
    }
  }, [notifications, getAuthHeaders]);

  // Función para reproducir sonido
  const playNotificationSound = useCallback(() => {
    try {
      const audio = new Audio('/notification-sound.mp3');
      audio.volume = 0.3; // Más bajo que las push notifications
      audio.play().catch(e => {
        console.log('Sonido no disponible:', e.message);
      });
    } catch (e) {
      console.log('Sonido no soportado');
    }
  }, []);

  // Marcar notificación como leída
  const markAsRead = useCallback(async (notificationId) => {
    try {
      const response = await fetch(`/api/notificaciones/admin/${notificationId}/`, {
        method: 'PATCH',
        headers: getAuthHeaders(),
        body: JSON.stringify({ leida: true }),
      });

      if (response.ok) {
        // Actualizar estado local
        setNotifications(prev =>
          prev.map(notif =>
            notif.id === notificationId
              ? { ...notif, leida: true }
              : notif
          )
        );
        setUnreadCount(prev => Math.max(0, prev - 1));
      }
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  }, [getAuthHeaders]);

  // Marcar todas como leídas
  const markAllAsRead = useCallback(async () => {
    try {
      // Actualizar todas las notificaciones como leídas
      const unreadNotifications = notifications.filter(n => !n.leida);

      for (const notification of unreadNotifications) {
        await fetch(`/api/notificaciones/admin/${notification.id}/`, {
          method: 'PATCH',
          headers: getAuthHeaders(),
          body: JSON.stringify({ leida: true }),
        });
      }

      // Actualizar estado local
      setNotifications(prev =>
        prev.map(notif => ({ ...notif, leida: true }))
      );
      setUnreadCount(0);

    } catch (error) {
      console.error('Error marking all as read:', error);
    }
  }, [notifications, getAuthHeaders]);

  // Efectos
  useEffect(() => {
    // Verificar inmediatamente al montar
    checkNotifications();

    // Luego cada 30 segundos
    const interval = setInterval(checkNotifications, 30000); // 30 segundos

    return () => clearInterval(interval);
  }, [checkNotifications]);

  // Limpiar error después de 5 segundos
  useEffect(() => {
    if (error) {
      const timeout = setTimeout(() => setError(null), 5000);
      return () => clearTimeout(timeout);
    }
  }, [error]);

  return {
    notifications,
    unreadCount,
    isLoading,
    lastChecked,
    error,
    markAsRead,
    markAllAsRead,
    refresh: checkNotifications,
  };
};
```

## 🎨 **USO EN COMPONENTES REACT**

### **Componente de Notificaciones:**

```javascript
import React from 'react';
import { useAdminNotifications } from './hooks/useAdminNotifications';

const NotificationCenter = () => {
  const {
    notifications,
    unreadCount,
    isConnected,
    connectionStatus,
    markAsRead
  } = useAdminNotifications();

  return (
    <div className="notification-center">
      {/* Badge de notificaciones */}
      <div className="notification-badge">
        <span>Notificaciones</span>
        {unreadCount > 0 && (
          <span className="badge">{unreadCount}</span>
        )}
      </div>

      {/* Estado de conexión */}
      <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
        {connectionStatus}
      </div>

      {/* Lista de notificaciones */}
      <div className="notification-list">
        {notifications.map(notification => (
          <div
            key={notification.id}
            className={`notification ${notification.leida ? 'read' : 'unread'}`}
            onClick={() => markAsRead(notification.id)}
          >
            <h4>{notification.titulo}</h4>
            <p>{notification.mensaje}</p>
            <small>{new Date(notification.creada).toLocaleString()}</small>
          </div>
        ))}
      </div>
    </div>
  );
};

export default NotificationCenter;
```

## 📊 **TIPOS DE NOTIFICACIONES**

### **Estructura de una notificación:**

```javascript
{
  id: 123,
  tipo: "nueva_compra", // nueva_compra, nuevo_pago, nueva_promocion
  titulo: "🛒 Nueva Compra Realizada",
  mensaje: "Juan Pérez realizó una compra de $899.99",
  url: "/admin/ventas/123",
  datos: { compra_id: 123, cliente_id: 456 },
  creada: "2025-11-12T22:30:00Z",
  leida: false
}
```

### **Tipos de notificaciones:**
- `nueva_compra` - Cuando un cliente realiza una compra
- `nuevo_pago` - Cuando se confirma un pago
- `nueva_promocion` - Cuando se crea una promoción activa

## 🔧 **MANEJO DE ERRORES**

### **Conexión fallida:**
```javascript
// El hook se reconecta automáticamente
// Muestra el estado al usuario
{connectionStatus === 'Desconectado' && (
  <div className="warning">
    Conexión perdida - reconectando...
  </div>
)}
```

### **Sin token JWT:**
```javascript
// El hook muestra warning en consola
// Asegúrate de que el usuario esté logueado antes de usar el hook
```

## 🎵 **SONIDO DE NOTIFICACIONES**

Agrega un archivo de sonido en `public/notification-sound.mp3` o modifica la función `playNotificationSound()` para usar la Web Audio API.

## 🧪 **PRUEBAS**

### **Verificar conexión:**
```javascript
// En la consola del navegador
const { debugWebSocket } = useAdminNotifications();
debugWebSocket(); // Muestra estado detallado
```

### **Simular notificación:**
```javascript
// El backend enviará notificaciones automáticamente
// cuando ocurran eventos reales (compras, pagos)
```

## 🚀 **DEPLOYMENT**

1. **Asegúrate** de que el backend tenga Nginx configurado para WebSocket
2. **Deploy** el código frontend con el hook `useAdminNotifications`
3. **Verifica** que las notificaciones lleguen en tiempo real

## 📞 **SOPORTE**

Si tienes problemas:
1. Verifica que el token JWT sea válido
2. Confirma que el backend tenga Daphne corriendo
3. Revisa los logs del backend para errores
4. Usa la función `debugWebSocket()` para diagnóstico

¡Las notificaciones WebSocket están listas para usar! 🎉

## 🌐 **CONEXIÓN WEBSOCKET**

### URL del WebSocket
```
ws://tu-dominio.com/ws/admin/notifications/
// O para HTTPS:
wss://tu-dominio.com/ws/admin/notifications/
```

### Autenticación
Las conexiones requieren autenticación JWT en el header de upgrade HTTP.

## 📝 **IMPLEMENTACIÓN EN REACT**

### 1. **Hook personalizado para notificaciones**

```javascript
// hooks/useAdminNotifications.js
import { useState, useEffect, useRef, useCallback } from 'react';
import ReconnectingWebSocket from 'reconnecting-websocket';

const WS_URL = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/admin/notifications/`;

export const useAdminNotifications = () => {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('Desconectado');
  const ws = useRef(null);

  // Conectar WebSocket
  const connect = useCallback(() => {
    if (ws.current) {
      ws.current.close();
    }

    ws.current = new ReconnectingWebSocket(WS_URL, [], {
      maxReconnectionDelay: 10000,
      minReconnectionDelay: 1000,
      reconnectionDelayGrowFactor: 1.3,
      maxRetries: Infinity,
      debug: false,
    });

    ws.current.onopen = () => {
      console.log('✅ WebSocket conectado');
      setIsConnected(true);
      setConnectionStatus('Conectado');
    };

    ws.current.onclose = () => {
      console.log('❌ WebSocket desconectado');
      setIsConnected(false);
      setConnectionStatus('Desconectado');
    };

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnectionStatus('Error de conexión');
    };

    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleMessage(data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
  }, []);

  // Manejar mensajes del WebSocket
  const handleMessage = useCallback((data) => {
    switch (data.type) {
      case 'connection_established':
        console.log('Conexión establecida:', data.message);
        setConnectionStatus('Conectado');
        break;

      case 'notification':
        // Nueva notificación recibida
        const newNotification = {
          id: data.id,
          tipo: data.tipo,
          titulo: data.titulo,
          mensaje: data.mensaje,
          url: data.url,
          datos: data.datos,
          creada: data.creada,
          leida: false, // Las nuevas notificaciones no están leídas
        };

        setNotifications(prev => [newNotification, ...prev]);
        setUnreadCount(prev => prev + 1);

        // Mostrar notificación del navegador si es soportado
        if ('Notification' in window && Notification.permission === 'granted') {
          new Notification(data.titulo, {
            body: data.mensaje,
            icon: '/icon-192x192.png',
            badge: '/badge-72x72.png',
            data: data.datos,
          });
        }
        break;

      case 'unread_count':
        setUnreadCount(data.count);
        break;

      case 'pong':
        // Respuesta a ping - conexión viva
        break;

      case 'error':
        console.error('WebSocket error:', data.message);
        break;

      default:
        console.log('Mensaje WebSocket desconocido:', data);
    }
  }, []);

  // Enviar ping para mantener conexión viva
  const sendPing = useCallback(() => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: 'ping' }));
    }
  }, []);

  // Marcar notificación como leída
  const markAsRead = useCallback((notificationId) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        type: 'mark_read',
        notification_id: notificationId,
      }));

      // Actualizar estado local
      setNotifications(prev =>
        prev.map(notif =>
          notif.id === notificationId
            ? { ...notif, leida: true }
            : notif
        )
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    }
  }, []);

  // Obtener conteo de no leídas
  const getUnreadCount = useCallback(() => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: 'get_unread_count' }));
    }
  }, []);

  // Limpiar conexión
  const disconnect = useCallback(() => {
    if (ws.current) {
      ws.current.close();
      ws.current = null;
    }
    setIsConnected(false);
    setConnectionStatus('Desconectado');
  }, []);

  // Efectos
  useEffect(() => {
    connect();

    // Ping cada 30 segundos para mantener conexión viva
    const pingInterval = setInterval(sendPing, 30000);

    return () => {
      clearInterval(pingInterval);
      disconnect();
    };
  }, [connect, sendPing, disconnect]);

  // Solicitar permisos de notificación al montar
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  return {
    notifications,
    unreadCount,
    isConnected,
    connectionStatus,
    markAsRead,
    getUnreadCount,
    sendPing,
    reconnect: connect,
  };
};
```

### 2. **Componente de notificaciones**

```javascript
// components/AdminNotifications.jsx
import React, { useState } from 'react';
import { useAdminNotifications } from '../hooks/useAdminNotifications';

const AdminNotifications = () => {
  const {
    notifications,
    unreadCount,
    isConnected,
    connectionStatus,
    markAsRead,
  } = useAdminNotifications();

  const [showDropdown, setShowDropdown] = useState(false);

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  const getNotificationIcon = (tipo) => {
    switch (tipo) {
      case 'nueva_compra':
        return '🛒';
      case 'pago_confirmado':
        return '💰';
      case 'promocion':
        return '🎉';
      default:
        return '📢';
    }
  };

  return (
    <div className="notifications-container">
      {/* Botón de notificaciones */}
      <button
        className="notification-button"
        onClick={() => setShowDropdown(!showDropdown)}
      >
        <span className="bell-icon">🔔</span>
        {unreadCount > 0 && (
          <span className="unread-badge">{unreadCount}</span>
        )}
      </button>

      {/* Estado de conexión */}
      <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
        {connectionStatus}
      </div>

      {/* Dropdown de notificaciones */}
      {showDropdown && (
        <div className="notifications-dropdown">
          <div className="dropdown-header">
            <h3>Notificaciones</h3>
            {unreadCount > 0 && (
              <span className="unread-text">{unreadCount} sin leer</span>
            )}
          </div>

          <div className="notifications-list">
            {notifications.length === 0 ? (
              <div className="empty-state">
                No hay notificaciones
              </div>
            ) : (
              notifications.map((notif) => (
                <div
                  key={notif.id}
                  className={`notification-item ${!notif.leida ? 'unread' : ''}`}
                  onClick={() => {
                    if (!notif.leida) {
                      markAsRead(notif.id);
                    }
                    if (notif.url) {
                      window.open(notif.url, '_blank');
                    }
                  }}
                >
                  <div className="notification-icon">
                    {getNotificationIcon(notif.tipo)}
                  </div>

                  <div className="notification-content">
                    <div className="notification-title">
                      {notif.titulo}
                    </div>
                    <div className="notification-message">
                      {notif.mensaje}
                    </div>
                    <div className="notification-time">
                      {formatTimestamp(notif.creada)}
                    </div>
                  </div>

                  {!notif.leida && (
                    <div className="unread-indicator"></div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminNotifications;
```

### 3. **Estilos CSS**

```css
/* styles/notifications.css */
.notifications-container {
  position: relative;
  display: inline-block;
}

.notification-button {
  background: none;
  border: none;
  cursor: pointer;
  position: relative;
  padding: 8px;
  border-radius: 50%;
  transition: background-color 0.2s;
}

.notification-button:hover {
  background-color: rgba(0, 0, 0, 0.1);
}

.bell-icon {
  font-size: 20px;
}

.unread-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  background: #ff4444;
  color: white;
  border-radius: 50%;
  padding: 2px 6px;
  font-size: 12px;
  font-weight: bold;
  min-width: 18px;
  text-align: center;
}

.connection-status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 12px;
  margin-top: 4px;
}

.connection-status.connected {
  background: #4CAF50;
  color: white;
}

.connection-status.disconnected {
  background: #f44336;
  color: white;
}

.notifications-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  width: 400px;
  max-height: 500px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  overflow: hidden;
}

.dropdown-header {
  padding: 16px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dropdown-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.unread-text {
  color: #ff4444;
  font-size: 14px;
}

.notifications-list {
  max-height: 400px;
  overflow-y: auto;
}

.notification-item {
  padding: 12px 16px;
  border-bottom: 1px solid #f5f5f5;
  cursor: pointer;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  transition: background-color 0.2s;
}

.notification-item:hover {
  background-color: #f8f9fa;
}

.notification-item.unread {
  background-color: #fff3cd;
}

.notification-item.unread:hover {
  background-color: #ffeaa7;
}

.notification-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-weight: 600;
  font-size: 14px;
  color: #333;
  margin-bottom: 4px;
}

.notification-message {
  font-size: 13px;
  color: #666;
  line-height: 1.4;
  margin-bottom: 4px;
}

.notification-time {
  font-size: 12px;
  color: #999;
}

.unread-indicator {
  width: 8px;
  height: 8px;
  background: #ff4444;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 6px;
}

.empty-state {
  padding: 40px 16px;
  text-align: center;
  color: #999;
  font-style: italic;
}

/* Responsive */
@media (max-width: 480px) {
  .notifications-dropdown {
    width: calc(100vw - 32px);
    max-width: 400px;
  }
}
```

### 4. **Integración en App principal**

```javascript
// App.jsx o main layout
import React from 'react';
import AdminNotifications from './components/AdminNotifications';

function App() {
  return (
    <div className="App">
      {/* Header con notificaciones */}
      <header>
        <AdminNotifications />
      </header>

      {/* Resto de la aplicación */}
      <main>
        {/* Tu contenido */}
      </main>
    </div>
  );
}

export default App;
```

## 📡 **TIPOS DE NOTIFICACIONES**

### Notificaciones de Compras
```javascript
{
  type: 'notification',
  id: 123,
  tipo: 'nueva_compra',
  titulo: '🛒 Nueva Compra Realizada',
  mensaje: 'Juan Pérez realizó una compra por $899.99',
  url: '/admin/compras/123/',
  datos: {
    compra_id: 123,
    cliente_id: 456,
    monto: 899.99
  },
  creada: '2025-11-12T20:30:00Z'
}
```

### Notificaciones de Pagos
```javascript
{
  type: 'notification',
  id: 124,
  tipo: 'pago_confirmado',
  titulo: '💰 Pago Confirmado',
  mensaje: 'Pago de $1799.98 confirmado para compra #1629',
  url: '/admin/pagos/1629/',
  datos: {
    compra_id: 1629,
    payment_intent: 'pi_3SSl1eRslCCSa79r10xQ0I16',
    monto: 1799.98
  },
  creada: '2025-11-12T20:52:24Z'
}
```

## 🔧 **TROUBLESHOOTING**

### Problema: "WebSocket connection failed"
**Solución:** Verificar que el usuario esté autenticado y tenga rol 'admin' o 'vendedor'.

### Problema: Notificaciones no llegan
**Solución:** Verificar logs del backend:
```bash
sudo journalctl -u smartsales365 -n 20 | grep "notific"
```

### Problema: Reconexión automática no funciona
**Solución:** Asegurarse de que `reconnecting-websocket` esté correctamente configurado.

## 📱 **COMPATIBILIDAD**

- ✅ Chrome 16+
- ✅ Firefox 11+
- ✅ Safari 6+
- ✅ Edge 12+
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

## 🔒 **SEGURIDAD**

- Conexiones requieren autenticación JWT
- Solo usuarios con rol 'admin' o 'vendedor'
- Validación de permisos en el backend
- Sanitización de datos WebSocket

---

## 📞 **SOPORTE**

Si tienes problemas con las notificaciones, revisa:
1. Logs del backend
2. Consola del navegador (F12 → Console)
3. Estado de conexión WebSocket
4. Permisos de Notification API
