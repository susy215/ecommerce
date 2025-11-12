# 🏆 Rankings de Rendimiento - Documentación Frontend

## 📋 **RESUMEN EJECUTIVO**

Esta documentación explica cómo integrar **Rankings de Rendimiento** en tu dashboard administrativo de React. Los rankings muestran métricas de rendimiento de productos, clientes y categorías para análisis competitivo.

## 🎯 **LO QUE OBTIENES**

- ✅ **Top productos** más vendidos con métricas detalladas
- ✅ **Top clientes** más activos y rentables
- ✅ **Top categorías** más rentables
- ✅ **Producto estrella** y **cliente estrella** del período
- ✅ **Métricas generales** de rendimiento
- ✅ **Filtros por período** (días personalizables)

## 🌐 **ENDPOINT API**

```javascript
// URL del endpoint
const API_URL = '/api/reportes/rankings/rendimiento/';

// Con parámetros
const params = new URLSearchParams({
  dias: 30,    // Período en días (default: 30)
  limit: 10    // Número de items por ranking (default: 10)
});

fetch(`/api/reportes/rankings/rendimiento/?${params}`)
  .then(r => r.json())
  .then(data => console.log(data));
```

## 🔐 **AUTENTICACIÓN**

Requiere **Bearer token** en headers:

```javascript
const headers = {
  'Authorization': `Bearer ${localStorage.getItem('token')}`,
  'Content-Type': 'application/json',
};
```

## 📊 **ESTRUCTURA DE RESPUESTA**

### **Respuesta Completa:**

```javascript
{
  "periodo_dias": 30,
  "fecha_inicio": "2025-11-01",
  "fecha_fin": "2025-12-01",

  // Rankings principales
  "productos_mas_vendidos": [
    {
      "ranking": 1,
      "nombre": "Producto Estrella",
      "sku": "PROD-001",
      "categoria": "Electrónicos",
      "unidades_vendidas": 150,
      "ingresos_totales": 45000.00,
      "precio_promedio": 300.00
    }
  ],

  "clientes_mas_activos": [
    {
      "ranking": 1,
      "nombre": "Juan Pérez",
      "email": "juan@email.com",
      "total_compras": 25000.00,
      "numero_ordenes": 25,
      "promedio_por_orden": 1000.00
    }
  ],

  "categorias_mas_rentables": [
    {
      "ranking": 1,
      "nombre": "Electrónicos",
      "unidades_vendidas": 500,
      "ingresos_totales": 150000.00,
      "productos_en_categoria": 25
    }
  ],

  // Métricas destacadas
  "metricas_generales": {
    "total_ventas": 500000.00,
    "total_ordenes": 500,
    "total_productos_vendidos": 1500,
    "promedio_por_orden": 1000.00
  },

  // Estrellas del período
  "producto_estrella": {
    "nombre": "Producto Estrella",
    "sku": "PROD-001",
    "categoria": "Electrónicos",
    "unidades_vendidas": 150,
    "ingresos_generados": 45000.00
  },

  "cliente_estrella": {
    "nombre": "Juan Pérez",
    "email": "juan@email.com",
    "total_compras": 25000.00,
    "numero_ordenes": 25
  }
}
```

## 🎨 **IMPLEMENTACIÓN EN REACT**

### **Hook personalizado: `useRankingsRendimiento.js`**

```javascript
import { useState, useEffect, useCallback } from 'react';

export const useRankingsRendimiento = (dias = 30, limit = 10) => {
  const [rankings, setRankings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchRankings = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('token') || localStorage.getItem('auth_token');
      if (!token) {
        setError('No hay token de autenticación');
        return;
      }

      const params = new URLSearchParams({ dias, limit });
      const response = await fetch(`/api/reportes/rankings/rendimiento/?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setRankings(data);
      } else if (response.status === 401) {
        setError('No autorizado - verifica tu sesión');
      } else {
        setError(`Error del servidor: ${response.status}`);
      }
    } catch (error) {
      console.error('Error fetching rankings:', error);
      setError('Error de conexión');
    } finally {
      setLoading(false);
    }
  }, [dias, limit]);

  useEffect(() => {
    fetchRankings();
  }, [fetchRankings]);

  return {
    rankings,
    loading,
    error,
    refetch: fetchRankings,
  };
};
```

### **Componente de Rankings: `RankingsRendimiento.jsx`**

```javascript
import React from 'react';
import { useRankingsRendimiento } from './hooks/useRankingsRendimiento';

const RankingsRendimiento = ({ dias = 30, limit = 10 }) => {
  const { rankings, loading, error, refetch } = useRankingsRendimiento(dias, limit);

  if (loading) {
    return <div className="loading">Cargando rankings...</div>;
  }

  if (error) {
    return (
      <div className="error">
        Error: {error}
        <button onClick={refetch}>Reintentar</button>
      </div>
    );
  }

  if (!rankings) {
    return <div>No hay datos disponibles</div>;
  }

  return (
    <div className="rankings-rendimiento">
      {/* Header con período */}
      <div className="rankings-header">
        <h2>🏆 Rankings de Rendimiento</h2>
        <p>Período: {rankings.fecha_inicio} - {rankings.fecha_fin}</p>
        <button onClick={refetch} className="refresh-btn">🔄 Actualizar</button>
      </div>

      {/* Métricas generales */}
      <div className="metricas-generales">
        <div className="metrica-card">
          <h3>Total Ventas</h3>
          <span className="valor">${rankings.metricas_generales.total_ventas.toLocaleString()}</span>
        </div>
        <div className="metrica-card">
          <h3>Total Órdenes</h3>
          <span className="valor">{rankings.metricas_generales.total_ordenes}</span>
        </div>
        <div className="metrica-card">
          <h3>Productos Vendidos</h3>
          <span className="valor">{rankings.metricas_generales.total_productos_vendidos}</span>
        </div>
        <div className="metrica-card">
          <h3>Promedio por Orden</h3>
          <span className="valor">${rankings.metricas_generales.promedio_por_orden.toFixed(2)}</span>
        </div>
      </div>

      {/* Estrellas del período */}
      <div className="estrellas-periodo">
        {rankings.producto_estrella && (
          <div className="estrella-card">
            <h3>⭐ Producto Estrella</h3>
            <p>{rankings.producto_estrella.nombre}</p>
            <small>{rankings.producto_estrella.unidades_vendidas} unidades vendidas</small>
          </div>
        )}

        {rankings.cliente_estrella && (
          <div className="estrella-card">
            <h3>👑 Cliente Estrella</h3>
            <p>{rankings.cliente_estrella.nombre}</p>
            <small>{rankings.cliente_estrella.numero_ordenes} órdenes realizadas</small>
          </div>
        )}
      </div>

      <div className="rankings-grid">
        {/* Productos más vendidos */}
        <div className="ranking-section">
          <h3>📦 Top Productos Más Vendidos</h3>
          <div className="ranking-list">
            {rankings.productos_mas_vendidos.map(producto => (
              <div key={producto.ranking} className="ranking-item">
                <div className="ranking-number">#{producto.ranking}</div>
                <div className="ranking-content">
                  <h4>{producto.nombre}</h4>
                  <p>{producto.sku} • {producto.categoria}</p>
                  <div className="ranking-metrics">
                    <span>{producto.unidades_vendidas} unidades</span>
                    <span>${producto.ingresos_totales.toLocaleString()}</span>
                    <span>${producto.precio_promedio.toFixed(2)} promedio</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Clientes más activos */}
        <div className="ranking-section">
          <h3>👥 Top Clientes Más Activos</h3>
          <div className="ranking-list">
            {rankings.clientes_mas_activos.map(cliente => (
              <div key={cliente.ranking} className="ranking-item">
                <div className="ranking-number">#{cliente.ranking}</div>
                <div className="ranking-content">
                  <h4>{cliente.nombre}</h4>
                  <p>{cliente.email}</p>
                  <div className="ranking-metrics">
                    <span>{cliente.numero_ordenes} órdenes</span>
                    <span>${cliente.total_compras.toLocaleString()}</span>
                    <span>${cliente.promedio_por_orden.toFixed(2)} promedio</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Categorías más rentables */}
        <div className="ranking-section">
          <h3>🏷️ Top Categorías Más Rentables</h3>
          <div className="ranking-list">
            {rankings.categorias_mas_rentables.map(categoria => (
              <div key={categoria.ranking} className="ranking-item">
                <div className="ranking-number">#{categoria.ranking}</div>
                <div className="ranking-content">
                  <h4>{categoria.nombre}</h4>
                  <p>{categoria.productos_en_categoria} productos en categoría</p>
                  <div className="ranking-metrics">
                    <span>{categoria.unidades_vendidas} unidades</span>
                    <span>${categoria.ingresos_totales.toLocaleString()}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default RankingsRendimiento;
```

## 🎨 **ESTILOS CSS RECOMENDADOS**

```css
.rankings-rendimiento {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.rankings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.rankings-header h2 {
  margin: 0;
  color: #2c3e50;
}

.refresh-btn {
  background: #3498db;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
}

.metricas-generales {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.metrica-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  text-align: center;
}

.metrica-card h3 {
  margin: 0 0 10px 0;
  color: #7f8c8d;
  font-size: 14px;
  text-transform: uppercase;
}

.metrica-card .valor {
  font-size: 24px;
  font-weight: bold;
  color: #2c3e50;
}

.estrellas-periodo {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.estrella-card {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
}

.rankings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 30px;
}

.ranking-section h3 {
  color: #2c3e50;
  margin-bottom: 20px;
  border-bottom: 2px solid #3498db;
  padding-bottom: 10px;
}

.ranking-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ranking-item {
  display: flex;
  align-items: center;
  background: white;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 1px 5px rgba(0,0,0,0.1);
  transition: transform 0.2s;
}

.ranking-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0,0,0,0.15);
}

.ranking-number {
  background: #3498db;
  color: white;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  margin-right: 15px;
  flex-shrink: 0;
}

.ranking-content h4 {
  margin: 0 0 5px 0;
  color: #2c3e50;
}

.ranking-content p {
  margin: 0 0 10px 0;
  color: #7f8c8d;
  font-size: 14px;
}

.ranking-metrics {
  display: flex;
  gap: 15px;
  font-size: 12px;
  color: #27ae60;
  font-weight: 500;
}

.error {
  background: #e74c3c;
  color: white;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #7f8c8d;
}
```

## 🔧 **PERSONALIZACIÓN**

### **Cambiar período:**
```javascript
// Últimos 7 días
const { rankings } = useRankingsRendimiento(7, 10);

// Últimos 90 días
const { rankings } = useRankingsRendimiento(90, 20);
```

### **Cambiar límite:**
```javascript
// Top 5 en lugar de top 10
const { rankings } = useRankingsRendimiento(30, 5);
```

## 📱 **RESPONSIVE DESIGN**

Los estilos CSS incluyen `grid-template-columns: repeat(auto-fit, minmax(350px, 1fr))` para adaptarse automáticamente a diferentes tamaños de pantalla.

## 🎯 **USO EN DASHBOARD**

```javascript
// En tu dashboard principal
import RankingsRendimiento from './components/RankingsRendimiento';

function Dashboard() {
  return (
    <div>
      <h1>Dashboard Administrativo</h1>
      
      {/* KPIs existentes */}
      <KPIsSection />
      
      {/* NUEVO: Rankings de Rendimiento */}
      <RankingsRendimiento dias={30} limit={10} />
      
      {/* Otros componentes */}
      <ChartsSection />
    </div>
  );
}
```

## 🚀 **DEPLOYMENT**

1. **Backend**: Ya está implementado y listo
2. **Frontend**: Copia el hook y componente
3. **¡Funciona inmediatamente!**

## 📞 **SOPORTE**

Si necesitas ayuda:
- Verifica que el token JWT sea válido
- Confirma que tengas permisos de admin/vendedor
- Revisa la consola del navegador para errores

¡Los Rankings de Rendimiento están listos para usar! 🏆
