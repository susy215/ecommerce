# 🛒 API Documentation para Frontend - Cliente E-commerce

## 📋 Tabla de Contenidos
1. [Configuración Inicial](#configuración-inicial)
2. [Autenticación](#autenticación)
3. [Productos y Categorías](#productos-y-categorías)
4. [Carrito y Checkout](#carrito-y-checkout)
5. [Perfil de Cliente](#perfil-de-cliente)
6. [Mis Compras](#mis-compras)
7. [Pagos con Stripe](#pagos-con-stripe)
8. [Manejo de Errores](#manejo-de-errores)
9. [Paginación](#paginación)

---

## 🚀 Configuración Inicial

### Instalar dependencias

```bash
npm install axios
```

### Configurar Axios

```javascript
// src/api/axios.js
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para agregar el token automáticamente
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para manejar errores globalmente
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token inválido o expirado
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

---

## 🔐 Autenticación

### 1. Registro de Usuario

**Endpoint:** `POST /usuarios/register/`

**Body:**
```json
{
  "username": "cliente1",
  "email": "cliente1@email.com",
  "password": "contraseña123",
  "first_name": "Juan",
  "last_name": "Pérez",
  "telefono": "555-1234"
}
```

**Ejemplo React:**
```javascript
// src/services/authService.js
import api from '../api/axios';

export const register = async (userData) => {
  try {
    const response = await api.post('/usuarios/register/', userData);
    return { success: true, data: response.data };
  } catch (error) {
    return { 
      success: false, 
      error: error.response?.data?.detail || 'Error en el registro' 
    };
  }
};
```

**Componente de ejemplo:**
```jsx
// src/pages/Register.jsx
import { useState } from 'react';
import { register } from '../services/authService';

function Register() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    telefono: ''
  });
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    const result = await register(formData);
    
    if (result.success) {
      // Redirigir a login
      window.location.href = '/login';
    } else {
      setError(result.error);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {error && <div className="error">{error}</div>}
      <input
        type="text"
        placeholder="Usuario"
        value={formData.username}
        onChange={(e) => setFormData({...formData, username: e.target.value})}
        required
      />
      {/* Resto de campos... */}
      <button type="submit">Registrarse</button>
    </form>
  );
}
```

### 2. Iniciar Sesión

**Endpoint:** `POST /usuarios/token/`

**Body:**
```json
{
  "username": "cliente1",
  "password": "cliente1"
}
```

**O con email:**
```json
{
  "email": "cliente1@email.com",
  "password": "cliente1"
}
```

**Respuesta:**
```json
{
  "token": "abc123xyz789..."
}
```

**Ejemplo React:**
```javascript
// src/services/authService.js
export const login = async (credentials) => {
  try {
    const response = await api.post('/usuarios/token/', credentials);
    const token = response.data.token;
    
    // Guardar token
    localStorage.setItem('token', token);
    
    return { success: true, token };
  } catch (error) {
    return { 
      success: false, 
      error: error.response?.data?.detail || 'Credenciales inválidas' 
    };
  }
};
```

### 3. Obtener Perfil Actual

**Endpoint:** `GET /usuarios/me/`

**Headers:** `Authorization: Token {token}`

**Respuesta:**
```json
{
  "id": 1,
  "username": "cliente1",
  "email": "cliente1@email.com",
  "first_name": "Juan",
  "last_name": "Pérez",
  "rol": "cliente",
  "telefono": "555-1234"
}
```

**Ejemplo React:**
```javascript
export const getProfile = async () => {
  try {
    const response = await api.get('/usuarios/me/');
    return { success: true, data: response.data };
  } catch (error) {
    return { success: false, error: error.response?.data };
  }
};
```

---

## 🛍️ Productos y Categorías

### 1. Listar Productos (con paginación)

**Endpoint:** `GET /productos/productos/`

**Query Params:**
- `page`: Número de página (default: 1)
- `search`: Buscar por nombre/SKU/descripción
- `categoria`: Filtrar por ID de categoría
- `ordering`: Ordenar (`nombre`, `-precio`, `stock`, `-fecha_creacion`)

**Ejemplos:**
- `/productos/productos/` - Primera página
- `/productos/productos/?page=2` - Segunda página
- `/productos/productos/?search=laptop` - Buscar "laptop"
- `/productos/productos/?categoria=1` - Filtrar por categoría
- `/productos/productos/?ordering=-precio` - Ordenar por precio descendente

**Respuesta:**
```json
{
  "count": 20,
  "next": "http://localhost:8000/api/productos/productos/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "sku": "LAPTOP001",
      "nombre": "Laptop HP 15\"",
      "descripcion": "Laptop HP con 8GB RAM y 256GB SSD",
      "precio": "850.00",
      "stock": 15,
      "activo": true,
      "categoria": {
        "id": 1,
        "nombre": "Electrónica",
        "slug": "electronica"
      },
      "fecha_creacion": "2025-10-26T10:00:00Z",
      "fecha_actualizacion": "2025-10-26T10:00:00Z"
    }
  ]
}
```

**Servicio React:**
```javascript
// src/services/productService.js
import api from '../api/axios';

export const getProducts = async (params = {}) => {
  try {
    const response = await api.get('/productos/productos/', { params });
    return { 
      success: true, 
      data: response.data.results,
      count: response.data.count,
      next: response.data.next,
      previous: response.data.previous
    };
  } catch (error) {
    return { success: false, error: error.response?.data };
  }
};
```

**Componente con paginación:**
```jsx
// src/pages/Products.jsx
import { useState, useEffect } from 'react';
import { getProducts } from '../services/productService';

function Products() {
  const [products, setProducts] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProducts();
  }, [page]);

  const loadProducts = async () => {
    setLoading(true);
    const result = await getProducts({ page });
    
    if (result.success) {
      setProducts(result.data);
      setTotalPages(Math.ceil(result.count / 20)); // 20 items por página
    }
    setLoading(false);
  };

  return (
    <div>
      <h1>Productos</h1>
      
      {loading ? (
        <p>Cargando...</p>
      ) : (
        <>
          <div className="products-grid">
            {products.map(product => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
          
          {/* Paginación */}
          <div className="pagination">
            <button 
              onClick={() => setPage(p => p - 1)} 
              disabled={page === 1}
            >
              Anterior
            </button>
            <span>Página {page} de {totalPages}</span>
            <button 
              onClick={() => setPage(p => p + 1)} 
              disabled={page === totalPages}
            >
              Siguiente
            </button>
          </div>
        </>
      )}
    </div>
  );
}
```

### 2. Detalle de Producto

**Endpoint:** `GET /productos/productos/{id}/`

**Respuesta:**
```json
{
  "id": 1,
  "sku": "LAPTOP001",
  "nombre": "Laptop HP 15\"",
  "descripcion": "Laptop HP con 8GB RAM y 256GB SSD",
  "precio": "850.00",
  "stock": 15,
  "activo": true,
  "categoria": {
    "id": 1,
    "nombre": "Electrónica",
    "slug": "electronica"
  }
}
```

### 3. Listar Categorías

**Endpoint:** `GET /productos/categorias/`

**Respuesta:**
```json
{
  "count": 7,
  "results": [
    {
      "id": 1,
      "nombre": "Electrónica",
      "slug": "electronica"
    },
    {
      "id": 2,
      "nombre": "Ropa",
      "slug": "ropa"
    }
  ]
}
```

**Servicio:**
```javascript
export const getCategories = async () => {
  try {
    const response = await api.get('/productos/categorias/');
    return { success: true, data: response.data.results };
  } catch (error) {
    return { success: false, error: error.response?.data };
  }
};
```

---

## 🛒 Carrito y Checkout

### Gestión del Carrito (Local Storage)

El carrito se maneja completamente en el **frontend** usando Local Storage:

```javascript
// src/utils/cartUtils.js

// Obtener carrito
export const getCart = () => {
  const cart = localStorage.getItem('cart');
  return cart ? JSON.parse(cart) : [];
};

// Agregar producto al carrito
export const addToCart = (product, quantity = 1) => {
  const cart = getCart();
  const existingItem = cart.find(item => item.producto === product.id);
  
  if (existingItem) {
    existingItem.cantidad += quantity;
    // Validar stock
    if (existingItem.cantidad > product.stock) {
      existingItem.cantidad = product.stock;
      alert(`Stock máximo: ${product.stock}`);
    }
  } else {
    cart.push({
      producto: product.id,
      nombre: product.nombre,
      precio: product.precio,
      cantidad: quantity,
      stock: product.stock
    });
  }
  
  localStorage.setItem('cart', JSON.stringify(cart));
  return cart;
};

// Actualizar cantidad
export const updateCartItem = (productId, quantity) => {
  const cart = getCart();
  const item = cart.find(item => item.producto === productId);
  
  if (item) {
    item.cantidad = quantity;
    if (item.cantidad <= 0) {
      return removeFromCart(productId);
    }
  }
  
  localStorage.setItem('cart', JSON.stringify(cart));
  return cart;
};

// Eliminar del carrito
export const removeFromCart = (productId) => {
  let cart = getCart();
  cart = cart.filter(item => item.producto !== productId);
  localStorage.setItem('cart', JSON.stringify(cart));
  return cart;
};

// Limpiar carrito
export const clearCart = () => {
  localStorage.removeItem('cart');
  return [];
};

// Calcular total
export const calculateTotal = () => {
  const cart = getCart();
  return cart.reduce((total, item) => {
    return total + (parseFloat(item.precio) * item.cantidad);
  }, 0).toFixed(2);
};
```

### Checkout - Crear Compra

**Endpoint:** `POST /compra/compras/checkout/`

**Body:**
```json
{
  "items": [
    {
      "producto": 1,
      "cantidad": 2
    },
    {
      "producto": 3,
      "cantidad": 1
    }
  ],
  "observaciones": "Entregar por la tarde"
}
```

**Respuesta exitosa:**
```json
{
  "id": 15,
  "cliente": 5,
  "cliente_nombre": "Juan Pérez",
  "fecha": "2025-10-26T15:30:00Z",
  "total": "1750.00",
  "observaciones": "Entregar por la tarde",
  "pago_referencia": "",
  "pagado_en": null,
  "esta_pagada": false,
  "items": [
    {
      "id": 1,
      "producto": 1,
      "producto_nombre": "Laptop HP 15\"",
      "producto_sku": "LAPTOP001",
      "cantidad": 2,
      "precio_unitario": "850.00",
      "subtotal": "1700.00"
    }
  ]
}
```

**⚠️ Errores posibles:**
```json
// Stock insuficiente
{
  "detail": "Stock insuficiente para Laptop HP 15\". Disponible: 1, Solicitado: 2"
}

// Producto inactivo
{
  "detail": "Producto 5 no existe o está inactivo"
}

// Items vacíos
{
  "detail": "Items requeridos"
}
```

**Servicio React:**
```javascript
// src/services/checkoutService.js
import api from '../api/axios';
import { getCart, clearCart } from '../utils/cartUtils';

export const checkout = async (observaciones = '') => {
  try {
    const cart = getCart();
    
    if (cart.length === 0) {
      return { success: false, error: 'El carrito está vacío' };
    }
    
    // Formatear items para el backend
    const items = cart.map(item => ({
      producto: item.producto,
      cantidad: item.cantidad
    }));
    
    const response = await api.post('/compra/compras/checkout/', {
      items,
      observaciones
    });
    
    // Limpiar carrito después de compra exitosa
    clearCart();
    
    return { success: true, data: response.data };
  } catch (error) {
    return { 
      success: false, 
      error: error.response?.data?.detail || 'Error al procesar la compra' 
    };
  }
};
```

**Componente Checkout:**
```jsx
// src/pages/Checkout.jsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCart, calculateTotal } from '../utils/cartUtils';
import { checkout } from '../services/checkoutService';

function Checkout() {
  const [cart] = useState(getCart());
  const [observaciones, setObservaciones] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleCheckout = async () => {
    setLoading(true);
    setError('');
    
    const result = await checkout(observaciones);
    
    if (result.success) {
      // Redirigir a página de pago
      navigate(`/payment/${result.data.id}`);
    } else {
      setError(result.error);
    }
    
    setLoading(false);
  };

  if (cart.length === 0) {
    return <div>El carrito está vacío</div>;
  }

  return (
    <div>
      <h1>Checkout</h1>
      
      {error && <div className="error">{error}</div>}
      
      <div className="cart-items">
        {cart.map(item => (
          <div key={item.producto} className="cart-item">
            <h3>{item.nombre}</h3>
            <p>Cantidad: {item.cantidad}</p>
            <p>Precio: ${item.precio}</p>
            <p>Subtotal: ${(item.precio * item.cantidad).toFixed(2)}</p>
          </div>
        ))}
      </div>
      
      <div className="total">
        <h2>Total: ${calculateTotal()}</h2>
      </div>
      
      <textarea
        placeholder="Observaciones (opcional)"
        value={observaciones}
        onChange={(e) => setObservaciones(e.target.value)}
      />
      
      <button onClick={handleCheckout} disabled={loading}>
        {loading ? 'Procesando...' : 'Continuar al pago'}
      </button>
    </div>
  );
}
```

---

## 👤 Perfil de Cliente

### Ver Perfil de Cliente

**Endpoint:** `GET /clientes/clientes/{id}/`

**Nota:** El cliente solo puede ver su propio perfil. El ID se obtiene del perfil de usuario.

**Respuesta:**
```json
{
  "id": 1,
  "usuario": 5,
  "usuario_username": "cliente1",
  "nombre": "Juan Pérez",
  "email": "cliente1@email.com",
  "telefono": "555-2001",
  "direccion": "Av. Principal 123, Ciudad",
  "asignado_a": 2,
  "asignado_a_nombre": "Vendedor Número 1",
  "fecha_creacion": "2025-10-26T10:00:00Z"
}
```

---

## 📦 Mis Compras

### 1. Listar Mis Compras

**Endpoint:** `GET /compra/compras/`

**Query Params:**
- `page`: Número de página
- `search`: Buscar por nombre de cliente u observaciones
- `ordering`: `-fecha`, `total`

**Respuesta:**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 15,
      "cliente": 5,
      "cliente_nombre": "Juan Pérez",
      "fecha": "2025-10-26T15:30:00Z",
      "total": "1750.00",
      "observaciones": "Entregar por la tarde",
      "pago_referencia": "PAY-1234",
      "pagado_en": "2025-10-26T16:00:00Z",
      "esta_pagada": true,
      "stripe_session_id": "",
      "stripe_payment_intent": "",
      "items": [
        {
          "id": 1,
          "producto": 1,
          "producto_nombre": "Laptop HP 15\"",
          "producto_sku": "LAPTOP001",
          "cantidad": 2,
          "precio_unitario": "850.00",
          "subtotal": "1700.00"
        }
      ]
    }
  ]
}
```

**Servicio:**
```javascript
// src/services/orderService.js
export const getMyOrders = async (page = 1) => {
  try {
    const response = await api.get('/compra/compras/', { 
      params: { page, ordering: '-fecha' } 
    });
    return { 
      success: true, 
      data: response.data.results,
      count: response.data.count 
    };
  } catch (error) {
    return { success: false, error: error.response?.data };
  }
};
```

### 2. Detalle de Compra

**Endpoint:** `GET /compra/compras/{id}/`

**Respuesta:** Igual que el formato anterior pero para una sola compra.

### 3. Descargar Comprobante PDF

**Endpoint:** `GET /compra/compras/{id}/receipt/`

**Ejemplo:**
```javascript
export const downloadReceipt = (orderId) => {
  const token = localStorage.getItem('token');
  const url = `http://localhost:8000/api/compra/compras/${orderId}/receipt/`;
  
  // Abrir en nueva ventana
  window.open(url + `?token=${token}`, '_blank');
};
```

---

## 💳 Pagos con Stripe

### 1. Crear Sesión de Pago

**Endpoint:** `POST /compra/compras/{id}/stripe_session/`

**Body (opcional):**
```json
{
  "success_url": "http://localhost:5173/checkout/success?compra=15",
  "cancel_url": "http://localhost:5173/checkout/cancel?compra=15"
}
```

**Respuesta:**
```json
{
  "id": "cs_test_abc123...",
  "url": "https://checkout.stripe.com/pay/cs_test_abc123..."
}
```

**Servicio:**
```javascript
// src/services/paymentService.js
export const createStripeSession = async (orderId) => {
  try {
    const response = await api.post(
      `/compra/compras/${orderId}/stripe_session/`,
      {
        success_url: `${window.location.origin}/checkout/success?compra=${orderId}`,
        cancel_url: `${window.location.origin}/checkout/cancel?compra=${orderId}`
      }
    );
    return { success: true, data: response.data };
  } catch (error) {
    return { 
      success: false, 
      error: error.response?.data?.detail || 'Error al crear sesión de pago' 
    };
  }
};
```

**Componente de Pago:**
```jsx
// src/pages/Payment.jsx
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { createStripeSession } from '../services/paymentService';

function Payment() {
  const { orderId } = useParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    initiatePayment();
  }, []);

  const initiatePayment = async () => {
    const result = await createStripeSession(orderId);
    
    if (result.success) {
      // Redirigir a Stripe Checkout
      window.location.href = result.data.url;
    } else {
      setError(result.error);
      setLoading(false);
    }
  };

  if (loading) {
    return <div>Redirigiendo a la pasarela de pago...</div>;
  }

  return (
    <div>
      <h1>Error en el pago</h1>
      <p>{error}</p>
    </div>
  );
}
```

### 2. Página de Éxito

```jsx
// src/pages/CheckoutSuccess.jsx
import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { getOrderDetail } from '../services/orderService';

function CheckoutSuccess() {
  const [searchParams] = useSearchParams();
  const compraId = searchParams.get('compra');
  const [order, setOrder] = useState(null);

  useEffect(() => {
    if (compraId) {
      loadOrder();
    }
  }, [compraId]);

  const loadOrder = async () => {
    const result = await getOrderDetail(compraId);
    if (result.success) {
      setOrder(result.data);
    }
  };

  return (
    <div>
      <h1>¡Pago exitoso! 🎉</h1>
      {order && (
        <div>
          <p>Número de orden: {order.id}</p>
          <p>Total pagado: ${order.total}</p>
          <p>Fecha: {new Date(order.fecha).toLocaleDateString()}</p>
          <button onClick={() => downloadReceipt(order.id)}>
            Descargar Comprobante
          </button>
        </div>
      )}
    </div>
  );
}
```

---

## ⚠️ Manejo de Errores

### Estructura de Errores del Backend

El backend devuelve errores en este formato:

```json
{
  "detail": "Mensaje de error específico"
}
```

O errores de validación:

```json
{
  "username": ["Este campo es requerido"],
  "email": ["Ingrese una dirección de correo válida"]
}
```

### Utilidad para Manejar Errores

```javascript
// src/utils/errorHandler.js

export const handleApiError = (error) => {
  if (error.response) {
    // El servidor respondió con un código de error
    const { data, status } = error.response;
    
    // Error con mensaje específico
    if (data.detail) {
      return data.detail;
    }
    
    // Errores de validación de campos
    if (typeof data === 'object') {
      const errors = Object.entries(data)
        .map(([field, messages]) => `${field}: ${messages.join(', ')}`)
        .join('\n');
      return errors;
    }
    
    // Error genérico por código de estado
    switch (status) {
      case 400:
        return 'Solicitud inválida';
      case 401:
        return 'No autorizado. Por favor inicia sesión';
      case 403:
        return 'No tienes permisos para esta acción';
      case 404:
        return 'Recurso no encontrado';
      case 500:
        return 'Error del servidor';
      default:
        return 'Error desconocido';
    }
  } else if (error.request) {
    // La solicitud se hizo pero no hubo respuesta
    return 'No se pudo conectar con el servidor';
  } else {
    // Error al configurar la solicitud
    return error.message || 'Error desconocido';
  }
};
```

### Componente de Error

```jsx
// src/components/ErrorAlert.jsx
function ErrorAlert({ error, onClose }) {
  if (!error) return null;
  
  return (
    <div className="error-alert">
      <span>{error}</span>
      {onClose && <button onClick={onClose}>×</button>}
    </div>
  );
}
```

---

## 📄 Paginación

### Respuesta con Paginación

Todos los endpoints de lista devuelven:

```json
{
  "count": 50,        // Total de items
  "next": "url",      // URL de la siguiente página (null si no hay)
  "previous": "url",  // URL de la página anterior (null si no hay)
  "results": []       // Array de resultados
}
```

### Hook Custom para Paginación

```javascript
// src/hooks/usePagination.js
import { useState, useEffect } from 'react';

export const usePagination = (fetchFunction, dependencies = []) => {
  const [data, setData] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, [page, ...dependencies]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    
    const result = await fetchFunction({ page });
    
    if (result.success) {
      setData(result.data);
      setTotalPages(Math.ceil(result.count / 20)); // 20 items por página
    } else {
      setError(result.error);
    }
    
    setLoading(false);
  };

  const nextPage = () => {
    if (page < totalPages) setPage(p => p + 1);
  };

  const prevPage = () => {
    if (page > 1) setPage(p => p - 1);
  };

  const goToPage = (pageNumber) => {
    if (pageNumber >= 1 && pageNumber <= totalPages) {
      setPage(pageNumber);
    }
  };

  return {
    data,
    page,
    totalPages,
    loading,
    error,
    nextPage,
    prevPage,
    goToPage,
    refresh: loadData
  };
};
```

### Uso del Hook

```jsx
// src/pages/Products.jsx
import { usePagination } from '../hooks/usePagination';
import { getProducts } from '../services/productService';

function Products() {
  const {
    data: products,
    page,
    totalPages,
    loading,
    error,
    nextPage,
    prevPage
  } = usePagination(getProducts);

  if (loading) return <div>Cargando...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <div className="products-grid">
        {products.map(product => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>
      
      <div className="pagination">
        <button onClick={prevPage} disabled={page === 1}>
          Anterior
        </button>
        <span>Página {page} de {totalPages}</span>
        <button onClick={nextPage} disabled={page === totalPages}>
          Siguiente
        </button>
      </div>
    </div>
  );
}
```

---

## 🎯 Flujo Completo de Compra

### Paso a Paso

```
1. Usuario navega productos
   ↓
2. Agrega productos al carrito (Local Storage)
   ↓
3. Va al checkout
   ↓
4. POST /compra/compras/checkout/ 
   ⚠️ Backend valida stock automáticamente
   ⚠️ Backend reduce stock automáticamente
   ↓
5. Si éxito: Recibe ID de compra
   ↓
6. POST /compra/compras/{id}/stripe_session/
   ↓
7. Redirige a Stripe Checkout
   ↓
8. Usuario completa pago en Stripe
   ↓
9. Stripe redirige a success_url
   ↓
10. Backend recibe webhook de Stripe
    ⚠️ Backend marca compra como pagada automáticamente
    ↓
11. Usuario ve confirmación de pago
```

---

## 📋 Ejemplo Completo de Flujo

```javascript
// src/App.jsx estructura sugerida
import { BrowserRouter, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Autenticación */}
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<Login />} />
        
        {/* Productos */}
        <Route path="/" element={<Products />} />
        <Route path="/products/:id" element={<ProductDetail />} />
        <Route path="/categories/:slug" element={<CategoryProducts />} />
        
        {/* Carrito y Checkout */}
        <Route path="/cart" element={<Cart />} />
        <Route path="/checkout" element={<Checkout />} />
        <Route path="/payment/:orderId" element={<Payment />} />
        <Route path="/checkout/success" element={<CheckoutSuccess />} />
        <Route path="/checkout/cancel" element={<CheckoutCancel />} />
        
        {/* Perfil y Órdenes */}
        <Route path="/profile" element={<Profile />} />
        <Route path="/orders" element={<MyOrders />} />
        <Route path="/orders/:id" element={<OrderDetail />} />
      </Routes>
    </BrowserRouter>
  );
}
```

---

## 🔧 Variables de Entorno

```env
# .env
VITE_API_URL=http://localhost:8000/api
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

Uso en código:
```javascript
const API_URL = import.meta.env.VITE_API_URL;
```

---

## ✅ Checklist de Implementación

- [ ] Configurar Axios con interceptores
- [ ] Implementar sistema de autenticación
- [ ] Crear servicio de productos con paginación
- [ ] Implementar carrito en Local Storage
- [ ] Crear flujo de checkout
- [ ] Integrar Stripe Checkout
- [ ] Implementar listado de órdenes
- [ ] Agregar manejo global de errores
- [ ] Probar flujo completo de compra

---

## 🚨 Notas Importantes

1. **Stock**: El backend valida y reduce automáticamente el stock. No necesitas manejarlo en el frontend.

2. **Autenticación**: Todos los endpoints requieren el token excepto:
   - `/usuarios/register/`
   - `/usuarios/token/`

3. **Errores de Stock**: Si un producto no tiene stock suficiente, el backend devolverá un error específico.

4. **Pagos**: El webhook de Stripe actualiza automáticamente el estado de pago. No necesitas hacer nada adicional.

5. **Paginación**: Todos los listados están paginados con 20 items por página.

---

¡Listo! Con esta documentación tienes todo lo necesario para implementar el frontend del e-commerce. 🚀
