# Guía pedagógica para mejorar Weapon Store

## Propósito y regla de seguridad

Esta guía propone una ruta incremental para convertir el estado actual de **Weapon Store** en un mejor ejercicio académico de Flask. El proyecto actualmente contiene catálogo, autenticación, carrito y un CRUD básico de productos; las mejoras deben hacerse en orden, demostrando cada resultado antes de avanzar.

> **Regla explícita:** Weapon Store es únicamente una **simulación académica de una tienda** para aprender desarrollo web. No es una plataforma de comercio real de armas, no debe procesar ventas reales, pagos reales, envíos reales ni facilitar la adquisición de armas o munición.

No incluyas secretos, contraseñas, tokens, datos personales reales ni archivos de usuarios en commits, capturas, ejemplos o documentación. No uses datos reales para probar el proyecto.

## Estado de partida verificado

- La aplicación está concentrada en `app.py` y usa Flask, Flask-SQLAlchemy, Jinja2 y SQLite.
- Hay registro, inicio/cierre de sesión, catálogo, carrito, descuento de stock y CRUD de productos para vendedores.
- La clave de sesión está escrita directamente en el código y la aplicación arranca con `debug=True`.
- No se observa protección CSRF en los formularios que cambian estado.
- La autorización del CRUD no es uniforme: editar comprueba el propietario, pero eliminar no comprueba que el producto pertenezca al vendedor autenticado.
- Las subidas de imágenes se guardan sin límites de tamaño ni validación suficiente de tipo y contenido.
- La base SQLite (`instance/database.db`) está versionada, lo que mezcla datos generados con código fuente.
- No hay un archivo claro de dependencias reproducibles ni una suite de pruebas automatizadas.
- `PRD.md` y `SPEC.md` describen checkout multi-vendedor, órdenes, API, historial y otras capacidades que no están implementadas en el código actual.

## Ruta rápida

1. Asegurar configuración, sesiones, formularios y autorización.
2. Hacer confiables las entradas, las imágenes, el carrito y el inventario.
3. Separar datos locales del código y reproducir la instalación.
4. Añadir pruebas y alinear PRD/SPEC con el alcance real.
5. Solo después evaluar funciones avanzadas de la simulación.

---

## Etapa 1 — Configuración segura y límites del ejercicio

### Objetivo

Eliminar riesgos básicos de configuración sin cambiar todavía el modelo funcional.

### Pasos concretos

1. Leer la configuración actual y listar qué valores deben salir del código.
2. Mover la clave de sesión a una variable de entorno local; usar una clave de desarrollo distinta de cualquier entorno compartido.
3. Configurar `debug` mediante una variable de entorno y dejarlo desactivado por defecto.
4. Documentar variables necesarias en un archivo de ejemplo sin valores secretos.
5. Añadir una nota visible en el README que confirme el carácter académico y simulado.
6. Revisar que los mensajes de error no expongan rutas, contraseñas ni información interna.

### Evidencia de terminado

- La aplicación no contiene una clave secreta literal.
- La ejecución normal no activa el depurador.
- El archivo de ejemplo contiene solo nombres de variables y valores ficticios.
- Una búsqueda del repositorio no encuentra secretos ni datos sensibles.

### Comandos seguros

```bash
python -m compileall app.py
git diff --check
git status --short
```

Estos comandos inspeccionan o validan localmente; no hacen `pull`, `commit` ni `push`.

### Fuera del alcance

No desplegar en internet, no configurar pagos, no crear credenciales reales y no migrar todavía de SQLite.

---

## Etapa 2 — Protección de formularios y autorización

### Objetivo

Evitar cambios de estado no autorizados y garantizar que cada vendedor solo opere sobre sus propios productos.

### Pasos concretos

1. Incorporar protección CSRF para registro, login si corresponde al diseño elegido, perfil, carrito, checkout simulado y CRUD.
2. Usar `POST` para toda operación que cree, edite, elimine o confirme datos; mantener `GET` para consultas.
3. Centralizar una comprobación de sesión y rol, en lugar de repetir validaciones frágiles en cada ruta.
4. En editar y eliminar, cargar el producto y verificar siempre `producto.vendedor_id == usuario.id`.
5. Rechazar IDs manipulados, usuarios inexistentes y roles enviados desde el navegador que no estén permitidos por el servidor.
6. Probar con dos usuarios de prueba: cada uno debe ver y modificar solo sus productos.

### Evidencia de terminado

- Un formulario sin token CSRF falla de forma controlada.
- Un vendedor no puede editar ni eliminar el producto de otro cambiando el ID de la URL.
- Un usuario no autenticado no puede acceder a rutas protegidas.
- Las respuestas de acceso denegado no revelan información de otros usuarios.

### Comandos seguros

```bash
python -m compileall app.py
pytest -q
git diff --check
```

Si aún no existe `pytest`, documenta la necesidad en vez de instalar dependencias a ciegas.

### Fuera del alcance

No implementar todavía un panel administrativo completo, permisos empresariales ni integración con proveedores externos de identidad.

---

## Etapa 3 — Validación de entradas, archivos y errores

### Objetivo

Hacer que el catálogo y el perfil toleren entradas inválidas sin corrupción, excepciones no controladas ni archivos peligrosos.

### Pasos concretos

1. Validar en servidor nombre, descripción, precio, stock, rol y correo; no confiar en validaciones HTML.
2. Rechazar precios negativos, stock negativo, campos obligatorios vacíos y cantidades imposibles.
3. Usar valores monetarios apropiados para evitar errores de `float` al calcular totales.
4. Definir un límite total de tamaño de petición y un número máximo de imágenes por producto.
5. Permitir solo extensiones y tipos MIME de imagen previamente definidos; verificar también el contenido y no solo el nombre.
6. Generar nombres de archivo no predecibles, conservarlos fuera de rutas ejecutables y evitar sobrescribir archivos.
7. Mostrar mensajes de validación claros y registrar errores técnicos sin exponerlos al usuario.

### Evidencia de terminado

- Cada entrada inválida devuelve un error comprensible y no crea registros parciales.
- Un archivo grande, con extensión falsa o de tipo no permitido se rechaza.
- Los archivos válidos se sirven como imágenes y no permiten ejecución.
- Una excepción de conversión numérica no derriba la aplicación.

### Comandos seguros

```bash
python -m compileall .
pytest -q
git diff --check
```

### Fuera del alcance

No subir archivos reales de estudiantes, documentos de identidad, fotos personales ni material relacionado con armas. No añadir reconocimiento de imágenes ni almacenamiento externo.

---

## Etapa 4 — Carrito e inventario coherentes

### Objetivo

Garantizar que el carrito simulado calcule y descuente cantidades válidas sin confiar en precios o stock guardados en la sesión.

### Pasos concretos

1. Guardar en sesión solo identificadores y cantidades mínimas; consultar nombre y precio actuales desde la base de datos.
2. Recalcular subtotales en servidor en cada vista y al confirmar la simulación.
3. Validar que el producto exista, esté disponible y que la cantidad sea positiva y no supere el stock.
4. Revalidar todo el carrito justo antes de descontar inventario.
5. Ejecutar el descuento dentro de una transacción y cancelar completo si algún producto no tiene stock.
6. Mostrar qué artículo simulado causó el rechazo y conservar el carrito para corregirlo.
7. Añadir eliminación individual y actualización de cantidades solo después de protegerlas con CSRF y autorización de sesión.

### Evidencia de terminado

- Alterar el precio o cantidad almacenados en la sesión no cambia el total aceptado por el servidor.
- Un carrito con un producto agotado no descuenta ningún otro producto.
- Dos confirmaciones consecutivas no pueden vender más unidades que el stock disponible.
- El resultado de la simulación queda claro y no se presenta como pago real.

### Comandos seguros

```bash
pytest -q
python -m compileall app.py
git diff --check
```

### Fuera del alcance

No implementar pasarela de pago, datos bancarios, facturación legal, pedidos reales, envíos ni liquidaciones de dinero.

---

## Etapa 5 — Datos reproducibles y calidad del proyecto

### Objetivo

Permitir que otra persona ejecute el ejercicio desde cero sin compartir una base de datos ni depender de instalaciones implícitas.

### Pasos concretos

1. Dejar de versionar la base SQLite generada y agregarla a las exclusiones apropiadas.
2. Mantener, si hace falta, un script de datos ficticios y mínimo para desarrollo; nunca incluir datos personales.
3. Crear un archivo de dependencias fijadas o un mecanismo reproducible equivalente.
4. Completar el README con versión de Python, creación del entorno virtual, instalación, configuración y ejecución local.
5. Añadir una configuración de prueba separada de la base de desarrollo.
6. Documentar cómo reiniciar datos de prueba sin borrar archivos arbitrarios.

### Evidencia de terminado

- Un entorno limpio puede instalar dependencias y arrancar la aplicación siguiendo el README.
- Las pruebas no dependen de `instance/database.db` ni de archivos subidos existentes.
- El estado de Git no incorpora bases ni uploads generados por la ejecución.

### Comandos seguros

```bash
python --version
python -m venv .venv
python -m pip install -r requirements.txt
pytest -q
git status --short
```

La creación de `.venv` es local. No uses credenciales ni ejecutes comandos de publicación.

### Fuera del alcance

No reemplazar SQLite por un servicio administrado, no configurar CI/CD con secretos reales y no desplegar la aplicación.

---

## Etapa 6 — Pruebas y alineación de requisitos

### Objetivo

Convertir los requisitos en evidencia verificable y corregir la desalineación entre documentación y código actual.

### Pasos concretos

1. Crear pruebas de autenticación, autorización, validación, uploads, carrito, stock y CRUD.
2. Añadir pruebas de regresión para impedir que un vendedor elimine productos ajenos.
3. Comparar cada requisito de `PRD.md` y `SPEC.md` con una de tres decisiones: implementado, pendiente o fuera de alcance académico.
4. Corregir la documentación para que no marque como terminado lo que el código no soporta.
5. Separar explícitamente el catálogo/carrito actual de las funciones no implementadas: órdenes, historial, API, checkout multi-vendedor real, notificaciones y liquidaciones.
6. Medir solo objetivos razonables para un ejercicio local; no presentar métricas de producción como garantías.

### Evidencia de terminado

- La suite automatizada pasa en un entorno limpio.
- Existe una matriz requisito → prueba → estado.
- PRD, SPEC y README describen el mismo alcance.
- Los elementos pendientes tienen responsable académico o una tarea futura, no una casilla marcada falsamente como completada.

### Comandos seguros

```bash
pytest -q
python -m compileall .
git diff --check
git status --short
```

### Fuera del alcance

No reclamar cumplimiento de 50.000 peticiones por minuto, pagos únicos reales, separación financiera, cumplimiento legal o certificaciones de seguridad sin pruebas y arquitectura específicas.

---

## Etapa 7 — Alcance avanzado de la simulación

### Objetivo

Ampliar el aprendizaje solo cuando las etapas anteriores estén demostradas y sin transformar el proyecto en un comercio real de armas.

### Pasos concretos

1. Modelar órdenes y detalles de orden únicamente como registros ficticios de la simulación.
2. Diseñar un carrito multi-vendedor y agrupar visualmente por vendedor sin pagos ni liquidaciones reales.
3. Añadir historial académico de simulaciones y estados controlados.
4. Incorporar una API JSON solo si existe una necesidad pedagógica clara y con la misma autorización que las vistas HTML.
5. Añadir observabilidad local: logs sin contraseñas, métricas de prueba y mensajes de error trazables.
6. Revisar rendimiento con datos sintéticos pequeños y declarar las limitaciones de cualquier medición.

### Evidencia de terminado

- Las nuevas funciones tienen modelo, pruebas, autorización y documentación coherentes.
- Los datos son ficticios y el flujo se identifica como simulación en la interfaz.
- No existe una ruta que procese dinero, identidades, armas reales, munición o logística real.

### Comandos seguros

```bash
pytest -q
python -m compileall .
git diff --check
```

### Fuera del alcance

Quedan fuera de todo el proyecto: comercio real de armas o munición, pagos, financiación, verificación legal de compradores, licencias, envíos reales, inventario comercial, notificaciones comerciales y cualquier dato sensible.

## Criterio final de entrega académica

La mejora está lista cuando las pruebas pasan, el README permite reproducir el entorno, no se versionan secretos ni datos generados, la autorización está comprobada con casos negativos y PRD/SPEC distinguen claramente lo implementado de lo pendiente. La entrega debe seguir siendo una simulación educativa, nunca un sistema operativo de comercio real de armas.
