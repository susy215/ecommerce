# 🛒 SmartSales365 - Documentación Frontend Cliente

## 📱 Para: React + Vite + JSX → Vercel

**Rol:** Cliente final que compra productos (NO admin)

---

## 🎯 Flujo del Cliente

```
1. Registro/Login
2. Ver productos y categorías
3. Agregar al carrito (estado local)
4. Aplicar cupón de descuento (opcional)
5. Checkout (crear pedido)
6. Pagar (Stripe o manual)
7. Recibir notificación push
8. Ver mis pedidos
9. Descargar comprobante PDF
```

---

## 🔧 Configuración Inicial

### 1. Instalar Dependencias

```bash
npm install axios
```

### 2. Variables de Entorno

Crear `.env`:

```env
# Backend API
VITE_API_URL=http://localhost:8000

# Stripe (clave pública)
VITE_STRIPE_PUBLIC_KEY=pk_test_...

# Producción (Vercel)
# VITE_API_URL=https://tu-backend.com
```

### 3. Configurar Axios

`src/api/axios.js`:

```javascript
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para agregar token automáticamente
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

// Interceptor para manejar errores de autenticación
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expirado o inválido
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

---

## 🔐 1. Autenticación

### Registro de Usuario

**Endpoint:** `POST /api/usuarios/register/`

```javascript
// src/services/auth.js
import api from '../api/axios';

export const authService = {
  // Registro
  async register(userData) {
    const response = await api.post('/usuarios/register/', {
      username: userData.username,
      email: userData.email,
      password: userData.password,
      first_name: userData.firstName,
      last_name: userData.lastName,
      telefono: userData.phone || '',
    });
    return response.data;
  },

  // Login
  async login(credentials) {
    const response = await api.post('/usuarios/token/', {
      username: credentials.username, // Puede ser username o email
      password: credentials.password,
    });
    
    const { token } = response.data;
    localStorage.setItem('token', token);
    
    // Obtener datos del usuario
    const user = await this.getMe();
    localStorage.setItem('user', JSON.stringify(user));
    
    return { token, user };
  },

  // Obtener perfil actual
  async getMe() {
    const response = await api.get('/usuarios/me/');
    return response.data;
  },

  // Actualizar perfil
  async updateMe(userData) {
    const response = await api.patch('/usuarios/me/', userData);
    localStorage.setItem('user', JSON.stringify(response.data));
    return response.data;
  },

  // Logout
  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },

  // Verificar si está autenticado
  isAuthenticated() {
    return !!localStorage.getItem('token');
  },

  // Obtener usuario actual
  getCurrentUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },
};
```

### Componente de Login

```jsx
// src/pages/Login.jsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/auth';

export default function Login() {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await authService.login(credentials);
      navigate('/productos'); // Redirigir a catálogo
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al iniciar sesión');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <h1>Iniciar Sesión</h1>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Usuario o Email"
          value={credentials.username}
          onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
          required
        />
        <input
          type="password"
          placeholder="Contraseña"
          value={credentials.password}
          onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
          required
        />
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={loading}>
          {loading ? 'Cargando...' : 'Entrar'}
        </button>
      </form>
      <p>
        ¿No tienes cuenta? <a href="/register">Regístrate</a>
      </p>
    </div>
  );
}
```

### Componente de Registro

```jsx
// src/pages/Register.jsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/auth';

export default function Register() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    firstName: '',
    lastName: '',
    phone: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('Las contraseñas no coinciden');
      return;
    }

    setLoading(true);

    try {
      await authService.register(formData);
      // Hacer login automático después del registro
      await authService.login({
        username: formData.username,
        password: formData.password,
      });
      navigate('/productos');
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al registrarse');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="register-container">
      <h1>Crear Cuenta</h1>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Usuario"
          value={formData.username}
          onChange={(e) => setFormData({ ...formData, username: e.target.value })}
          required
        />
        <input
          type="email"
          placeholder="Email"
          value={formData.email}
          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          required
        />
        <input
          type="text"
          placeholder="Nombre"
          value={formData.firstName}
          onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
        />
        <input
          type="text"
          placeholder="Apellido"
          value={formData.lastName}
          onChange={(e) => setFormData({ ...formData, lastName: e.target.value })}
        />
        <input
          type="tel"
          placeholder="Teléfono (opcional)"
          value={formData.phone}
          onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
        />
        <input
          type="password"
          placeholder="Contraseña"
          value={formData.password}
          onChange={(e) => setFormData({ ...formData, password: e.target.value })}
          required
        />
        <input
          type="password"
          placeholder="Confirmar Contraseña"
          value={formData.confirmPassword}
          onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
          required
        />
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={loading}>
          {loading ? 'Registrando...' : 'Registrarse'}
        </button>
      </form>
      <p>
        ¿Ya tienes cuenta? <a href="/login">Inicia sesión</a>
      </p>
    </div>
  );
}
```

---

## 🛍️ 2. Productos y Categorías

### Service de Productos

```javascript
// src/services/products.js
import api from '../api/axios';

export const productService = {
  // Listar productos (con paginación y filtros)
  async getProducts(params = {}) {
    const response = await api.get('/productos/', { params });
    return response.data; // { count, next, previous, results }
  },

  // Obtener un producto específico
  async getProduct(id) {
    const response = await api.get(`/productos/${id}/`);
    return response.data;
  },

  // Listar categorías
  async getCategories() {
    const response = await api.get('/productos/categorias/');
    return response.data;
  },

  // Buscar productos
  async searchProducts(query) {
    const response = await api.get('/productos/', {
      params: { search: query },
    });
    return response.data;
  },

  // Filtrar por categoría
  async getProductsByCategory(categoryId) {
    const response = await api.get('/productos/', {
      params: { categoria: categoryId },
    });
    return response.data;
  },
};
```

### Catálogo de Productos

```jsx
// src/pages/Products.jsx
import { useState, useEffect } from 'react';
import { productService } from '../services/products';
import ProductCard from '../components/ProductCard';

export default function Products() {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    loadCategories();
  }, []);

  useEffect(() => {
    loadProducts();
  }, [selectedCategory, searchQuery, page]);

  const loadCategories = async () => {
    try {
      const data = await productService.getCategories();
      setCategories(data.results || data);
    } catch (error) {
      console.error('Error cargando categorías:', error);
    }
  };

  const loadProducts = async () => {
    setLoading(true);
    try {
      const params = { page };
      if (selectedCategory) params.categoria = selectedCategory;
      if (searchQuery) params.search = searchQuery;

      const data = await productService.getProducts(params);
      setProducts(data.results);
      setTotalPages(Math.ceil(data.count / 20)); // 20 items por página
    } catch (error) {
      console.error('Error cargando productos:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    loadProducts();
  };

  return (
    <div className="products-page">
      <h1>Catálogo de Productos</h1>

      {/* Buscador */}
      <form onSubmit={handleSearch} className="search-bar">
        <input
          type="text"
          placeholder="Buscar productos..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <button type="submit">Buscar</button>
      </form>

      {/* Filtro por categoría */}
      <div className="categories">
        <button
          className={!selectedCategory ? 'active' : ''}
          onClick={() => {
            setSelectedCategory(null);
            setPage(1);
          }}
        >
          Todas
        </button>
        {categories.map((cat) => (
          <button
            key={cat.id}
            className={selectedCategory === cat.id ? 'active' : ''}
            onClick={() => {
              setSelectedCategory(cat.id);
              setPage(1);
            }}
          >
            {cat.nombre}
          </button>
        ))}
      </div>

      {/* Lista de productos */}
      {loading ? (
        <p>Cargando productos...</p>
      ) : (
        <>
          <div className="products-grid">
            {products.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>

          {/* Paginación */}
          {totalPages > 1 && (
            <div className="pagination">
              <button
                onClick={() => setPage(page - 1)}
                disabled={page === 1}
              >
                Anterior
              </button>
              <span>Página {page} de {totalPages}</span>
              <button
                onClick={() => setPage(page + 1)}
                disabled={page === totalPages}
              >
                Siguiente
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
```

### Componente ProductCard

```jsx
// src/components/ProductCard.jsx
import { useCart } from '../context/CartContext';

export default function ProductCard({ product }) {
  const { addToCart } = useCart();

  return (
    <div className="product-card">
      {product.imagen && (
        <img src={product.imagen} alt={product.nombre} />
      )}
      <h3>{product.nombre}</h3>
      <p className="description">{product.descripcion}</p>
      <p className="price">${parseFloat(product.precio).toFixed(2)}</p>
      <p className="stock">
        {product.stock > 0 ? (
          <span className="in-stock">En stock: {product.stock}</span>
        ) : (
          <span className="out-of-stock">Agotado</span>
        )}
      </p>
      <button
        onClick={() => addToCart(product)}
        disabled={product.stock === 0}
        className="add-to-cart-btn"
      >
        {product.stock > 0 ? 'Agregar al carrito' : 'No disponible'}
      </button>
    </div>
  );
}
```

---

## 🛒 3. Carrito de Compra (Estado Local)

### Context del Carrito

```jsx
// src/context/CartContext.jsx
import { createContext, useContext, useState, useEffect } from 'react';

const CartContext = createContext();

export function CartProvider({ children }) {
  const [cart, setCart] = useState([]);

  // Cargar carrito del localStorage al iniciar
  useEffect(() => {
    const savedCart = localStorage.getItem('cart');
    if (savedCart) {
      setCart(JSON.parse(savedCart));
    }
  }, []);

  // Guardar carrito en localStorage cada vez que cambie
  useEffect(() => {
    localStorage.setItem('cart', JSON.stringify(cart));
  }, [cart]);

  const addToCart = (product, quantity = 1) => {
    setCart((prevCart) => {
      const existingItem = prevCart.find((item) => item.id === product.id);
      
      if (existingItem) {
        // Incrementar cantidad
        return prevCart.map((item) =>
          item.id === product.id
            ? { ...item, quantity: Math.min(item.quantity + quantity, product.stock) }
            : item
        );
      } else {
        // Agregar nuevo item
        return [...prevCart, { ...product, quantity: Math.min(quantity, product.stock) }];
      }
    });
  };

  const removeFromCart = (productId) => {
    setCart((prevCart) => prevCart.filter((item) => item.id !== productId));
  };

  const updateQuantity = (productId, quantity) => {
    if (quantity <= 0) {
      removeFromCart(productId);
      return;
    }

    setCart((prevCart) =>
      prevCart.map((item) =>
        item.id === productId
          ? { ...item, quantity: Math.min(quantity, item.stock) }
          : item
      )
    );
  };

  const clearCart = () => {
    setCart([]);
  };

  const getCartTotal = () => {
    return cart.reduce((total, item) => total + parseFloat(item.precio) * item.quantity, 0);
  };

  const getCartCount = () => {
    return cart.reduce((count, item) => count + item.quantity, 0);
  };

  return (
    <CartContext.Provider
      value={{
        cart,
        addToCart,
        removeFromCart,
        updateQuantity,
        clearCart,
        getCartTotal,
        getCartCount,
      }}
    >
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
}
```

### Página del Carrito

```jsx
// src/pages/Cart.jsx
import { useNavigate } from 'react-router-dom';
import { useCart } from '../context/CartContext';

export default function Cart() {
  const { cart, updateQuantity, removeFromCart, getCartTotal, clearCart } = useCart();
  const navigate = useNavigate();

  if (cart.length === 0) {
    return (
      <div className="cart-empty">
        <h1>Tu carrito está vacío</h1>
        <button onClick={() => navigate('/productos')}>
          Ir a comprar
        </button>
      </div>
    );
  }

  return (
    <div className="cart-page">
      <h1>Mi Carrito</h1>

      <div className="cart-items">
        {cart.map((item) => (
          <div key={item.id} className="cart-item">
            <img src={item.imagen || '/placeholder.png'} alt={item.nombre} />
            <div className="item-details">
              <h3>{item.nombre}</h3>
              <p className="price">${parseFloat(item.precio).toFixed(2)}</p>
            </div>
            <div className="item-quantity">
              <button onClick={() => updateQuantity(item.id, item.quantity - 1)}>-</button>
              <span>{item.quantity}</span>
              <button onClick={() => updateQuantity(item.id, item.quantity + 1)}>+</button>
            </div>
            <div className="item-total">
              ${(parseFloat(item.precio) * item.quantity).toFixed(2)}
            </div>
            <button onClick={() => removeFromCart(item.id)} className="remove-btn">
              🗑️
            </button>
          </div>
        ))}
      </div>

      <div className="cart-summary">
        <h2>Resumen del Pedido</h2>
        <p>Subtotal: ${getCartTotal().toFixed(2)}</p>
        <div className="cart-actions">
          <button onClick={clearCart} className="clear-btn">
            Vaciar carrito
          </button>
          <button onClick={() => navigate('/checkout')} className="checkout-btn">
            Proceder al pago
          </button>
        </div>
      </div>
    </div>
  );
}
```

---

## 🎁 4. Promociones y Cupones

### Service de Promociones

```javascript
// src/services/promotions.js
import api from '../api/axios';

export const promotionService = {
  // Listar promociones vigentes
  async getPromotions() {
    const response = await api.get('/promociones/promociones/');
    return response.data;
  },

  // Validar código de promoción
  async validateCode(code) {
    try {
      const response = await api.get(`/promociones/promociones/validar_codigo/`, {
        params: { codigo: code },
      });
      return response.data; // { valido: true, promocion: {...} }
    } catch (error) {
      throw error.response?.data || error;
    }
  },
};
```

### Componente de Cupón

```jsx
// src/components/CouponInput.jsx
import { useState } from 'react';
import { promotionService } from '../services/promotions';

export default function CouponInput({ onApply }) {
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleApply = async () => {
    if (!code.trim()) return;

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const result = await promotionService.validateCode(code.toUpperCase());
      if (result.valido) {
        setSuccess(`¡Cupón aplicado! ${result.promocion.descripcion}`);
        onApply(result.promocion);
      } else {
        setError('Código de cupón inválido o expirado');
      }
    } catch (err) {
      setError(err.detail || 'Error al validar el cupón');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="coupon-input">
      <input
        type="text"
        placeholder="Código de cupón"
        value={code}
        onChange={(e) => setCode(e.target.value.toUpperCase())}
        disabled={loading}
      />
      <button onClick={handleApply} disabled={loading || !code.trim()}>
        {loading ? 'Validando...' : 'Aplicar'}
      </button>
      {error && <p className="error">{error}</p>}
      {success && <p className="success">{success}</p>}
    </div>
  );
}
```

---

## 💳 5. Checkout y Pago

### Service de Compras

```javascript
// src/services/checkout.js
import api from '../api/axios';

export const checkoutService = {
  // Crear pedido (checkout)
  async createOrder(orderData) {
    const response = await api.post('/compra/compras/checkout/', orderData);
    return response.data;
  },

  // Marcar como pagada (pago manual)
  async markAsPaid(orderId, referencia) {
    const response = await api.post(`/compra/compras/${orderId}/pay/`, {
      referencia,
    });
    return response.data;
  },

  // Crear sesión de Stripe
  async createStripeSession(orderId) {
    const response = await api.post(`/compra/compras/${orderId}/stripe_session/`);
    return response.data; // { session_id, url }
  },

  // Obtener mis compras
  async getMyOrders() {
    const response = await api.get('/compra/compras/');
    return response.data;
  },

  // Obtener detalle de una compra
  async getOrder(orderId) {
    const response = await api.get(`/compra/compras/${orderId}/`);
    return response.data;
  },

  // Descargar comprobante PDF
  getReceiptUrl(orderId) {
    const token = localStorage.getItem('token');
    return `${import.meta.env.VITE_API_URL}/api/compra/compras/${orderId}/receipt/?token=${token}`;
  },
};
```

### Página de Checkout

```jsx
// src/pages/Checkout.jsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCart } from '../context/CartContext';
import { checkoutService } from '../services/checkout';
import { promotionService } from '../services/promotions';
import CouponInput from '../components/CouponInput';

export default function Checkout() {
  const { cart, getCartTotal, clearCart } = useCart();
  const [observaciones, setObservaciones] = useState('');
  const [coupon, setCoupon] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleCheckout = async () => {
    setLoading(true);
    setError('');

    try {
      // Preparar items para el backend
      const items = cart.map((item) => ({
        producto: item.id,
        cantidad: item.quantity,
      }));

      const orderData = {
        items,
        observaciones,
      };

      // Agregar código de promoción si existe
      if (coupon) {
        orderData.codigo_promocion = coupon.codigo;
      }

      // Crear pedido
      const order = await checkoutService.createOrder(orderData);

      // Limpiar carrito
      clearCart();

      // Redirigir a página de pago
      navigate(`/pago/${order.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al procesar el pedido');
    } finally {
      setLoading(false);
    }
  };

  const calculateDiscount = () => {
    if (!coupon) return 0;
    const subtotal = getCartTotal();
    if (coupon.tipo === 'porcentaje') {
      return (subtotal * parseFloat(coupon.valor)) / 100;
    } else {
      return parseFloat(coupon.valor);
    }
  };

  const getFinalTotal = () => {
    return Math.max(0, getCartTotal() - calculateDiscount());
  };

  if (cart.length === 0) {
    return (
      <div className="checkout-empty">
        <h1>No hay productos en el carrito</h1>
        <button onClick={() => navigate('/productos')}>Ir a comprar</button>
      </div>
    );
  }

  return (
    <div className="checkout-page">
      <h1>Finalizar Compra</h1>

      {/* Resumen de productos */}
      <div className="order-summary">
        <h2>Resumen del Pedido</h2>
        {cart.map((item) => (
          <div key={item.id} className="summary-item">
            <span>{item.nombre} x {item.quantity}</span>
            <span>${(parseFloat(item.precio) * item.quantity).toFixed(2)}</span>
          </div>
        ))}
        
        <div className="summary-subtotal">
          <strong>Subtotal:</strong>
          <strong>${getCartTotal().toFixed(2)}</strong>
        </div>

        {/* Cupón de descuento */}
        <CouponInput onApply={setCoupon} />

        {coupon && (
          <div className="summary-discount">
            <span>Descuento ({coupon.codigo}):</span>
            <span className="discount">-${calculateDiscount().toFixed(2)}</span>
          </div>
        )}

        <div className="summary-total">
          <strong>Total:</strong>
          <strong>${getFinalTotal().toFixed(2)}</strong>
        </div>
      </div>

      {/* Observaciones */}
      <div className="order-notes">
        <label>Observaciones (opcional)</label>
        <textarea
          value={observaciones}
          onChange={(e) => setObservaciones(e.target.value)}
          placeholder="Instrucciones especiales, dirección de entrega, etc."
          rows="4"
        />
      </div>

      {error && <p className="error">{error}</p>}

      <button
        onClick={handleCheckout}
        disabled={loading}
        className="checkout-btn"
      >
        {loading ? 'Procesando...' : 'Confirmar Pedido'}
      </button>
    </div>
  );
}
```

### Página de Pago

```jsx
// src/pages/Payment.jsx
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { checkoutService } from '../services/checkout';
import { loadStripe } from '@stripe/stripe-js';

// Inicializar Stripe
const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLIC_KEY);

export default function Payment() {
  const { orderId } = useParams();
  const [order, setOrder] = useState(null);
  const [paymentMethod, setPaymentMethod] = useState('stripe');
  const [referencia, setReferencia] = useState('');
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    loadOrder();
  }, [orderId]);

  const loadOrder = async () => {
    try {
      const data = await checkoutService.getOrder(orderId);
      setOrder(data);
    } catch (err) {
      setError('Pedido no encontrado');
    } finally {
      setLoading(false);
    }
  };

  const handleStripePayment = async () => {
    setProcessing(true);
    setError('');

    try {
      // Crear sesión de Stripe
      const { url } = await checkoutService.createStripeSession(orderId);
      
      // Redirigir a Stripe Checkout
      window.location.href = url;
    } catch (err) {
      setError('Error al procesar el pago con Stripe');
      setProcessing(false);
    }
  };

  const handleManualPayment = async () => {
    if (!referencia.trim()) {
      setError('Ingresa una referencia de pago');
      return;
    }

    setProcessing(true);
    setError('');

    try {
      await checkoutService.markAsPaid(orderId, referencia);
      navigate(`/pedidos/${orderId}/confirmacion`);
    } catch (err) {
      setError('Error al confirmar el pago');
      setProcessing(false);
    }
  };

  if (loading) return <p>Cargando...</p>;
  if (!order) return <p>Pedido no encontrado</p>;

  return (
    <div className="payment-page">
      <h1>Pagar Pedido #{order.id}</h1>

      <div className="order-info">
        <p><strong>Total a pagar:</strong> ${parseFloat(order.total).toFixed(2)}</p>
        {order.descuento_aplicado > 0 && (
          <p><strong>Descuento aplicado:</strong> ${parseFloat(order.descuento_aplicado).toFixed(2)}</p>
        )}
      </div>

      {/* Métodos de pago */}
      <div className="payment-methods">
        <h2>Método de Pago</h2>

        <label>
          <input
            type="radio"
            value="stripe"
            checked={paymentMethod === 'stripe'}
            onChange={(e) => setPaymentMethod(e.target.value)}
          />
          <span>💳 Tarjeta de Crédito/Débito (Stripe)</span>
        </label>

        <label>
          <input
            type="radio"
            value="manual"
            checked={paymentMethod === 'manual'}
            onChange={(e) => setPaymentMethod(e.target.value)}
          />
          <span>🏦 Transferencia Bancaria</span>
        </label>
      </div>

      {/* Pago con Stripe */}
      {paymentMethod === 'stripe' && (
        <div className="stripe-payment">
          <p>Serás redirigido a la página segura de Stripe para completar el pago.</p>
          <button
            onClick={handleStripePayment}
            disabled={processing}
            className="pay-btn"
          >
            {processing ? 'Redirigiendo...' : 'Pagar con Stripe'}
          </button>
        </div>
      )}

      {/* Pago manual */}
      {paymentMethod === 'manual' && (
        <div className="manual-payment">
          <p>Realiza la transferencia a la siguiente cuenta:</p>
          <div className="bank-info">
            <p><strong>Banco:</strong> Banco XYZ</p>
            <p><strong>Cuenta:</strong> 1234-5678-9012</p>
            <p><strong>Beneficiario:</strong> SmartSales365</p>
          </div>
          <label>
            Número de referencia:
            <input
              type="text"
              value={referencia}
              onChange={(e) => setReferencia(e.target.value)}
              placeholder="Ej: REF123456"
            />
          </label>
          <button
            onClick={handleManualPayment}
            disabled={processing || !referencia.trim()}
            className="pay-btn"
          >
            {processing ? 'Confirmando...' : 'Confirmar Pago'}
          </button>
        </div>
      )}

      {error && <p className="error">{error}</p>}
    </div>
  );
}
```

---

## 📦 6. Mis Pedidos

### Página de Pedidos

```jsx
// src/pages/MyOrders.jsx
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { checkoutService } from '../services/checkout';

export default function MyOrders() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async () => {
    try {
      const data = await checkoutService.getMyOrders();
      setOrders(data.results || data);
    } catch (error) {
      console.error('Error cargando pedidos:', error);
    } finally {
      setLoading(false);
    }
  };

  const downloadReceipt = (orderId) => {
    const url = checkoutService.getReceiptUrl(orderId);
    window.open(url, '_blank');
  };

  if (loading) return <p>Cargando pedidos...</p>;

  if (orders.length === 0) {
    return (
      <div className="no-orders">
        <h1>No tienes pedidos aún</h1>
        <button onClick={() => navigate('/productos')}>
          Ir a comprar
        </button>
      </div>
    );
  }

  return (
    <div className="my-orders-page">
      <h1>Mis Pedidos</h1>

      <div className="orders-list">
        {orders.map((order) => (
          <div key={order.id} className="order-card">
            <div className="order-header">
              <h3>Pedido #{order.id}</h3>
              <span className={`status ${order.pagado_en ? 'paid' : 'pending'}`}>
                {order.pagado_en ? '✅ Pagado' : '⏳ Pendiente de pago'}
              </span>
            </div>

            <div className="order-details">
              <p><strong>Fecha:</strong> {new Date(order.fecha).toLocaleDateString()}</p>
              <p><strong>Total:</strong> ${parseFloat(order.total).toFixed(2)}</p>
              {order.descuento_aplicado > 0 && (
                <p><strong>Descuento:</strong> ${parseFloat(order.descuento_aplicado).toFixed(2)}</p>
              )}
              <p><strong>Items:</strong> {order.items.length} producto(s)</p>
            </div>

            <div className="order-items">
              {order.items.map((item) => (
                <div key={item.id} className="order-item">
                  <span>{item.producto_detalle?.nombre || 'Producto'}</span>
                  <span>x {item.cantidad}</span>
                  <span>${parseFloat(item.subtotal).toFixed(2)}</span>
                </div>
              ))}
            </div>

            <div className="order-actions">
              <button onClick={() => navigate(`/pedidos/${order.id}`)}>
                Ver Detalle
              </button>
              {order.pagado_en && (
                <button onClick={() => downloadReceipt(order.id)} className="download-btn">
                  📄 Descargar Comprobante
                </button>
              )}
              {!order.pagado_en && (
                <button onClick={() => navigate(`/pago/${order.id}`)} className="pay-btn">
                  💳 Pagar Ahora
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## 🔔 7. Notificaciones Push

### Configuración de Notificaciones

```javascript
// src/services/pushNotifications.js
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Obtener clave pública VAPID
export async function getVapidPublicKey() {
  const response = await fetch(`${API_URL}/api/notificaciones/vapid-public-key/`);
  const data = await response.json();
  return data.public_key;
}

// Convertir clave VAPID a Uint8Array
function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

// Convertir ArrayBuffer a Base64
function arrayBufferToBase64(buffer) {
  if (!buffer) return '';
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return window.btoa(binary);
}

// Suscribirse a notificaciones
export async function subscribeToPushNotifications(token) {
  // Verificar soporte
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
    console.warn('Push notifications no soportadas');
    return false;
  }

  try {
    // Registrar service worker
    const registration = await navigator.serviceWorker.register('/sw.js');
    console.log('Service Worker registrado');

    // Solicitar permiso
    const permission = await Notification.requestPermission();
    if (permission !== 'granted') {
      console.log('Permiso de notificaciones denegado');
      return false;
    }

    // Obtener clave VAPID
    const vapidPublicKey = await getVapidPublicKey();
    const convertedVapidKey = urlBase64ToUint8Array(vapidPublicKey);

    // Suscribirse
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: convertedVapidKey,
    });

    // Enviar al backend
    await fetch(`${API_URL}/api/notificaciones/subscriptions/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${token}`,
      },
      body: JSON.stringify({
        endpoint: subscription.endpoint,
        p256dh: arrayBufferToBase64(subscription.getKey('p256dh')),
        auth: arrayBufferToBase64(subscription.getKey('auth')),
        user_agent: navigator.userAgent,
      }),
    });

    console.log('✅ Suscrito a notificaciones push');
    return true;
  } catch (error) {
    console.error('Error al suscribirse:', error);
    return false;
  }
}

// Desuscribirse
export async function unsubscribeFromPushNotifications() {
  try {
    const registration = await navigator.serviceWorker.getRegistration();
    if (!registration) return;

    const subscription = await registration.pushManager.getSubscription();
    if (!subscription) return;

    await subscription.unsubscribe();
    console.log('✅ Desuscrito de notificaciones');
  } catch (error) {
    console.error('Error al desuscribirse:', error);
  }
}
```

### Service Worker

```javascript
// public/sw.js
self.addEventListener('push', (event) => {
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
      ],
    };

    event.waitUntil(
      self.registration.showNotification(data.title, options)
    );
  }
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'open' || !event.action) {
    const urlToOpen = event.notification.data.url || '/pedidos';
    event.waitUntil(
      clients.openWindow(urlToOpen)
    );
  }
});
```

### Integrar en App

```jsx
// src/App.jsx
import { useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { CartProvider } from './context/CartContext';
import { authService } from './services/auth';
import { subscribeToPushNotifications } from './services/pushNotifications';

// Pages
import Login from './pages/Login';
import Register from './pages/Register';
import Products from './pages/Products';
import Cart from './pages/Cart';
import Checkout from './pages/Checkout';
import Payment from './pages/Payment';
import MyOrders from './pages/MyOrders';

function App() {
  useEffect(() => {
    // Suscribirse a notificaciones si está autenticado
    if (authService.isAuthenticated()) {
      const token = localStorage.getItem('token');
      subscribeToPushNotifications(token);
    }
  }, []);

  return (
    <BrowserRouter>
      <CartProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/productos" element={<Products />} />
          <Route path="/carrito" element={<Cart />} />
          <Route path="/checkout" element={<Checkout />} />
          <Route path="/pago/:orderId" element={<Payment />} />
          <Route path="/pedidos" element={<MyOrders />} />
          <Route path="/" element={<Products />} />
        </Routes>
      </CartProvider>
    </BrowserRouter>
  );
}

export default App;
```

---

## 🚀 Despliegue en Vercel

### 1. Preparar proyecto

```bash
npm run build
```

### 2. Crear `vercel.json`

```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ],
  "headers": [
    {
      "source": "/sw.js",
      "headers": [
        {
          "key": "Service-Worker-Allowed",
          "value": "/"
        }
      ]
    }
  ]
}
```

### 3. Variables de entorno en Vercel

```
VITE_API_URL=https://tu-backend.com
VITE_STRIPE_PUBLIC_KEY=pk_live_...
```

### 4. Deploy

```bash
npm install -g vercel
vercel
```

---

## 📚 Resumen de Endpoints

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/usuarios/register/` | POST | Registrar usuario |
| `/api/usuarios/token/` | POST | Login (obtener token) |
| `/api/usuarios/me/` | GET | Obtener perfil |
| `/api/usuarios/me/` | PATCH | Actualizar perfil |
| `/api/productos/` | GET | Listar productos |
| `/api/productos/{id}/` | GET | Detalle de producto |
| `/api/productos/categorias/` | GET | Listar categorías |
| `/api/compra/compras/checkout/` | POST | Crear pedido |
| `/api/compra/compras/` | GET | Mis pedidos |
| `/api/compra/compras/{id}/` | GET | Detalle de pedido |
| `/api/compra/compras/{id}/pay/` | POST | Marcar como pagado |
| `/api/compra/compras/{id}/stripe_session/` | POST | Crear sesión Stripe |
| `/api/compra/compras/{id}/receipt/` | GET | Descargar comprobante |
| `/api/promociones/promociones/` | GET | Listar promociones |
| `/api/promociones/promociones/validar_codigo/` | GET | Validar cupón |
| `/api/notificaciones/vapid-public-key/` | GET | Obtener clave VAPID |
| `/api/notificaciones/subscriptions/` | POST | Suscribirse a push |

---

## ✅ Checklist Final

- [ ] Configurar `.env` con API_URL y Stripe
- [ ] Implementar AuthService con login/registro
- [ ] Crear CartContext para carrito local
- [ ] Implementar catálogo de productos
- [ ] Implementar página de checkout
- [ ] Implementar pago con Stripe
- [ ] Configurar Service Worker para push
- [ ] Suscribirse a notificaciones al login
- [ ] Implementar página "Mis Pedidos"
- [ ] Probar flujo completo en local con HTTPS
- [ ] Deploy en Vercel
- [ ] Configurar variables de entorno en Vercel

**¡Listo para implementar!** 🚀

