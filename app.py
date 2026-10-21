import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)

# -----------------------------------------------------------------------------
# CONFIGURACIÓN Y VARIABLES DE ENTORNO
# -----------------------------------------------------------------------------
app.config['SECRET_KEY'] = os.getenv("SESSION_SECRET", "Wardog2026_default_key")
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1")

# Banderas de seguridad para la cookie de sesión
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

csrf = CSRFProtect(app)

UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

EXTENSIONES_PERMITIDAS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def es_imagen_permitida(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in EXTENSIONES_PERMITIDAS

# -----------------------------------------------------------------------------
# FILTROS DE PLANTILLA
# -----------------------------------------------------------------------------
@app.template_filter('formato_precio')
def formato_precio(valor):
    try:
        return f"{int(valor):,}".replace(",", ".")
    except (ValueError, TypeError):
        return valor

# -----------------------------------------------------------------------------
# MANEJADORES DE ERRORES PERSONALIZADOS
# -----------------------------------------------------------------------------
@app.errorhandler(404)
def pagina_no_encontrada(e):
    flash('La página o recurso al que intentas acceder no existe.')
    return redirect(url_for('inicio'))

@app.errorhandler(500)
def error_servidor(e):
    db.session.rollback()
    flash('Ocurrió un error interno en el servidor. Inténtalo de nuevo.')
    return redirect(url_for('inicio'))

# -----------------------------------------------------------------------------
# DECORADORES DE AUTORIZACIÓN Y ROLES
# -----------------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión para acceder a esta sección.')
            return redirect(url_for('login'))

        # Verificación de usuario existente en la base de datos
        usuario = Usuario.query.get(session['usuario_id'])
        if not usuario:
            session.clear()
            flash('Tu sesión expiró o no es válida. Por favor ingresa nuevamente.')
            return redirect(url_for('login'))

        return f(*args, **kwargs)
    return decorated_function

def role_required(rol_requerido):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'usuario_id' not in session:
                return redirect(url_for('login'))
            if session.get('usuario_rol') != rol_requerido:
                flash('Acceso denegado: No tienes los permisos requeridos.')
                return redirect(url_for('inicio'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# -----------------------------------------------------------------------------
# MODELOS DE LA BASE DE DATOS
# -----------------------------------------------------------------------------
class Seguidor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seguidor_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    seguido_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(20), nullable=False)
    foto_perfil = db.Column(db.String(300), default='/static/uploads/default.png')
    descripcion = db.Column(db.Text, default='¡Hola! Estoy usando WarDog Store.')

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=1)
    descripcion = db.Column(db.Text, default='Sin especificaciones detalladas.')
    envio = db.Column(db.String(100), default='Envío Nacional Estándar')
    
    vendedor_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    vendedor = db.relationship('Usuario', backref=db.backref('productos', lazy=True))
    
    imagenes = db.relationship('FotoProducto', backref='producto', cascade='all, delete-orphan', lazy=True)

class FotoProducto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ruta = db.Column(db.String(300), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)

with app.app_context():
    db.create_all()

# -----------------------------------------------------------------------------
# RUTAS DE AUTENTICACIÓN
# -----------------------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash('Por favor ingresa correo y contraseña.')
            return redirect(url_for('login'))

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and check_password_hash(usuario.password, password):
            session['usuario_id'] = usuario.id
            session['usuario_nombre'] = usuario.nombre
            session['usuario_rol'] = usuario.rol
            return redirect(url_for('inicio'))
        else:
            flash('Correo o contraseña incorrectos.')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        rol = request.form.get('rol', '').strip()

        if not nombre or not email or not password or not rol:
            flash('Todos los campos son obligatorios.')
            return redirect(url_for('registro'))

        if rol not in ('cliente', 'vendedor'):
            flash('Rol seleccionado no válido.')
            return redirect(url_for('registro'))

        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            flash('El correo ya está registrado.')
            return redirect(url_for('registro'))

        try:
            hashed_password = generate_password_hash(password, method='scrypt')
            nuevo_usuario = Usuario(nombre=nombre, email=email, password=hashed_password, rol=rol)
            db.session.add(nuevo_usuario)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('Error al registrar el usuario. Inténtalo de nuevo.')
            return redirect(url_for('registro'))

        session['usuario_id'] = nuevo_usuario.id
        session['usuario_nombre'] = nuevo_usuario.nombre
        session['usuario_rol'] = nuevo_usuario.rol

        return redirect(url_for('inicio'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# -----------------------------------------------------------------------------
# RUTAS DE VITRINA, PERFIL Y SEGUIDORES
# -----------------------------------------------------------------------------
@app.route('/')
@login_required
def inicio():
    usuario = Usuario.query.get(session['usuario_id'])
    productos = Producto.query.all()
    carrito = session.get('carrito', [])
    total_items = sum(item['cantidad'] for item in carrito)
    return render_template('index.html', productos=productos, total_items=total_items, usuario=usuario)

@app.route('/producto/<int:id>')
@login_required
def detalle_producto(id):
    usuario_actual = Usuario.query.get(session['usuario_id'])
    producto = Producto.query.get_or_404(id)
    vendedor = producto.vendedor
    
    seguidores_vendedor = Seguidor.query.filter_by(seguido_id=vendedor.id).count()
    lo_sigo = Seguidor.query.filter_by(seguidor_id=usuario_actual.id, seguido_id=vendedor.id).first() is not None

    return render_template(
        'producto_detalle.html', 
        producto=producto, 
        usuario=usuario_actual,
        vendedor=vendedor,
        seguidores_vendedor=seguidores_vendedor,
        lo_sigo=lo_sigo
    )

@app.route('/perfil')
@app.route('/perfil/<int:user_id>')
@login_required
def vista_perfil(user_id=None):
    usuario_actual = Usuario.query.get(session['usuario_id'])
    
    if user_id is None or user_id == usuario_actual.id:
        usuario = usuario_actual
        es_propio = True
    else:
        usuario = Usuario.query.get_or_404(user_id)
        es_propio = False

    mis_productos = Producto.query.filter_by(vendedor_id=usuario.id).all() if usuario.rol == 'vendedor' else []
    mis_productos_count = len(mis_productos)
    seguidores_count = Seguidor.query.filter_by(seguido_id=usuario.id).count()
    siguiendo_count = Seguidor.query.filter_by(seguidor_id=usuario.id).count()

    lo_sigo = False
    if not es_propio:
        lo_sigo = Seguidor.query.filter_by(seguidor_id=usuario_actual.id, seguido_id=usuario.id).first() is not None

    return render_template(
        'perfil.html', 
        usuario=usuario,
        usuario_actual=usuario_actual,
        es_propio=es_propio,
        mis_productos=mis_productos,
        mis_productos_count=mis_productos_count,
        seguidores_count=seguidores_count,
        siguiendo_count=siguiendo_count,
        lo_sigo=lo_sigo
    )

@app.route('/seguir/<int:id>', methods=['POST'])
@login_required
def seguir_usuario(id):
    usuario_actual_id = session['usuario_id']
    if usuario_actual_id != id:
        existente = Seguidor.query.filter_by(seguidor_id=usuario_actual_id, seguido_id=id).first()
        if not existente:
            try:
                nuevo_seguimiento = Seguidor(seguidor_id=usuario_actual_id, seguido_id=id)
                db.session.add(nuevo_seguimiento)
                db.session.commit()
                flash('¡Ahora sigues a este usuario!')
            except Exception:
                db.session.rollback()

    return redirect(request.referrer or url_for('vista_perfil', user_id=id))

@app.route('/dejar_de_seguir/<int:id>', methods=['POST'])
@login_required
def dejar_de_seguir(id):
    usuario_actual_id = session['usuario_id']
    seguimiento = Seguidor.query.filter_by(seguidor_id=usuario_actual_id, seguido_id=id).first()
    if seguimiento:
        try:
            db.session.delete(seguimiento)
            db.session.commit()
            flash('Has dejado de seguir a este usuario.')
        except Exception:
            db.session.rollback()

    return redirect(request.referrer or url_for('vista_perfil', user_id=id))

@app.route('/editar_perfil', methods=['POST'])
@login_required
def editar_perfil():
    usuario = Usuario.query.get(session['usuario_id'])
    descripcion = request.form.get('descripcion', '').strip()
    
    if 'foto_archivo' in request.files:
        archivo = request.files['foto_archivo']
        if archivo and archivo.filename != '':
            if not es_imagen_permitida(archivo.filename):
                flash('Tipo de imagen no permitido para la foto de perfil.')
                return redirect(url_for('vista_perfil'))

            nombre_archivo = secure_filename(f"user_{usuario.id}_{archivo.filename}")
            ruta_guardado = os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo)
            archivo.save(ruta_guardado)
            usuario.foto_perfil = f"/static/uploads/{nombre_archivo}"

    if descripcion:
        usuario.descripcion = descripcion

    try:
        db.session.commit()
        flash('Perfil actualizado con éxito.')
    except Exception:
        db.session.rollback()
        flash('Ocurrió un error al actualizar el perfil.')

    return redirect(url_for('vista_perfil'))

# -----------------------------------------------------------------------------
# RUTAS DE CARRITO Y PASARELA DE PAGO
# -----------------------------------------------------------------------------
@app.route('/cliente')
@login_required
def vista_cliente():
    usuario = Usuario.query.get(session['usuario_id'])
    carrito = session.get('carrito', [])
    
    for item in carrito:
        if 'imagen' not in item:
            prod = Producto.query.get(item['id'])
            if prod and prod.imagenes:
                item['imagen'] = prod.imagenes[0].ruta
            else:
                item['imagen'] = '/static/uploads/default_product.png'

    total_pagar = sum(item['precio'] * item['cantidad'] for item in carrito)
    return render_template('cliente.html', carrito=carrito, total_pagar=total_pagar, usuario=usuario)

@app.route('/agregar_al_carrito/<int:id>', methods=['POST'])
@login_required
def agregar_al_carrito(id):
    producto = Producto.query.filter_by(id=id).first()
    if not producto:
        flash('El producto solicitado no existe.')
        return redirect(url_for('inicio'))

    try:
        cantidad_solicitada = int(request.form.get('cantidad', 1))
    except ValueError:
        flash('Cantidad inválida.')
        return redirect(url_for('detalle_producto', id=id))

    if cantidad_solicitada <= 0:
        flash('La cantidad añadida debe ser mayor a cero.')
        return redirect(url_for('detalle_producto', id=id))

    if 'carrito' not in session:
        session['carrito'] = []

    carrito = session['carrito']
    encontrado = False
    foto_ruta = producto.imagenes[0].ruta if producto.imagenes else '/static/uploads/default_product.png'

    cantidad_en_carrito = 0
    for item in carrito:
        if item['id'] == producto.id:
            cantidad_en_carrito = item['cantidad']
            break

    total_proyectado = cantidad_en_carrito + cantidad_solicitada

    if total_proyectado > producto.stock:
        flash(f'No puedes añadir {cantidad_solicitada} unidades más. El stock disponible es de {producto.stock} (ya tienes {cantidad_en_carrito} en tu carrito).')
        return redirect(request.referrer or url_for('inicio'))

    for item in carrito:
        if item['id'] == producto.id:
            item['cantidad'] = total_proyectado
            item['precio'] = producto.precio
            item['imagen'] = foto_ruta
            encontrado = True
            break
            
    if not encontrado:
        carrito.append({
            'id': producto.id,
            'nombre': producto.nombre,
            'precio': producto.precio,
            'cantidad': cantidad_solicitada,
            'imagen': foto_ruta
        })

    session.modified = True
    flash(f'Se agregaron {cantidad_solicitada} unidad(es) de "{producto.nombre}" al carrito.')
    return redirect(url_for('vista_cliente'))

@app.route('/actualizar_cantidad_carrito/<int:id>', methods=['POST'])
@login_required
def actualizar_cantidad_carrito(id):
    accion = request.form.get('accion')
    producto = Producto.query.filter_by(id=id).first()
    carrito = session.get('carrito', [])

    for item in carrito:
        if item['id'] == id:
            if accion == 'sumar':
                if producto and item['cantidad'] < producto.stock:
                    item['cantidad'] += 1
                else:
                    flash(f'No hay más unidades disponibles. Stock máximo para "{item["nombre"]}": {producto.stock if producto else 0}.')
            elif accion == 'restar':
                if item['cantidad'] > 1:
                    item['cantidad'] -= 1
                else:
                    flash('Llegaste al mínimo (1). Si deseas quitar el producto, usa el botón "Eliminar".')
            break

    session.modified = True
    return redirect(url_for('vista_cliente'))

@app.route('/eliminar_del_carrito/<int:id>', methods=['POST'])
@login_required
def eliminar_del_carrito(id):
    carrito = session.get('carrito', [])
    session['carrito'] = [item for item in carrito if item['id'] != id]
    session.modified = True
    flash('Producto eliminado del carrito.')
    return redirect(url_for('vista_cliente'))

@app.route('/vaciar_carrito', methods=['POST'])
@login_required
def vaciar_carrito():
    session.pop('carrito', None)
    return redirect(url_for('vista_cliente'))

@app.route('/pasarela_pago', methods=['GET', 'POST'])
@login_required
def pasarela_pago():
    usuario = Usuario.query.get(session['usuario_id'])
    carrito = session.get('carrito', [])

    if not carrito and request.method == 'GET':
        return redirect(url_for('vista_cliente'))

    total_pagar = 0
    carrito_validado = []
    
    for item in carrito:
        prod = Producto.query.get(item['id'])
        if prod:
            subtotal = prod.precio * item['cantidad']
            total_pagar += subtotal
            carrito_validado.append(item)

    if request.method == 'POST':
        metodo_pago = request.form.get('metodo_pago', 'PSE')
        
        for item in carrito:
            producto = Producto.query.get(item['id'])
            if not producto:
                flash(f'El producto "{item["nombre"]}" ya no está disponible.')
                return redirect(url_for('vista_cliente'))

            if item['cantidad'] > producto.stock:
                flash(f'No hay suficiente stock disponible para "{producto.nombre}". Stock actual: {producto.stock}.')
                return redirect(url_for('vista_cliente'))

        try:
            for item in carrito:
                producto = Producto.query.get(item['id'])
                producto.stock -= item['cantidad']

            db.session.commit()
            session.pop('carrito', None)
            return render_template('pasarela_pago.html', pago_exitoso=True, metodo_pago=metodo_pago, usuario=usuario, total_pagar=total_pagar, carrito=[])
        except Exception:
            db.session.rollback()
            flash('Ocurrió un error al procesar el pago. Por favor intenta de nuevo.')
            return redirect(url_for('vista_cliente'))

    return render_template('pasarela_pago.html', carrito=carrito_validado, total_pagar=total_pagar, usuario=usuario)

# -----------------------------------------------------------------------------
# PANEL DE VENDEDOR Y GESTIÓN PROTEGIDA DE PRODUCTOS E IMÁGENES
# -----------------------------------------------------------------------------
@app.route('/vendedor')
@login_required
@role_required('vendedor')
def vista_vendedor():
    usuario = Usuario.query.get(session['usuario_id'])
    productos = Producto.query.filter_by(vendedor_id=usuario.id).all()
    return render_template('vendedor.html', productos=productos, usuario=usuario)

@app.route('/vendedor/producto/nuevo', methods=['POST'])
@login_required
@role_required('vendedor')
def agregar_producto():
    nombre = request.form.get('nombre', '').strip()
    precio_str = request.form.get('precio', '').strip()
    stock_str = request.form.get('stock', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    envio = request.form.get('envio', '').strip()

    if not nombre or not precio_str or not stock_str or not descripcion or not envio:
        flash('Todos los campos son obligatorios.')
        return redirect(url_for('vista_vendedor'))

    try:
        precio = float(precio_str)
        stock = int(stock_str)
    except ValueError:
        flash('El precio y el stock deben ser números válidos.')
        return redirect(url_for('vista_vendedor'))

    if precio <= 0:
        flash('El precio debe ser un número positivo mayor que cero.')
        return redirect(url_for('vista_vendedor'))

    if stock < 0:
        flash('El stock no puede ser un valor negativo.')
        return redirect(url_for('vista_vendedor'))

    archivos = request.files.getlist('imagenes_archivos')
    for archivo in archivos:
        if archivo and archivo.filename != '':
            if not es_imagen_permitida(archivo.filename):
                flash('Tipo de archivo no permitido. Solo se aceptan imágenes (.png, .jpg, .jpeg, .gif, .webp).')
                return redirect(url_for('vista_vendedor'))

    try:
        nuevo_prod = Producto(
            nombre=nombre,
            precio=precio,
            stock=stock,
            descripcion=descripcion,
            envio=envio,
            vendedor_id=session['usuario_id']
        )
        db.session.add(nuevo_prod)
        db.session.commit()

        for i, archivo in enumerate(archivos):
            if archivo and archivo.filename != '':
                nombre_archivo = secure_filename(f"prod_{nuevo_prod.id}_{i}_{archivo.filename}")
                ruta_guardado = os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo)
                archivo.save(ruta_guardado)
                nueva_foto = FotoProducto(ruta=f"/static/uploads/{nombre_archivo}", producto_id=nuevo_prod.id)
                db.session.add(nueva_foto)

        if not nuevo_prod.imagenes:
            foto_default = FotoProducto(ruta='/static/uploads/default_product.png', producto_id=nuevo_prod.id)
            db.session.add(foto_default)

        db.session.commit()
        flash('Producto publicado exitosamente.')
    except Exception:
        db.session.rollback()
        flash('Ocurrió un error al publicar el producto.')

    return redirect(url_for('vista_vendedor'))

@app.route('/vendedor/producto/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('vendedor')
def editar_producto(id):
    producto = Producto.query.get_or_404(id)
    
    if producto.vendedor_id != session['usuario_id']:
        flash('Acceso denegado: No puedes modificar productos de otro vendedor.')
        return redirect(url_for('vista_vendedor'))

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        precio_str = request.form.get('precio', '').strip()
        stock_str = request.form.get('stock', '').strip()
        envio = request.form.get('envio', '').strip()
        descripcion = request.form.get('descripcion', '').strip()

        if not nombre or not precio_str or not stock_str or not descripcion or not envio:
            flash('Todos los campos son obligatorios.')
            return redirect(url_for('editar_producto', id=producto.id))

        try:
            precio = float(precio_str)
            stock = int(stock_str)
        except ValueError:
            flash('El precio y el stock deben ser números válidos.')
            return redirect(url_for('editar_producto', id=producto.id))

        if precio <= 0 or stock < 0:
            flash('El precio debe ser positivo y el stock no puede ser negativo.')
            return redirect(url_for('editar_producto', id=producto.id))

        archivos = request.files.getlist('nuevas_imagenes')
        for archivo in archivos:
            if archivo and archivo.filename != '':
                if not es_imagen_permitida(archivo.filename):
                    flash('Tipo de archivo no permitido en imágenes.')
                    return redirect(url_for('editar_producto', id=producto.id))

        try:
            producto.nombre = nombre
            producto.precio = precio
            producto.stock = stock
            producto.envio = envio
            producto.descripcion = descripcion

            for i, archivo in enumerate(archivos):
                if archivo and archivo.filename != '':
                    nombre_archivo = secure_filename(f"prod_{producto.id}_{i}_{archivo.filename}")
                    ruta_guardado = os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo)
                    archivo.save(ruta_guardado)
                    nueva_foto = FotoProducto(ruta=f"/static/uploads/{nombre_archivo}", producto_id=producto.id)
                    db.session.add(nueva_foto)

            db.session.commit()
            flash('Producto actualizado correctamente.')
        except Exception:
            db.session.rollback()
            flash('Error al guardar los cambios en el producto.')

        return redirect(url_for('editar_producto', id=producto.id))

    usuario = Usuario.query.get(session['usuario_id'])
    return render_template('editar_producto.html', producto=producto, usuario=usuario)

@app.route('/vendedor/foto/eliminar/<int:foto_id>', methods=['POST'])
@login_required
@role_required('vendedor')
def eliminar_foto(foto_id):
    foto = FotoProducto.query.get_or_404(foto_id)
    producto = Producto.query.get(foto.producto_id)

    if producto and producto.vendedor_id == session['usuario_id']:
        ruta_archivo = os.path.join(app.root_path, foto.ruta.lstrip('/'))
        if os.path.exists(ruta_archivo):
            try:
                os.remove(ruta_archivo)
            except Exception:
                pass
        
        try:
            db.session.delete(foto)
            db.session.commit()
            flash('Imagen eliminada correctamente.')
        except Exception:
            db.session.rollback()
            flash('Error al eliminar la imagen de la base de datos.')

        return redirect(url_for('editar_producto', id=producto.id))

    flash('Acceso denegado: No puedes eliminar imágenes de productos de otros vendedores.')
    return redirect(url_for('vista_vendedor'))

@app.route('/vendedor/producto/eliminar/<int:id>', methods=['POST'])
@login_required
@role_required('vendedor')
def eliminar_producto(id):
    producto = Producto.query.get_or_404(id)
    
    if producto.vendedor_id != session['usuario_id']:
        flash('Acceso denegado: No puedes eliminar productos de otro vendedor.')
        return redirect(url_for('vista_vendedor'))

    for foto in producto.imagenes:
        if foto.ruta and not foto.ruta.endswith('default_product.png'):
            ruta_archivo = os.path.join(app.root_path, foto.ruta.lstrip('/'))
            if os.path.exists(ruta_archivo):
                try:
                    os.remove(ruta_archivo)
                except Exception:
                    pass

    try:
        db.session.delete(producto)
        db.session.commit()
        flash('Producto e imágenes eliminados con éxito.')
    except Exception:
        db.session.rollback()
        flash('Error al eliminar el producto de la base de datos.')

    return redirect(url_for('vista_vendedor'))

# -----------------------------------------------------------------------------
# PUNTO DE ENTRADA PRINCIPAL
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)  