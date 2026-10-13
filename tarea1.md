# Guía básica de Weapon Store

## Objetivo

Dejar la aplicación funcionando localmente y practicar configuraciones básicas de seguridad, autorización, validación, carrito y pruebas.

## Regla de simulación académica

Weapon Store es únicamente un ejercicio académico. No implementes pagos, envíos ni comercio real. No uses secretos, contraseñas, tokens, datos personales ni datos reales.

## Pasos de trabajo

1. **Ejecutar localmente**
   - Crea un entorno virtual, instala las dependencias y ejecuta la aplicación.
   - Comprueba que puedas abrirla en el navegador.

2. **Configuración segura**
   - Usa una variable de entorno para la clave de sesión.
   - Mantén la depuración desactivada por defecto.
   - Documenta la configuración con valores de ejemplo, nunca con secretos.

3. **Autorización y CSRF**
   - Protege los formularios que modifican datos con CSRF.
   - Verifica el inicio de sesión y el rol antes de permitir cambios.
   - Impide que un vendedor edite o elimine productos de otro vendedor.

4. **Validación y carrito**
   - Valida en el servidor los campos obligatorios, precios, cantidades e imágenes permitidas.
   - Rechaza valores negativos, productos inexistentes o cantidades mayores que el stock.
   - Calcula el total y actualiza el inventario en el servidor.

5. **Pruebas y README**
   - Prueba inicio de sesión, permisos, productos, carrito e inventario.
   - Ejecuta las pruebas y documenta en el README cómo instalar y ejecutar el proyecto.

## Comandos mínimos

Desde la carpeta del proyecto:

```bash
python -m venv .venv
python -m pip install -r requirements.txt
python app.py
pytest -q
git diff --check
```

## Evidencias

- Aplicación ejecutándose localmente.
- README con instalación, configuración y ejecución.
- Resultado de las pruebas.
- Explicación breve o capturas de las comprobaciones realizadas.
- Entrega sin secretos ni datos reales.

## Checklist final

- [ ] La aplicación inicia localmente.
- [ ] La depuración está desactivada por defecto.
- [ ] La configuración no contiene secretos.
- [ ] Los formularios importantes tienen protección CSRF.
- [ ] Los permisos impiden modificar productos ajenos.
- [ ] Los productos, imágenes, cantidades y stock se validan.
- [ ] El carrito calcula los totales en el servidor.
- [ ] Las pruebas pasan.
- [ ] El README está actualizado.
- [ ] Pagos, envíos y comercio real no forman parte de la entrega.
