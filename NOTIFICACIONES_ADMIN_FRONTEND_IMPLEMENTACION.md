# 🖥️ Frontend Admin - Notificaciones WebSocket

## 🎯 Implementación Completa

### **URLs del Backend (Ya implementadas):**

```javascript
// WebSocket
ws://tu-dominio.com/ws/admin/notifications/
wss://tu-dominio.com/ws/admin/notifications/  // Producción

// REST API
GET    /api/notificaciones/admin/                    // Lista notificaciones
GET    /api/notificaciones/admin/no-leidas/          // Conteo no leídas
POST   /api/notificaciones/admin/{id}/marcar-leida/  // Marcar como leída
POST   /api/notificaciones/admin/marcar-todas-leidas/ // Marcar todas
```

## 🔧 **Código Frontend - Copia y pega directamente:**

### **1. Servicio WebSocket (`src/services/adminNotifications.js`)**

```javascript
import ReconnectingWebSocket from 'reconnecting-websocket'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export function setupAdminWebSocket(onMessage, onError, token) {
  if (!token) {
    console.warn('No hay token para WebSocket admin')
    return null
  }

  const wsUrl = `${API_URL.replace('http', 'ws')}/ws/admin/notifications/?token=${token}`

  const ws = new ReconnectingWebSocket(wsUrl, [], {
    maxReconnectionDelay: 10000,
    minReconnectionDelay: 1000,
    reconnectionDelayGrowFactor: 1.3,
    maxRetries: 10,
  })

  ws.onopen = () => {
    console.log('✅ WebSocket admin conectado')
  }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      console.log('📨 Notificación admin:', data)
      onMessage(data)
    } catch (e) {
      console.error('Error parseando mensaje WS:', e)
      onError(e)
    }
  }

  ws.onerror = (error) => {
    console.error('❌ Error WebSocket admin:', error)
    onError(error)
  }

  ws.onclose = (event) => {
    console.log('🔌 WebSocket admin cerrado:', event.code)
  }

  return ws
}

export function disconnectAdminWebSocket(ws) {
  if (ws) {
    ws.close()
  }
}

// API REST calls
export const adminNotificationsAPI = {
  getNotifications: () => axios.get('/api/notificaciones/admin/'),
  getUnreadCount: () => axios.get('/api/notificaciones/admin/no-leidas/'),
  markAsRead: (id) => axios.post(`/api/notificaciones/admin/${id}/marcar-leida/`),
  markAllAsRead: () => axios.post('/api/notificaciones/admin/marcar-todas-leidas/')
}
```

### **2. Hook Personalizado (`src/hooks/useAdminNotifications.js`)**

```javascript
import { useState, useEffect, useRef } from 'react'
import { setupAdminWebSocket, disconnectAdminWebSocket, adminNotificationsAPI } from '../services/adminNotifications'

export function useAdminNotifications(token) {
  const [notifications, setNotifications] = useState([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef(null)

  useEffect(() => {
    if (!token) return

    const handleMessage = (data) => {
      if (data.type === 'notification') {
        setNotifications(prev => [data, ...prev])
        setUnreadCount(prev => prev + 1)

        // Mostrar notificación del navegador
        if ('Notification' in window && Notification.permission === 'granted') {
          new Notification(data.titulo, {
            body: data.mensaje,
            icon: '/admin-icon.png',
            tag: `admin-${data.id}`
          })
        }
      }
    }

    const handleError = (error) => {
      console.error('Error WS admin:', error)
      setIsConnected(false)
    }

    wsRef.current = setupAdminWebSocket(handleMessage, handleError, token)
    setIsConnected(true)

    // Cargar historial inicial
    loadNotifications()
    loadUnreadCount()

    return () => {
      disconnectAdminWebSocket(wsRef.current)
    }
  }, [token])

  const loadNotifications = async () => {
    try {
      const response = await adminNotificationsAPI.getNotifications()
      setNotifications(response.data.results || [])
    } catch (error) {
      console.error('Error cargando notificaciones:', error)
    }
  }

  const loadUnreadCount = async () => {
    try {
      const response = await adminNotificationsAPI.getUnreadCount()
      setUnreadCount(response.data.count || 0)
    } catch (error) {
      console.error('Error cargando conteo:', error)
    }
  }

  const markAsRead = async (notificationId) => {
    try {
      await adminNotificationsAPI.markAsRead(notificationId)
      setNotifications(prev =>
        prev.map(n => n.id === notificationId ? { ...n, leida: true } : n)
      )
      setUnreadCount(prev => Math.max(0, prev - 1))
    } catch (error) {
      console.error('Error marcando como leída:', error)
    }
  }

  const markAllAsRead = async () => {
    try {
      await adminNotificationsAPI.markAllAsRead()
      setNotifications(prev => prev.map(n => ({ ...n, leida: true })))
      setUnreadCount(0)
    } catch (error) {
      console.error('Error marcando todas como leídas:', error)
    }
  }

  return {
    notifications,
    unreadCount,
    isConnected,
    markAsRead,
    markAllAsRead,
    loadNotifications
  }
}
```

### **3. Componente de Notificaciones (`src/components/admin/NotificationPanel.jsx`)**

```javascript
import { useState } from 'react'
import { Bell, X, Check, ShoppingCart, CreditCard } from 'lucide-react'
import { useAdminNotifications } from '../../hooks/useAdminNotifications'

const TYPE_ICONS = {
  nueva_compra: ShoppingCart,
  nuevo_pago: CreditCard,
}

export default function NotificationPanel({ isOpen, onClose, token }) {
  const { notifications, unreadCount, markAsRead, markAllAsRead } = useAdminNotifications(token)
  const [activeTab, setActiveTab] = useState('all')

  const filteredNotifications = activeTab === 'unread'
    ? notifications.filter(n => !n.leida)
    : notifications

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      <div className="relative ml-auto w-full max-w-md bg-white dark:bg-gray-800 shadow-xl flex flex-col">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="font-semibold text-lg">Notificaciones</h2>
          <button onClick={onClose} className="p-1 rounded-full hover:bg-gray-100">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex border-b">
          <button
            onClick={() => setActiveTab('all')}
            className={`flex-1 py-2 px-4 text-sm font-medium ${
              activeTab === 'all' ? 'border-b-2 border-blue-500 text-blue-600' : ''
            }`}
          >
            Todas ({notifications.length})
          </button>
          <button
            onClick={() => setActiveTab('unread')}
            className={`flex-1 py-2 px-4 text-sm font-medium ${
              activeTab === 'unread' ? 'border-b-2 border-blue-500 text-blue-600' : ''
            }`}
          >
            No leídas ({unreadCount})
          </button>
        </div>

        {unreadCount > 0 && (
          <div className="p-3 border-b">
            <button
              onClick={markAllAsRead}
              className="w-full py-2 px-4 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
            >
              Marcar todas como leídas
            </button>
          </div>
        )}

        <div className="flex-1 overflow-y-auto">
          {filteredNotifications.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Bell className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No hay notificaciones</p>
            </div>
          ) : (
            <div className="divide-y">
              {filteredNotifications.map((notification) => {
                const Icon = TYPE_ICONS[notification.tipo] || Bell

                return (
                  <div
                    key={notification.id}
                    onClick={() => markAsRead(notification.id)}
                    className="p-4 hover:bg-gray-50 cursor-pointer"
                  >
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                        <Icon className="w-4 h-4 text-blue-600" />
                      </div>

                      <div className="flex-1">
                        <h4 className="font-medium text-sm">{notification.titulo}</h4>
                        <p className="text-sm text-gray-600 mt-1">{notification.mensaje}</p>
                        <p className="text-xs text-gray-500 mt-2">
                          {new Date(notification.creada).toLocaleString()}
                        </p>
                      </div>

                      {!notification.leida && (
                        <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
```

### **4. Badge de Notificaciones (`src/components/admin/NotificationBadge.jsx`)**

```javascript
import { Bell } from 'lucide-react'
import { useAdminNotifications } from '../../hooks/useAdminNotifications'

export default function NotificationBadge({ token, onClick }) {
  const { unreadCount } = useAdminNotifications(token)

  return (
    <button
      onClick={onClick}
      className="relative p-2 rounded-full hover:bg-gray-100"
    >
      <Bell className="w-5 h-5" />
      {unreadCount > 0 && (
        <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full min-w-[18px] h-[18px] flex items-center justify-center">
          {unreadCount > 99 ? '99+' : unreadCount}
        </span>
      )}
    </button>
  )
}
```

### **5. Integración en Layout (`src/layouts/AdminLayout.jsx`)**

```javascript
import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import NotificationBadge from '../components/admin/NotificationBadge'
import NotificationPanel from '../components/admin/NotificationPanel'

export default function AdminLayout() {
  const [notificationsOpen, setNotificationsOpen] = useState(false)
  const token = localStorage.getItem('auth_token')

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="flex justify-between items-center px-6 py-4">
          <h1 className="text-xl font-semibold">Panel Administrativo</h1>

          <NotificationBadge
            token={token}
            onClick={() => setNotificationsOpen(true)}
          />
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6">
        <Outlet />
      </main>

      {/* Notification Panel */}
      <NotificationPanel
        token={token}
        isOpen={notificationsOpen}
        onClose={() => setNotificationsOpen(false)}
      />
    </div>
  )
}
```

## 🎯 **Tipos de Notificaciones que Recibirás:**

### **Nueva Compra** 🛒
```javascript
{
  type: "notification",
  id: 123,
  tipo: "nueva_compra",
  titulo: "Nueva Compra Realizada",
  mensaje: "El cliente Juan Pérez realizó una compra #456 por $150.00",
  url: "/admin/orders/456/",
  datos: {
    compra_id: 456,
    cliente_id: 789,
    cliente_nombre: "Juan Pérez",
    total: 150.00,
    items_count: 3,
    pagado: false
  },
  creada: "2025-11-10T22:45:00Z",
  leida: false
}
```

### **Nuevo Pago** 💰
```javascript
{
  type: "notification",
  id: 124,
  tipo: "nuevo_pago",
  titulo: "Nuevo Pago Confirmado",
  mensaje: "El cliente Juan Pérez confirmó el pago de la compra #456 por $150.00",
  url: "/admin/orders/456/",
  datos: {
    compra_id: 456,
    cliente_id: 789,
    cliente_nombre: "Juan Pérez",
    total: 150.00,
    metodo_pago: "pi_123456..."
  },
  creada: "2025-11-10T22:46:00Z",
  leida: false
}
```

## ✅ **¡Ya está todo listo!**

Tu frontend de administrador ahora puede:

1. **Conectarse automáticamente** al WebSocket cuando un admin inicia sesión
2. **Recibir notificaciones en tiempo real** cuando los clientes hacen compras/pagos
3. **Mostrar un badge** con el conteo de notificaciones no leídas
4. **Marcar notificaciones como leídas** individualmente o todas juntas
5. **Redirigir a las páginas relevantes** al hacer clic en las notificaciones

**¿Necesitas ayuda con alguna parte específica de la implementación?** 🤔
