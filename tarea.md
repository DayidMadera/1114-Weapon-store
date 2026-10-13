# Tarea: mejorar Weapon Store

## Objetivo

Mejorar la aplicación para que funcione de forma local, segura y clara como ejercicio de Flask.

## Regla de simulación académica

Weapon Store es solo una simulación para aprender. No debe manejar ventas, pagos, envíos ni datos reales relacionados con armas o munición.

No incluyas secretos, contraseñas, tokens, datos personales ni bases de datos generadas en la entrega.

## Para esta entrega

Completa estos pasos en orden:

1. **Ejecutar localmente**
   - Crea un entorno virtual e instala las dependencias.
   - Ejecuta la aplicación en tu equipo.
   - Explica en el README cómo instalarla y ejecutarla.

2. **Configurar sin secretos**
   - Lee la clave de sesión desde una variable de entorno.
   - Mantén el modo de depuración desactivado por defecto.
   - Documenta las variables necesarias con valores de ejemplo, nunca con secretos.

3. **Corregir autorización y CSRF**
   - Protege los formularios que cambian datos con CSRF.
   - Comprueba que el usuario haya iniciado sesión y tenga el rol correcto.
   - Verifica que un vendedor solo pueda editar o eliminar sus propios productos.
   - Rechaza accesos con IDs cambiados desde la URL.

4. **Validar productos e imágenes**
   - Valida en el servidor nombre, precio, stock y campos obligatorios.
   - Rechaza precios o cantidades negativas.
   - Acepta solo imágenes permitidas y con un tamaño razonable.
   - Muestra errores claros sin enseñar información interna.

5. **Revisar carrito e inventario**
   - Comprueba que el producto exista y tenga stock.
   - Calcula precios y totales en el servidor.
   - No permitas cantidades cero, negativas o mayores que el stock.
   - Descuenta el inventario solo si todo el carrito es válido.

6. **Probar y documentar**
   - Añade o corrige pruebas de login, autorización, productos, imágenes, carrito e inventario.
   - Ejecuta las pruebas.
   - Actualiza el README para que describa solo lo que realmente funciona.

## Comandos mínimos

Ejecuta desde la carpeta del proyecto:

```bash
python -m venv .venv
python -m pip install -r requirements.txt
python app.py
pytest -q
git diff --check
```

Si el proyecto usa otros comandos, escríbelos en el README. No ejecutes comandos de publicación ni guardes credenciales reales.

## Evidencia de terminado

- [ ] La aplicación inicia y funciona localmente.
- [ ] El README explica instalación, configuración y ejecución.
- [ ] No hay secretos ni datos reales en el código o en la entrega.
- [ ] La depuración no está activa por defecto.
- [ ] Los formularios protegidos rechazan solicitudes sin CSRF.
- [ ] Un vendedor no puede cambiar productos de otro vendedor.
- [ ] Los productos, imágenes, cantidades y stock se validan.
- [ ] Las pruebas pasan.

## Lista final

- [ ] Código actualizado.
- [ ] Pruebas ejecutadas.
- [ ] README actualizado.
- [ ] Capturas o explicación breve de las pruebas realizadas.
- [ ] Base de datos, imágenes generadas y archivos con secretos excluidos.

## Después

Estas funciones no son necesarias para esta entrega: pagos, pedidos reales, envíos, API, panel administrativo completo, carrito avanzado, notificaciones, despliegue en internet y migración a servicios externos.
