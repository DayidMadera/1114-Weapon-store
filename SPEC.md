# SPEC: Plataforma de Comercio Electrónico

## Programas y Tecnologías en Uso

* **Backend:** Python 3.x, Flask
* **Base de Datos:** SQL (PostgreSQL, MySQL o SQLite)
* **Frontend:** HTML5, JavaScript (ES6+), CSS3
* **Integración:** Jinja2 (Plantillas Flask) y JSON (API)

---

## Arquitectura del Sistema

* **Renderizado del Lado del Servidor (SSR):** Las páginas principales se renderizan con Flask y Jinja2 para optimizar velocidad y SEO.
* **Lógica del Lado del Cliente (CSR):** JavaScript se encarga de la interactividad dinámica (carrito de compras sin recargar la página, filtros y llamadas a la API).

---

## Funcionalidades Principales

### Módulo de Clientes (Frontend)
* **Catálogo de Productos:** Visualización de productos con imagen, título, descripción y precio.
* **Carrito de Compras:** Manejo dinámico de ítems y cantidades.
* **Autenticación:** Registro, inicio y cierre de sesión de usuarios.
* **Checkout:** Formulario de procesamiento y confirmación de orden.
* **Historial:** Perfil de usuario con compras realizadas.

### Módulo de Administración (Backend)
* **CRUD de las armas:** Crear, ver, editar y eliminar productos del catálogo.
* **Gestión de Inventario:** Descuento automático de stock al finalizar una compra.
* **Gestión de Órdenes:** Seguimiento de pedidos e historial global.

---

## Modelo de Datos (SQL)

### Tabla: Usuarios
* `id` (PK, INT, AUTO_INCREMENT)
* `nombre` (VARCHAR)
* `email` (VARCHAR, UNIQUE)
* `password_hash` (VARCHAR)
* `rol` (VARCHAR - 'admin' / 'cliente')

### Tabla: Armas
* `id` (PK, INT, AUTO_INCREMENT)
* `nombre` (VARCHAR)
* `descripcion` (TEXT)
* `precio` (DECIMAL)
* `stock` (INT)
* `imagen_url` (VARCHAR)

### Tabla: Ordenes
* `id` (PK, INT, AUTO_INCREMENT)
* `usuario_id` (FK, INT)
* `fecha_creacion` (DATETIME)
* `total` (DECIMAL)
* `estado` (VARCHAR - 'pendiente', 'pagada', 'enviada')

### Tabla: Detalles_Orden
* `id` (PK, INT, AUTO_INCREMENT)
* `orden_id` (FK, INT)
* `producto_id` (FK, INT)
* `cantidad` (INT)
* `precio_unitario` (DECIMAL)

---

## Estructura de Rutas (Flask)

### Vistas HTML (Jinja2)
* `GET /` - Catálogo principal
* `GET /producto/<id>` - Detalle de las armas
* `GET /carrito` - Página del carrito
* `GET /login` / `POST /login` - Autenticación
* `GET /registro` / `POST /registro` - Registro
* `GET /admin` - Panel de control de administración

### API Endpoints (JSON)
* `POST /api/carrito/agregar` - Agregar producto al carrito
* `POST /api/checkout` - Procesar la compra
* `GET /api/productos` - Obtener productos para filtros dinámicos

---

## Fases de Desarrollo

1. **Configuración e Infraestructura:** Setup de Flask, conexión SQL y modelos.
2. **Backend Core:** Rutas principales, autenticación y CRUD de productos.
3. **Frontend:** Plantillas HTML5 y Jinja2 para las vistas.
4. **Interactividad:** Lógica en JavaScript para el carrito y peticiones API.
5. **Pruebas y Despliegue:** Validación del flujo de compra.
