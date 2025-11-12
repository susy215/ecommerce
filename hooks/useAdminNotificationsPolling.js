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
