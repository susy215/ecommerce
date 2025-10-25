# SmartSales365 – Guía para Frontend (API contract)

Esta guía define exactamente qué endpoints existen, cómo autenticarse, cómo paginar/filtrar y cómo manejar errores. Úsala tal cual para no inventar APIs ni paginaciones.

Base URL (dev): http://localhost:8000

- Documentación interactiva: GET /api/docs/
- OpenAPI JSON: GET /api/schema/

Todos los endpoints devuelven y reciben JSON. Cabeceras recomendadas:
- Content-Type: application/json
- Accept: application/json

Autenticación
- Tipo: Token
- Header: Authorization: Token <token>
- Endpoints abiertos: /api/usuarios/register/, /api/usuarios/token/, /api/docs, /api/schema

---

## Autenticación y usuarios

1) Obtener token (username o email)
- POST /api/usuarios/token/
- Body:
  {
    "username": "user123",   // o usa "email": "user@dominio.com"
    "password": "tu_clave"
  }
- Respuesta 200:
  { "token": "<TOKEN>" }
- Errores: 400 {"detail": "Credenciales inválidas"}

2) Registro público
- POST /api/usuarios/register/
- Body:
  {
    "username": "user123",
    "email": "user@dominio.com",
    "password": "...",
    "first_name": "Nombre",
    "last_name": "Apellido",
    "telefono": "..."
  }
- Respuesta 201: objeto usuario sin password

3) Perfil del usuario autenticado
- GET /api/usuarios/me/
- PATCH /api/usuarios/me/ (editar datos básicos; campos de rol/permiso NO se pueden cambiar)

Notas
- Usa siempre el token en Authorization tras login/registro para el resto de llamadas.

---

## Categorías y productos

1) Listar categorías
- GET /api/productos/categorias/
- Autenticación: requerida
- Respuesta 200 (paginada):
  {
    "count": 3,
    "next": null,
    "previous": null,
    "results": [
      {"id": 1, "nombre": "Ropa", "slug": "ropa"},
      ...
    ]
  }

2) Listar productos (con filtros)
- GET /api/productos/?page=1&search=camisa&ordering=precio&categoria=1
- Autenticación: requerida
- Filtros soportados:
  - search: busca en sku, nombre, descripcion
  - ordering: nombre | precio | stock | fecha_creacion (agrega - para descendente, ej: -precio)
  - categoria: id de categoría
- Usuarios no admin solo ven productos con "activo": true
- Respuesta 200 (paginada):
  {
    "count": 25,
    "next": "...page=2",
    "previous": null,
    "results": [
      {
        "id": 10,
        "sku": "SKU-001",
        "nombre": "Camisa Azul",
        "descripcion": "...",
        "precio": "49.99",
        "stock": 50,
        "activo": true,
        "categoria": {"id":1, "nombre":"Ropa", "slug":"ropa"},
        "fecha_creacion": "2025-10-25T10:00:00Z",
        "fecha_actualizacion": "2025-10-25T10:00:00Z"
      }
    ]
  }

3) Detalle de producto
- GET /api/productos/{id}/

Notas
- Crear/editar/eliminar categorías y productos es solo para admin.

---

## Carrito, checkout y pagos

El carrito vive en el frontend (localStorage/estado). El backend solo recibe el pedido final en un único endpoint "checkout" y crea la compra con los items. Para el pago, se integra Stripe Checkout; también queda un endpoint de pago manual como respaldo.

1) Checkout (crear compra)
- POST /api/compra/compras/checkout/
- Autenticación: requerida (si no hay sesión, pide login antes de este paso)
- Body:
  {
    "items": [
      { "producto": 10, "cantidad": 2 },
      { "producto": 15, "cantidad": 1 }
    ],
    "observaciones": "Entregar por la tarde"
  }
- Reglas:
  - El precio_unitario se toma SIEMPRE del producto en el servidor (no se confía en el cliente)
  - cantidad > 0
  - productos deben existir y estar activos
- Respuesta 201:
  {
    "id": 123,
    "cliente": 45,
    "fecha": "2025-10-25T10:05:00Z",
    "total": "149.97",
    "observaciones": "Entregar por la tarde",
    "pago_referencia": "",
    "pagado_en": null,
    "items": [
      {
        "id": 1,
        "producto": 10,
        "producto_nombre": "Camisa Azul",
        "cantidad": 2,
        "precio_unitario": "49.99",
        "subtotal": "99.98"
      },
      {
        "id": 2,
        "producto": 15,
        "producto_nombre": "Pantalón Negro",
        "cantidad": 1,
        "precio_unitario": "49.99",
        "subtotal": "49.99"
      }
    ]
  }
- Errores 400:
  - {"detail": "Items requeridos"}
  - {"detail": "Formato de item inválido"}
  - {"detail": "Cantidad debe ser mayor a 0"}
  - {"detail": "Producto {id} no existe o inactivo"}

2) Crear sesión de pago (Stripe Checkout)
- POST /api/compra/compras/{id}/stripe_session/
- Autenticación: requerida (dueño o admin)
- Body opcional:
  {
    "success_url": "https://midominio.com/checkout/success?compra=123",
    "cancel_url": "https://midominio.com/checkout/cancel?compra=123"
  }
  Si no se envían, el backend usa FRONTEND_URL del servidor (por defecto http://localhost:5173).
- Respuesta 200:
  { "id": "cs_test_a1...", "url": "https://checkout.stripe.com/c/pay/cs_test_a1..." }
- Uso en frontend:
  - Redirige al usuario a la URL recibida (window.location.href = response.url)
  - Al completar el pago, Stripe redirige a success_url; el backend marcará la compra como pagada vía webhook.
- Posibles errores:
  - 400 {"detail": "La compra debe tener items y total > 0"}
  - 500 {"detail": "Falta STRIPE_API_KEY en el servidor"} (revisar configuración)

3) Descargar comprobante (PDF)
- GET /api/compra/compras/{id}/receipt/
- Autenticación: requerida (dueño o admin)
- Respuesta 200: application/pdf (adjunto)

4) Pago manual (respaldo/opcional)
- POST /api/compra/compras/{id}/pay/
- Autenticación: requerida
- Body: { "referencia": "transfer_123" }
- Respuesta 200: compra actualizada con pago_referencia y pagado_en
- Errores 400:
  - {"detail": "El total debe ser mayor a 0"}
  - {"detail": "La compra ya está pagada"}
  - {"detail": "Referencia de pago requerida"}

5) Mis compras
- GET /api/compra/compras/?page=1&ordering=-fecha
- Autenticación: requerida
- Respuesta: listado paginado de compras del usuario

6) Detalle de compra
- GET /api/compra/compras/{id}/
- Autenticación: requerida (solo dueño o admin)

Notas importantes
- No existe CRUD de items desde el frontend. El único lugar donde se envían items es en checkout.
- Si el usuario no tiene perfil de Cliente, el backend lo crea automáticamente al hacer checkout.
- Para guest checkout (sin login) NO está implementado en esta versión.
- No necesitas llamar al webhook de Stripe: el servidor lo expone en /api/compra/stripe/webhook/ y Stripe lo invoca automáticamente.

---

## Clientes (opcional front)

En general no necesitas tocar clientes; el backend asigna el cliente automáticamente al checkout.
- Rutas disponibles: /api/clientes/ (CRUD estándar DRF)
- Visibilidad: un usuario normal ve solo sus clientes (normalmente uno); admin ve todos.

---

## Reportes (uso admin)

- GET /api/reportes/summary/
- Autenticación: requerida (ideal admin)
- Respuesta 200:
  {
    "ventas_count": 12,              // número de compras (terminología histórica)
    "productos_count": 50,
    "clientes_count": 8,
    "total_ventas": "1234.50",
    "ultimas_ventas": [
      {"id": 123, "cliente__nombre": "Juan Perez", "fecha": "2025-10-25T10:05:00Z", "total": "149.97"}
    ]
  }

---

## Paginación, búsqueda y ordenamiento

- Paginación por defecto: PageNumberPagination (20 items por página)
- Parámetros:
  - page: número de página (1 por defecto)
  - search: texto de búsqueda (en endpoints que lo soportan, p.ej. productos)
  - ordering: campo para ordenar; usa prefijo '-' para descendente
- Respuesta paginada estándar DRF:
  {
    "count": <int>,
    "next": <url|null>,
    "previous": <url|null>,
    "results": [ ... ]
  }

---

## Manejo de errores (estándar DRF)

- 400 Bad Request (validación):
  - {"detail": "mensaje"}
  - o bien {"campo": ["error 1", "error 2"]}
- 401 Unauthorized: token ausente o inválido
- 403 Forbidden: sin permisos (p.ej., ver compra de otro usuario)
- 404 Not Found: recurso inexistente

Ejemplo de validación de campos:
{
  "email": ["Enter a valid email address."],
  "password": ["This password is too short."]
}

---

## Flujo recomendado en el frontend

1) Usuario navega categorías y productos (con search/ordering)
2) Añade productos al carrito (solo en frontend)
3) En checkout:
  - Si no está logueado: mostrar login (POST /api/usuarios/token/)
  - Con token: POST /api/compra/compras/checkout/ con items
4) Crear sesión de pago: POST /api/compra/compras/{id}/stripe_session/ y redirigir a response.url
5) Stripe redirige a success_url; el backend marca la compra como pagada vía webhook
6) Mostrar detalle de compra; ofrecer "Descargar comprobante" (GET /api/compra/compras/{id}/receipt/)

Cosas que NO implementar en el front:
- CRUD de items contra el backend (no existe)
- Estados complejos de pedido (no existen)
- Carrito en el backend (vive en el front)

---

## Ejemplo rápido de uso (pseudo)

// Login
POST /api/usuarios/token/ -> token

// Listar categorías y productos
GET /api/productos/categorias/
GET /api/productos/?categoria=1&search=camisa&ordering=-precio

// Checkout
POST /api/compra/compras/checkout/
{
  "items": [ {"producto": 10, "cantidad": 2} ],
  "observaciones": "..."
}
-> Respuesta incluye id de compra y total

// Crear sesión de pago (Stripe)
POST /api/compra/compras/{id}/stripe_session/
-> { "url": "https://checkout.stripe.com/c/pay/..." }
// Redirigir en el frontend a esa URL

---

Notas finales
- Si necesitas un endpoint de "guest checkout", se puede agregar luego; hoy todo el checkout requiere usuario autenticado.
- Para probar rápidamente, usa /api/docs/ (Swagger) y pega el token en el botón Authorize.
- Configuración en servidor: STRIPE_SECRET_KEY (secreta, sk_...), STRIPE_PUBLISHABLE_KEY (opcional para frontend, pk_...), STRIPE_WEBHOOK_SECRET, STRIPE_CURRENCY (opcional), FRONTEND_URL.
