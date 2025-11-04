# 🎁 Promociones y Devoluciones - Documentación Frontend

## 📋 Índice

1. [Promociones y Descuentos](#promociones-y-descuentos)
2. [Sistema de Devoluciones](#sistema-de-devoluciones)
3. [Garantías](#garantías)
4. [Flujos Completos](#flujos-completos)

---

## 🎁 Promociones y Descuentos

### 1. Listar Promociones Disponibles

**Endpoint:** `GET /api/promociones/promociones/`

**Query Params:**
- `vigentes=true` - Solo promociones vigentes

**Respuesta:**
```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "codigo": "VERANO2025",
      "nombre": "Descuento de Verano",
      "descripcion": "20% de descuento en toda la tienda",
      "tipo_descuento": "porcentaje",
      "valor_descuento": "20.00",
      "descuento_maximo": "100.00",
      "monto_minimo": "50.00",
      "fecha_inicio": "2025-01-01T00:00:00Z",
      "fecha_fin": "2025-12-31T23:59:59Z",
      "activa": true,
      "usos_maximos": 100,
      "usos_actuales": 15,
      "esta_vigente": true
    }
  ]
}
```

**Servicio React:**
```javascript
// src/services/promocionService.js
import api from '../api/axios';

export const getPromociones = async (vigentes = true) => {
  try {
    const params = vigentes ? { vigentes: 'true' } : {};
    const response = await api.get('/promociones/promociones/', { params });
    return { success: true, data: response.data.results };
  } catch (error) {
    return { success: false, error: error.response?.data };
  }
};
```

### 2. Validar Código de Promoción

**Endpoint:** `POST /api/promociones/promociones/validar/`

**Body:**
```json
{
  "codigo": "VERANO2025",
  "monto": 100.00
}
```

**Respuesta Exitosa:**
```json
{
  "valido": true,
  "promocion": {
    "id": 1,
    "codigo": "VERANO2025",
    "nombre": "Descuento de Verano",
    "tipo_descuento": "porcentaje",
    "valor_descuento": "20.00"
  },
  "monto_original": "100.00",
  "descuento": "20.00",
  "total_final": "80.00"
}
```

**Respuesta con Error:**
```json
{
  "detail": "La promoción no está vigente o ha alcanzado el límite de usos"
}
```

**Servicio React:**
```javascript
export const validarPromocion = async (codigo, monto) => {
  try {
    const response = await api.post('/promociones/promociones/validar/', {
      codigo: codigo.toUpperCase(),
      monto
    });
    return { success: true, data: response.data };
  } catch (error) {
    return { 
      success: false, 
      error: error.response?.data?.detail || 'Código inválido' 
    };
  }
};
```

### 3. Aplicar Promoción en Checkout

**Endpoint:** `POST /api/compra/compras/checkout/`

**Body con Promoción:**
```json
{
  "items": [
    {
      "producto": 1,
      "cantidad": 2
    }
  ],
  "observaciones": "Entrega rápida",
  "codigo_promocion": "VERANO2025"
}
```

**Respuesta:**
```json
{
  "id": 20,
  "cliente": 5,
  "fecha": "2025-10-28T10:00:00Z",
  "total": "80.00",
  "observaciones": "Entrega rápida",
  "promocion": 1,
  "promocion_codigo": "VERANO2025",
  "descuento_aplicado": "20.00",
  "esta_pagada": false,
  "items": [...]
}
```

**Componente de Checkout con Promoción:**
```jsx
// src/pages/Checkout.jsx
import { useState, useEffect } from 'react';
import { getCart, calculateTotal } from '../utils/cartUtils';
import { validarPromocion } from '../services/promocionService';
import { checkout } from '../services/checkoutService';

function Checkout() {
  const [cart] = useState(getCart());
  const [codigoPromocion, setCodigoPromocion] = useState('');
  const [promocionAplicada, setPromocionAplicada] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [subtotal, setSubtotal] = useState(0);
  const [totalFinal, setTotalFinal] = useState(0);

  useEffect(() => {
    const sub = parseFloat(calculateTotal());
    setSubtotal(sub);
    setTotalFinal(sub);
  }, [cart]);

  const handleValidarPromocion = async () => {
    if (!codigoPromocion.trim()) {
      setError('Ingrese un código de promoción');
      return;
    }

    setLoading(true);
    setError('');
    
    const result = await validarPromocion(codigoPromocion, subtotal);
    
    if (result.success) {
      setPromocionAplicada(result.data);
      setTotalFinal(parseFloat(result.data.total_final));
      setError('');
    } else {
      setError(result.error);
      setPromocionAplicada(null);
      setTotalFinal(subtotal);
    }
    
    setLoading(false);
  };

  const handleCheckout = async () => {
    setLoading(true);
    
    const result = await checkout({
      items: cart.map(item => ({
        producto: item.producto,
        cantidad: item.cantidad
      })),
      observaciones: '',
      codigo_promocion: promocionAplicada ? codigoPromocion : ''
    });
    
    if (result.success) {
      window.location.href = `/payment/${result.data.id}`;
    } else {
      setError(result.error);
    }
    
    setLoading(false);
  };

  return (
    <div className="checkout">
      <h1>Checkout</h1>
      
      {/* Lista de productos */}
      <div className="cart-items">
        {cart.map(item => (
          <div key={item.producto} className="cart-item">
            <h3>{item.nombre}</h3>
            <p>Cantidad: {item.cantidad} × ${item.precio}</p>
          </div>
        ))}
      </div>
      
      {/* Código de promoción */}
      <div className="promo-section">
        <h3>¿Tienes un código de promoción?</h3>
        <div className="promo-input-group">
          <input
            type="text"
            placeholder="Ej: VERANO2025"
            value={codigoPromocion}
            onChange={(e) => setCodigoPromocion(e.target.value.toUpperCase())}
            disabled={promocionAplicada !== null}
          />
          {!promocionAplicada ? (
            <button onClick={handleValidarPromocion} disabled={loading}>
              Aplicar
            </button>
          ) : (
            <button onClick={() => {
              setPromocionAplicada(null);
              setCodigoPromocion('');
              setTotalFinal(subtotal);
            }}>
              Quitar
            </button>
          )}
        </div>
        
        {promocionAplicada && (
          <div className="promo-success">
            ✓ Promoción "{promocionAplicada.promocion.nombre}" aplicada!
            Descuento: ${promocionAplicada.descuento}
          </div>
        )}
        
        {error && <div className="error">{error}</div>}
      </div>
      
      {/* Resumen */}
      <div className="summary">
        <div className="summary-line">
          <span>Subtotal:</span>
          <span>${subtotal.toFixed(2)}</span>
        </div>
        
        {promocionAplicada && (
          <div className="summary-line discount">
            <span>Descuento:</span>
            <span>-${promocionAplicada.descuento}</span>
          </div>
        )}
        
        <div className="summary-line total">
          <span>Total:</span>
          <span>${totalFinal.toFixed(2)}</span>
        </div>
      </div>
      
      <button 
        className="btn-checkout" 
        onClick={handleCheckout}
        disabled={loading || cart.length === 0}
      >
        {loading ? 'Procesando...' : 'Continuar al pago'}
      </button>
    </div>
  );
}

export default Checkout;
```

---

## 🔄 Sistema de Devoluciones

### Conceptos

El sistema usa **Patrón Estado** con 4 estados:

```
pendiente → aprobada → completada
    ↓
rechazada
```

**Tipos de devolución:**
- `devolucion`: Devolución con reembolso de dinero
- `cambio`: Cambio por otro producto

**Garantía:** 30 días desde la fecha de compra

### 1. Ver Mis Devoluciones

**Endpoint:** `GET /api/promociones/devoluciones/`

**Query Params:**
- `estado`: `pendiente`, `aprobada`, `rechazada`, `completada`
- `tipo`: `devolucion`, `cambio`

**Respuesta:**
```json
{
  "count": 2,
  "results": [
    {
      "id": 1,
      "compra_item": 15,
      "compra_item_info": {
        "id": 15,
        "producto_id": 3,
        "producto_nombre": "Laptop HP 15\"",
        "producto_sku": "LAPTOP001",
        "cantidad_comprada": 2,
        "precio_unitario": "850.00"
      },
      "cliente": 5,
      "cliente_nombre": "Juan Pérez",
      "tipo": "devolucion",
      "tipo_display": "Devolución con Reembolso",
      "estado": "pendiente",
      "estado_display": "Pendiente de Revisión",
      "motivo": "Producto defectuoso",
      "descripcion": "La pantalla tiene píxeles muertos",
      "cantidad": 1,
      "monto_reembolso": "850.00",
      "fecha_solicitud": "2025-10-28T09:00:00Z",
      "fecha_aprobacion": null,
      "fecha_rechazo": null,
      "fecha_completado": null,
      "respuesta_admin": "",
      "producto_reemplazo": null,
      "puede_cancelar": true,
      "dentro_garantia": true
    }
  ]
}
```

**Servicio:**
```javascript
// src/services/devolucionService.js
import api from '../api/axios';

export const getMisDevoluciones = async (estado = null) => {
  try {
    const params = estado ? { estado } : {};
    const response = await api.get('/promociones/devoluciones/', { params });
    return { success: true, data: response.data.results };
  } catch (error) {
    return { success: false, error: error.response?.data };
  }
};
```

### 2. Crear Solicitud de Devolución

**Endpoint:** `POST /api/promociones/devoluciones/`

**Body:**
```json
{
  "compra_item": 15,
  "tipo": "devolucion",
  "motivo": "Producto defectuoso",
  "descripcion": "La pantalla tiene píxeles muertos",
  "cantidad": 1
}
```

**Validaciones del Backend:**
- ✅ La compra debe estar pagada
- ✅ El producto debe pertenecer al cliente
- ✅ La cantidad no puede exceder la cantidad comprada
- ✅ Para cambios, debe estar dentro de garantía (30 días)

**Respuesta:**
```json
{
  "id": 1,
  "compra_item": 15,
  "tipo": "devolucion",
  "estado": "pendiente",
  "motivo": "Producto defectuoso",
  "cantidad": 1,
  "monto_reembolso": "850.00",
  "fecha_solicitud": "2025-10-28T09:00:00Z"
}
```

**Servicio:**
```javascript
export const crearDevolucion = async (data) => {
  try {
    const response = await api.post('/promociones/devoluciones/', data);
    return { success: true, data: response.data };
  } catch (error) {
    return { 
      success: false, 
      error: error.response?.data?.detail || 'Error al crear devolución' 
    };
  }
};
```

**Componente:**
```jsx
// src/components/CrearDevolucion.jsx
import { useState } from 'react';
import { crearDevolucion } from '../services/devolucionService';

function CrearDevolucion({ compraItem, onSuccess }) {
  const [formData, setFormData] = useState({
    tipo: 'devolucion',
    motivo: '',
    descripcion: '',
    cantidad: 1
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = await crearDevolucion({
      compra_item: compraItem.id,
      ...formData
    });

    if (result.success) {
      onSuccess(result.data);
    } else {
      setError(result.error);
    }

    setLoading(false);
  };

  return (
    <form onSubmit={handleSubmit} className="devolucion-form">
      <h3>Solicitar Devolución</h3>
      
      <div className="product-info">
        <p><strong>{compraItem.producto_nombre}</strong></p>
        <p>Cantidad comprada: {compraItem.cantidad}</p>
      </div>

      <div className="form-group">
        <label>Tipo de devolución</label>
        <select
          value={formData.tipo}
          onChange={(e) => setFormData({...formData, tipo: e.target.value})}
        >
          <option value="devolucion">Devolución con Reembolso</option>
          <option value="cambio">Cambio por otro Producto</option>
        </select>
      </div>

      <div className="form-group">
        <label>Cantidad a devolver</label>
        <input
          type="number"
          min="1"
          max={compraItem.cantidad}
          value={formData.cantidad}
          onChange={(e) => setFormData({...formData, cantidad: parseInt(e.target.value)})}
          required
        />
      </div>

      <div className="form-group">
        <label>Motivo</label>
        <input
          type="text"
          placeholder="Ej: Producto defectuoso"
          value={formData.motivo}
          onChange={(e) => setFormData({...formData, motivo: e.target.value})}
          required
        />
      </div>

      <div className="form-group">
        <label>Descripción detallada</label>
        <textarea
          placeholder="Describe el problema en detalle"
          value={formData.descripcion}
          onChange={(e) => setFormData({...formData, descripcion: e.target.value})}
          rows={4}
        />
      </div>

      {error && <div className="error">{error}</div>}

      <button type="submit" disabled={loading}>
        {loading ? 'Enviando...' : 'Enviar Solicitud'}
      </button>
    </form>
  );
}

export default CrearDevolucion;
```

### 3. Cancelar Solicitud

**Endpoint:** `POST /api/promociones/devoluciones/{id}/cancelar/`

**Condición:** Solo si `estado = "pendiente"`

**Respuesta:**
```json
{
  "detail": "Solicitud cancelada exitosamente",
  "devolucion": {
    "id": 1,
    "estado": "rechazada",
    "respuesta_admin": "Cancelada por el cliente"
  }
}
```

**Servicio:**
```javascript
export const cancelarDevolucion = async (devolucionId) => {
  try {
    const response = await api.post(`/promociones/devoluciones/${devolucionId}/cancelar/`);
    return { success: true, data: response.data };
  } catch (error) {
    return { 
      success: false, 
      error: error.response?.data?.detail || 'Error al cancelar' 
    };
  }
};
```

### 4. Ver Estado de Devolución

**Componente:**
```jsx
// src/components/EstadoDevolucion.jsx
function EstadoDevolucion({ devolucion }) {
  const getEstadoBadge = (estado) => {
    const colores = {
      pendiente: 'orange',
      aprobada: 'green',
      rechazada: 'red',
      completada: 'blue'
    };
    
    return (
      <span className={`badge badge-${colores[estado]}`}>
        {devolucion.estado_display}
      </span>
    );
  };

  const getTipoBadge = (tipo) => {
    return tipo === 'devolucion' ? '↩ Devolución' : '⇄ Cambio';
  };

  return (
    <div className="devolucion-card">
      <div className="devolucion-header">
        <h3>Solicitud #{devolucion.id}</h3>
        {getEstadoBadge(devolucion.estado)}
      </div>

      <div className="devolucion-body">
        <p><strong>Producto:</strong> {devolucion.compra_item_info.producto_nombre}</p>
        <p><strong>Tipo:</strong> {getTipoBadge(devolucion.tipo)}</p>
        <p><strong>Cantidad:</strong> {devolucion.cantidad}</p>
        <p><strong>Motivo:</strong> {devolucion.motivo}</p>
        {devolucion.descripcion && (
          <p><strong>Descripción:</strong> {devolucion.descripcion}</p>
        )}
        
        {devolucion.tipo === 'devolucion' && (
          <p><strong>Monto a reembolsar:</strong> ${devolucion.monto_reembolso}</p>
        )}

        <p><strong>Fecha de solicitud:</strong> {new Date(devolucion.fecha_solicitud).toLocaleDateString()}</p>

        {devolucion.respuesta_admin && (
          <div className="admin-response">
            <strong>Respuesta del administrador:</strong>
            <p>{devolucion.respuesta_admin}</p>
          </div>
        )}

        {/* Fechas de transición */}
        {devolucion.fecha_aprobacion && (
          <p><strong>Aprobada el:</strong> {new Date(devolucion.fecha_aprobacion).toLocaleDateString()}</p>
        )}
        {devolucion.fecha_completado && (
          <p><strong>Completada el:</strong> {new Date(devolucion.fecha_completado).toLocaleDateString()}</p>
        )}
        {devolucion.fecha_rechazo && (
          <p><strong>Rechazada el:</strong> {new Date(devolucion.fecha_rechazo).toLocaleDateString()}</p>
        )}
      </div>

      {devolucion.puede_cancelar && (
        <div className="devolucion-actions">
          <button 
            className="btn-cancel"
            onClick={() => handleCancelar(devolucion.id)}
          >
            Cancelar Solicitud
          </button>
        </div>
      )}
    </div>
  );
}
```

---

## ✅ Garantías

### Verificar Garantía

La garantía es de **30 días** desde la fecha de compra.

**Campo en respuesta:** `dentro_garantia: true/false`

**Ejemplo de validación:**
```javascript
const puedeDevolver = (compra, productoItem) => {
  const fechaCompra = new Date(compra.fecha);
  const hoy = new Date();
  const diasTranscurridos = Math.floor((hoy - fechaCompra) / (1000 * 60 * 60 * 24));
  
  return {
    dentroGarantia: diasTranscurridos <= 30,
    diasRestantes: Math.max(0, 30 - diasTranscurridos),
    puedeDevolver: compra.esta_pagada && diasTranscurridos <= 30
  };
};
```

**Componente de Info de Garantía:**
```jsx
function GarantiaInfo({ compra }) {
  const info = puedeDevolver(compra);
  
  return (
    <div className={`garantia-info ${info.dentroGarantia ? 'active' : 'expired'}`}>
      {info.dentroGarantia ? (
        <>
          <span className="icon">✓</span>
          <div>
            <strong>Garantía activa</strong>
            <p>{info.diasRestantes} días restantes para devoluciones</p>
          </div>
        </>
      ) : (
        <>
          <span className="icon">✗</span>
          <div>
            <strong>Garantía expirada</strong>
            <p>El período de devolución ha finalizado</p>
          </div>
        </>
      )}
    </div>
  );
}
```

---

## 🔄 Flujos Completos

### Flujo 1: Compra con Promoción

```
1. Cliente ve productos
2. Agrega al carrito
3. Va a checkout
4. Ingresa código "VERANO2025"
5. Valida promoción → Frontend muestra descuento
6. Confirma compra con promoción
7. Backend aplica descuento y crea compra
8. Redirige a pago
```

### Flujo 2: Solicitar Devolución

```
1. Cliente ve "Mis Compras"
2. Selecciona una compra pagada
3. Verifica garantía (30 días)
4. Selecciona producto a devolver
5. Llena formulario de devolución
6. Backend valida y crea solicitud (estado: pendiente)
7. Admin revisa y aprueba/rechaza
8. Si aprobada: Admin completa devolución
9. Backend restaura stock automáticamente
10. Cliente ve estado actualizado
```

### Flujo 3: Cambio de Producto

```
1. Cliente solicita cambio (tipo: "cambio")
2. Backend valida garantía
3. Admin aprueba
4. Admin selecciona producto de reemplazo
5. Admin completa cambio
6. Backend:
   - Restaura stock del producto original (+1)
   - Reduce stock del producto nuevo (-1)
7. Cliente recibe notificación
```

---

## 📊 Ejemplo de Página "Mis Compras" Completa

```jsx
// src/pages/MyOrders.jsx
import { useState, useEffect } from 'react';
import { getMyOrders } from '../services/orderService';
import { getMisDevoluciones } from '../services/devolucionService';
import CrearDevolucion from '../components/CrearDevolucion';
import EstadoDevolucion from '../components/EstadoDevolucion';
import GarantiaInfo from '../components/GarantiaInfo';

function MyOrders() {
  const [orders, setOrders] = useState([]);
  const [devoluciones, setDevoluciones] = useState([]);
  const [selectedItem, setSelectedItem] = useState(null);
  const [showDevolucionForm, setShowDevolucionForm] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    const ordersResult = await getMyOrders();
    const devolucionesResult = await getMisDevoluciones();
    
    if (ordersResult.success) setOrders(ordersResult.data);
    if (devolucionesResult.success) setDevoluciones(devolucionesResult.data);
  };

  const handleSolicitarDevolucion = (item) => {
    setSelectedItem(item);
    setShowDevolucionForm(true);
  };

  const handleDevolucionCreada = (nuevaDevolucion) => {
    setDevoluciones([nuevaDevolucion, ...devoluciones]);
    setShowDevolucionForm(false);
    alert('Solicitud de devolución creada exitosamente');
  };

  return (
    <div className="my-orders">
      <h1>Mis Compras</h1>

      {/* Lista de Compras */}
      <div className="orders-list">
        {orders.map(order => (
          <div key={order.id} className="order-card">
            <div className="order-header">
              <h3>Orden #{order.id}</h3>
              <span className={order.esta_pagada ? 'paid' : 'unpaid'}>
                {order.esta_pagada ? '✓ Pagada' : '⏳ Pendiente'}
              </span>
            </div>

            <GarantiaInfo compra={order} />

            <div className="order-items">
              {order.items.map(item => (
                <div key={item.id} className="order-item">
                  <div>
                    <strong>{item.producto_nombre}</strong>
                    <p>Cantidad: {item.cantidad} × ${item.precio_unitario}</p>
                  </div>
                  
                  {order.esta_pagada && puedeDevolver(order).puedeDevolver && (
                    <button 
                      onClick={() => handleSolicitarDevolucion(item)}
                      className="btn-devolucion"
                    >
                      Solicitar Devolución
                    </button>
                  )}
                </div>
              ))}
            </div>

            <div className="order-summary">
              {order.descuento_aplicado > 0 && (
                <p className="discount">
                  Promoción aplicada: -{order.promocion_codigo} 
                  (-${order.descuento_aplicado})
                </p>
              )}
              <p className="total">Total: ${order.total}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Lista de Devoluciones */}
      <h2>Mis Devoluciones</h2>
      <div className="devoluciones-list">
        {devoluciones.map(dev => (
          <EstadoDevolucion key={dev.id} devolucion={dev} />
        ))}
      </div>

      {/* Modal de Crear Devolución */}
      {showDevolucionForm && (
        <div className="modal">
          <div className="modal-content">
            <button 
              className="close" 
              onClick={() => setShowDevolucionForm(false)}
            >
              ×
            </button>
            <CrearDevolucion 
              compraItem={selectedItem} 
              onSuccess={handleDevolucionCreada}
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default MyOrders;
```

---

## 🎯 Estados del Sistema

### Estados de Devolución

| Estado | Descripción | Acciones del Cliente | Acciones del Admin |
|--------|-------------|---------------------|-------------------|
| **pendiente** | Solicitud recibida | Puede cancelar | Aprobar/Rechazar |
| **aprobada** | Admin aprobó | Solo ver | Completar devolución |
| **rechazada** | Admin rechazó | Solo ver | - |
| **completada** | Devolución finalizada | Solo ver | - |

### Tipos de Descuento

| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| **porcentaje** | % del monto | 20% → $100 → $20 descuento |
| **monto** | Cantidad fija | $50 → $100 → $50 descuento |

---

## ⚠️ Validaciones Importantes

### Promociones
- ✅ Debe estar activa
- ✅ Fecha dentro del rango (inicio-fin)
- ✅ No exceder usos máximos
- ✅ Monto mínimo cumplido

### Devoluciones
- ✅ Compra debe estar pagada
- ✅ Producto pertenece al cliente
- ✅ Cantidad ≤ cantidad comprada
- ✅ Garantía vigente (para cambios)
- ✅ Solo pendiente puede cancelarse

---

¡Listo! Con esta documentación tienes todo para implementar el sistema de promociones y devoluciones en tu frontend. 🚀
