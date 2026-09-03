Product Requirements Document (PRD)
1. Información General
1.1 Nombre del proyecto

Multi-Vendor Checkout

1.2 Problema

Actualmente, cuando un usuario desea comprar un artículo del Vendedor A y otro del Vendedor B, debe realizar dos transacciones y procesos de pago independientes.

Esta experiencia genera una fricción significativa durante el proceso de compra, reduce el Ticket Promedio de Compra (AOV) y aumenta los costos asociados al procesamiento de pagos.

1.3 Solución

Implementar un carrito multi-vendedor que permita agrupar productos de diferentes tiendas dentro de una misma sesión de compra y procesar todos los productos mediante una única transacción.

Aunque el pago será único, los procesos logísticos y operativos continuarán siendo independientes para cada vendedor.

2. Objetivos de Negocio
2.1 KPIs
KPI	Objetivo
Ticket Promedio de Compra (AOV)	Incrementar 15%
Periodo de medición	Primeros 90 días
Abandono del carrito	Reducir 8%
2.2 Beneficios esperados
Reducir la fricción del proceso de checkout.
Aumentar la cantidad de productos por transacción.
Incrementar el valor promedio de cada compra.
Reducir operaciones de pago independientes.
Mejorar la experiencia de compra multi-vendedor.
3. Alcance
3.1 Incluido en Fase 1
Carrito con productos de múltiples vendedores.
Agrupación visual de productos por vendedor.
Cálculo independiente de costos de envío.
Cálculo independiente de tiempos estimados de entrega.
Checkout mediante una única transacción.
Validación de inventario.
Notificación independiente para cada vendedor.
Liquidación independiente del importe correspondiente a cada vendedor.
Eliminación individual de productos.
Funcionalidad "Guardar para más tarde".
3.2 Fuera de alcance

En esta fase no se permitirá consolidar los envíos de diferentes vendedores en un único paquete físico.

Si los vendedores se encuentran en ciudades diferentes:

Los productos se enviarán por separado.
Los costos de envío serán independientes.
Los tiempos de entrega serán independientes.
Cada vendedor gestionará su propio despacho.

El usuario verá un único pago, pero podrá recibir múltiples paquetes.

4. Historias de Usuario
US-01 — Carrito multi-vendedor

Como comprador, quiero agregar productos de diferentes tiendas a mi carrito para pagar todo junto en una sola transacción.

Criterios de aceptación
El usuario puede agregar productos de diferentes vendedores.
Los productos permanecen dentro del mismo carrito.
Los productos se agrupan visualmente por vendedor.
El usuario puede realizar un único proceso de checkout.
El pago se procesa mediante una única transacción.
US-02 — Desglose de envío

Como comprador, quiero ver el desglose de los costos de envío de cada vendedor antes de pagar para entender por qué varía el precio total.

Criterios de aceptación
Cada vendedor debe mostrar su costo de envío.
Cada vendedor debe mostrar su tiempo estimado de entrega.
El total del carrito debe incluir los costos de envío correspondientes.
El usuario debe poder identificar qué costo corresponde a cada vendedor.
US-03 — Operación independiente del vendedor

Como vendedor, quiero recibir la notificación de venta y el dinero de mi producto de forma independiente para gestionar mi propio inventario y facturación sin enredarme con otras tiendas.

Criterios de aceptación
Cada vendedor recibe una notificación de sus productos vendidos.
El vendedor recibe únicamente el importe que le corresponde.
La información de otros vendedores no debe mezclarse con su operación.
El inventario debe actualizarse de manera independiente.
La liquidación debe poder identificarse por vendedor.
5. Requisitos Funcionales
RF-01 — Interfaz del carrito agrupada por vendedor

La pantalla del carrito debe organizar visualmente los artículos según la tienda que los vende.

Criterios de aceptación
Debe mostrar el nombre del vendedor como encabezado.
Debajo del encabezado deben aparecer sus respectivos productos.
Cada grupo de vendedor debe mostrar su propio:
Costo de envío.
Tiempo de entrega estimado.
El usuario debe poder eliminar un producto individual.
El usuario debe poder guardar un producto para más tarde.
Las acciones realizadas sobre un producto no deben modificar los productos de otros vendedores.
RF-02 — Checkout multi-vendedor

El sistema debe permitir que productos pertenecientes a diferentes vendedores sean procesados mediante una única transacción.

Criterios de aceptación
El checkout debe recibir todos los productos válidos del carrito.
El sistema debe identificar a qué vendedor pertenece cada producto.
Debe calcularse el importe correspondiente a cada vendedor.
Debe calcularse el costo de envío de cada vendedor.
El comprador debe realizar un único pago.
RF-03 — Distribución de la venta

Después de completar el pago, el sistema debe separar internamente la operación por vendedor.

Criterios de aceptación
Cada vendedor debe recibir únicamente sus productos vendidos.
Cada vendedor debe recibir el importe correspondiente.
Los pedidos de cada vendedor deben poder gestionarse independientemente.
Un vendedor no debe tener acceso a información operativa de otros vendedores.
RF-04 — Validación de inventario

El sistema debe validar la disponibilidad de los productos durante el checkout.

Criterios de aceptación
El inventario debe verificarse antes de confirmar la transacción.
Si todos los productos están disponibles, el checkout puede continuar.
Si un producto deja de estar disponible, la transacción debe bloquearse.
El usuario debe regresar al carrito para modificar su compra.
6. Manejo de Errores
Producto agotado durante el checkout
Comportamiento esperado

Si un producto se agota mientras el usuario está realizando el checkout:

Bloquear la transacción.
Cancelar la confirmación del checkout.
Regresar al usuario a la pantalla del carrito.
Identificar visualmente el producto agotado.
Resaltar el producto en color rojo.
Mostrar el siguiente mensaje:

"El artículo de la tienda X ya no está disponible. Modifica tu carrito para continuar".

Resultado esperado

El usuario debe poder modificar su carrito y continuar con el proceso de compra sin tener que iniciar nuevamente toda la sesión.

7. Requisitos No Funcionales
RNF-01 — Rendimiento bajo carga

Durante eventos de alta demanda, como CyberMonday, el backend del carrito y checkout debe soportar:

50.000 peticiones de checkout concurrentes por minuto

sin que se produzcan caídas del servicio.

Criterio de aceptación

El sistema debe mantener disponibilidad y procesamiento correcto bajo la carga definida.

RNF-02 — Tiempo de respuesta

El cálculo y renderizado del subtotal de un carrito con múltiples vendedores no debe superar:

800 ms

Criterio de aceptación

El tiempo entre la solicitud del cálculo y la disponibilidad del subtotal para renderización debe ser ≤ 800 ms bajo condiciones normales de operación.

8. Flujo Principal
Usuario
   │
   ▼
Agrega producto del Vendedor A
   │
   ▼
Agrega producto del Vendedor B
   │
   ▼
Carrito Multi-Vendedor
   │
   ├── Vendedor A
   │     ├── Producto A1
   │     ├── Producto A2
   │     ├── Envío
   │     └── Tiempo de entrega
   │
   └── Vendedor B
         ├── Producto B1
         ├── Envío
         └── Tiempo de entrega
   │
   ▼
Checkout
   │
   ▼
Validación de inventario
   │
   ├── ❌ Producto agotado
   │       └── Regresar al carrito
   │
   └── ✅ Inventario disponible
           │
           ▼
      Pago único
           │
           ▼
    Distribución interna
       ┌───┴───┐
       ▼       ▼
  Vendedor A  Vendedor B
       │       │
       ▼       ▼
    Pedido    Pedido
    Envío     Envío
    Pago      Pago

9. Reglas de Negocio
Un carrito puede contener productos de múltiples vendedores.
Cada producto debe estar asociado a un único vendedor.
Cada vendedor mantiene su propia información logística.
Los costos de envío se calculan por vendedor.
Los tiempos de entrega se calculan por vendedor.
El comprador realiza un único pago.
La distribución contable de la transacción debe realizarse por vendedor.
El agotamiento de cualquier producto requerido para completar la compra debe impedir la confirmación del checkout.
Los envíos no se consolidan entre vendedores durante la Fase 1.
10. Criterios de Éxito

El lanzamiento será considerado exitoso si durante los primeros 90 días se alcanza:

+15% de incremento en AOV.
-8% de reducción en abandono del carrito.
Soporte de 50.000 peticiones de checkout concurrentes por minuto.
Tiempo de cálculo/renderizado del subtotal de ≤ 800 ms.
Correcta separación operativa y financiera de los pedidos por vendedor.
11. Fuera de Alcance Futuro

Las siguientes funcionalidades podrán considerarse en futuras fases:

Consolidación física de envíos.
Optimización automática de paquetes entre vendedores.
Agrupación logística por ciudad.
Optimización de costos de envío multi-vendedor.
Nuevas estrategias de distribución y liquidación financiera.
12. Versionado
Versión	Fecha	Estado
1.0	2026-09-03	Draft / Fase 1
13. Estado del Documento

Estado: Draft

Fase: 1

Última actualización: 2026-09-03
