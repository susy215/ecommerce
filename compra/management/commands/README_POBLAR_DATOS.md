# 📊 Comando Mejorado: poblar_datos

Comando mejorado para poblar la base de datos con datos de prueba **distribuidos inteligentemente en múltiples fechas**.

## 🚀 Características Nuevas

✅ **Distribución temporal inteligente**: Las compras se distribuyen de forma realista
✅ **Control total**: Define cantidad de compras y rango de fechas
✅ **Temporadas altas/bajas**: Simula variaciones estacionales
✅ **Estadísticas detalladas**: Muestra distribución mensual de ventas
✅ **Clientes frecuentes**: Algunos clientes compran más que otros
✅ **Días laborales**: 70% de compras en lunes-viernes
✅ **Variación de precios**: Precios históricos ligeramente diferentes
✅ **Estado de pago realista**: Compras antiguas tienen mayor probabilidad de estar pagadas

---

## 📖 Uso Básico

### Opción 1: Configuración por defecto (100 compras, 12 meses)

```bash
python manage.py poblar_datos
```

Esto creará:
- 10 categorías de electrodomésticos
- 24 productos variados
- 4 usuarios (1 admin + 3 clientes)
- 5 clientes (3 con usuario, 2 invitados)
- 3 promociones activas
- **100 compras distribuidas en los últimos 12 meses**

---

### Opción 2: Especificar número de compras

```bash
# Crear 200 compras en los últimos 12 meses
python manage.py poblar_datos --compras 200

# Crear 500 compras
python manage.py poblar_datos --compras 500

# Crear solo 50 compras
python manage.py poblar_datos --compras 50
```

---

### Opción 3: Controlar el rango de fechas

```bash
# Compras en los últimos 6 meses
python manage.py poblar_datos --meses 6

# Compras en los últimos 24 meses (2 años)
python manage.py poblar_datos --meses 24

# Compras en los últimos 3 meses
python manage.py poblar_datos --meses 3
```

---

### Opción 4: Especificar fecha de inicio

```bash
# Desde el 1 de enero de 2024
python manage.py poblar_datos --desde 2024-01-01

# Desde junio de 2024
python manage.py poblar_datos --desde 2024-06-01

# Desde hace 18 meses hasta hoy
python manage.py poblar_datos --desde 2023-05-01
```

---

### Opción 5: Combinar opciones

```bash
# 300 compras en los últimos 18 meses
python manage.py poblar_datos --compras 300 --meses 18

# 500 compras desde enero 2024
python manage.py poblar_datos --compras 500 --desde 2024-01-01

# 1000 compras en el último año
python manage.py poblar_datos --compras 1000 --meses 12
```

---

### Opción 6: Limpiar y repoblar

```bash
# ⚠️ CUIDADO: Esto elimina TODOS los datos existentes
python manage.py poblar_datos --limpiar

# Limpiar y crear 250 compras en 6 meses
python manage.py poblar_datos --limpiar --compras 250 --meses 6
```

---

## 📊 Ejemplo de Salida

```
Iniciando población de datos...
Creando categorías...
Creando productos...
Creando usuarios...
Creando clientes...
Creando promociones...
Creando 200 compras históricas en 12 meses...

  ✓ Creadas 200 compras históricas
  ✓ Compras pagadas: 172 (86.0%)
  ✓ Total en ventas pagadas: $89,456.78

  📊 Distribución mensual:
     2024-01:  10 compras | Total: $  3,245.67 | Promedio: $  324.57
     2024-02:  12 compras | Total: $  4,123.89 | Promedio: $  343.66
     2024-03:  18 compras | Total: $  7,234.12 | Promedio: $  401.90
     2024-04:  14 compras | Total: $  5,678.34 | Promedio: $  405.60
     2024-05:  16 compras | Total: $  6,890.45 | Promedio: $  430.65
     2024-06:  22 compras | Total: $  9,123.78 | Promedio: $  414.72
     2024-07:  18 compras | Total: $  7,456.23 | Promedio: $  414.23
     2024-08:  20 compras | Total: $  8,234.56 | Promedio: $  411.73
     2024-09:  24 compras | Total: $ 10,567.89 | Promedio: $  440.33
     2024-10:  19 compras | Total: $  8,901.34 | Promedio: $  468.49
     2024-11:  21 compras | Total: $  9,876.54 | Promedio: $  470.31
     2024-12:   6 compras | Total: $  8,123.97 | Promedio: $1,353.99

✅ Datos poblados exitosamente!

📋 Resumen:
  - Categorías: 10
  - Productos: 24
  - Usuarios: 4
  - Clientes: 5
  - Compras: 200
  - Promociones: 3

🔑 Credenciales:
  - Admin: admin / admin
  - Cliente: cliente1 / cliente1
```

---

## 🎯 Casos de Uso Recomendados

### Para Desarrollo Local
```bash
python manage.py poblar_datos --compras 50 --meses 3
```

### Para Testing/QA
```bash
python manage.py poblar_datos --compras 200 --meses 6
```

### Para Demo/Presentaciones
```bash
python manage.py poblar_datos --limpiar --compras 300 --meses 12
```

### Para Probar Reportes Anuales
```bash
python manage.py poblar_datos --compras 1000 --meses 24 --desde 2023-01-01
```

### Para Análisis de IA/Predicciones
```bash
# Necesitas muchos datos históricos
python manage.py poblar_datos --compras 2000 --meses 24
```

---

## 🔍 Detalles de la Distribución

### Distribución Temporal
- **Más ventas en meses recientes**: Los meses más cercanos tienen más peso
- **Temporadas altas**: Cada 3 meses hay un pico de ventas
- **Días laborales**: 70% de las compras ocurren de lunes a viernes
- **Horas de trabajo**: Entre 8:00 AM y 8:00 PM

### Clientes
- **30% son clientes frecuentes**: Algunos clientes compran más seguido
- **70% son clientes ocasionales**: Compran menos frecuentemente

### Productos por Compra
- **40%** compra 1 producto
- **30%** compra 2-3 productos  
- **30%** compra 4-7 productos

### Cantidades
- **Productos caros** (>$500): Solo 1 unidad
- **Productos medianos** ($200-$500): 1-2 unidades
- **Productos baratos** (<$200): 1-4 unidades

### Promociones
- **30%** de las compras tienen promoción aplicada
- Se validan montos mínimos y fechas de vigencia

### Estado de Pago
- **85-95%** de compras están pagadas (más antiguas = mayor %)
- **5-15%** están pendientes de pago
- Pago ocurre entre 0-3 días después de la compra

### Precios Históricos
- **20%** de productos tienen variación de precio (±5%)
- Simula cambios de precio en el tiempo

---

## ⚠️ Notas Importantes

1. **No afecta usuarios superadmin**: El comando no elimina usuarios con `is_superuser=True`

2. **Flag --limpiar es destructivo**: Elimina:
   - Todas las compras
   - Todos los items de compra
   - Todos los clientes
   - Todos los productos
   - Todas las categorías
   - Todas las promociones
   - Usuarios no-superadmin

3. **Requiere base de datos vacía o con pocos datos**: Si ya tienes datos, usa `--limpiar` con cuidado

4. **Stock de productos**: El comando no reduce stock (para permitir múltiples ejecuciones)

---

## 🔗 Comandos Relacionados

```bash
# Ver todos los comandos disponibles
python manage.py help

# Generar claves VAPID
python manage.py generate_vapid_keys

# Crear superusuario
python manage.py createsuperuser

# Hacer migraciones
python manage.py migrate

# Recolectar archivos estáticos
python manage.py collectstatic
```

---

## 🐛 Troubleshooting

### Error: "relation does not exist"
```bash
# Ejecutar migraciones primero
python manage.py migrate
```

### Error: "Promocion has no attribute 'esta_vigente'"
El modelo `Promocion` necesita tener el método `esta_vigente()`. Verifica que exista.

### Error: "Compra has no attribute 'aplicar_promocion'"
El modelo `Compra` necesita tener el método `aplicar_promocion()`. Verifica que exista.

### Muy lento al crear muchas compras
Es normal. Crear 1000+ compras puede tomar varios minutos debido a todas las relaciones.

---

## 📈 Próximas Mejoras Planeadas

- [ ] Soporte para múltiples monedas
- [ ] Devoluciones automáticas (5% de compras)
- [ ] Envíos y tracking
- [ ] Reviews de productos
- [ ] Wishlist de clientes
- [ ] Carritos abandonados

---

**¡Disfruta poblando tu base de datos!** 🎉

