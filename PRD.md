PRD
Información General y Contexto
El Problema: Actualmente, si un usuario quiere comprar un artículo del Vendedor A y otro del Vendedor B, debe realizar dos transacciones y procesos de pago independientes. Esto genera una fricción enorme, disminuye el ticket promedio de compra en un 24% e incrementa los costos de procesamiento de las pasarelas de pago.Meta de Negocio (KPIs):Incrementar el Ticket Promedio de Compra (AOV) en un 15% en los primeros 90 días tras el lanzamiento.Reducir la tasa de abandono del carrito de compras en un 8%.Fuera de Alcance (Out of Scope): En esta Fase 1, el sistema no permitirá consolidar los envíos en un solo paquete físico si los vendedores están en ciudades distintas. Los envíos se calcularán y despacharán por separado, aunque el pago sea único.

Historias de Usuario
US-01: Como comprador, quiero agregar productos de diferentes tiendas a mi carrito para pagar todo junto en una sola transacción.US-02: Como comprador, quiero ver el desglose de los costos de envío de cada vendedor antes de pagar para entender por qué varía el precio total.US-03: Como vendedor, quiero recibir la notificación de venta y el dinero de mi producto de forma independiente para gestionar mi propio inventario y facturación sin enredarme con otras tiendas.

Requisitos Funcionales y Criterios de Aceptación
RF-01: Interfaz del Carrito Agrupada por VendedorDescripción: La pantalla del carrito de compras debe organizar visualmente los artículos según la tienda que los vende.Criterios de Aceptación:Debe mostrar el nombre del vendedor como encabezado y, debajo, sus respectivos productos.Cada grupo de vendedor debe tener su propio cálculo de "Costo de Envío" y "Tiempo de Entrega Estimado".El usuario debe poder eliminar un producto o guardar para más tarde sin alterar los productos de los otros vendedores.

Requisitos No Funcionales
Rendimiento bajo carga masiva: Durante eventos de alta demanda (como un CyberMonday), el backend del carrito de compras debe soportar 50,000 peticiones de checkout concurrentes por minuto sin caídas del servicio.Tiempo de Respuesta: El cálculo del subtotal del carrito con múltiples vendedores no debe tardar más de 800ms en renderizarse.

Gestión de Errores
¿Qué pasa si un producto se agota mientras el usuario está en el checkout?El sistema debe bloquear la transacción, regresar al usuario a la pantalla del carrito, resaltar el producto sin stock en color rojo y mostrar el mensaje: "El artículo de la tienda X ya no está disponible. Modifica tu carrito para continuar".
