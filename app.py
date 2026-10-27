import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader
import cloudinary.api

app = Flask(__name__)

# -----------------------------------------------------------------------------
# CONFIGURACIÓN Y SEGURIDAD
# -----------------------------------------------------------------------------
app.config['SECRET_KEY'] = os.getenv("SESSION_SECRET", "Wardog2026_default_key")
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1")

# Protección avanzada de cookies de sesión
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

csrf = CSRFProtect(app)

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE CLOUDINARY (Para que las imágenes funcionen en cualquier parte)
# -----------------------------------------------------------------------------
# Reemplaza estos valores con tus datos de Cloudinary o usa variables de entorno
cloudinary.config(
    cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME', 'tu_cloud_name'),
    api_key = os.getenv('CLOUDINARY_API_KEY', 'tu_api_key'),
    api_secret = os.getenv('CLOUDINARY_API_SECRET', 'tu_api_secret')
)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

EXTENSIONES_PERMITIDAS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def es_imagen_permitida(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in EXTENSIONES_PERMITIDAS

# -----------------------------------------------------------------------------
# FILTROS Y MANEJADORES DE ERRORES
# -----------------------------------------------------------------------------
@app.template_filter('formato_precio')
def formato_precio(valor):
    try:
        return f"{int(valor):,}".replace(",", ".")
    except (ValueError, TypeError):
        return valor

@app.errorhandler(404)
def pagina_no_encontrada(e):
    if request.path.startswith('/static/'):
        return "Archivo no encontrado", 404
    flash('La página o recurso al que intentas acceder no existe.')
    return redirect(url_for('inicio'))

@app.errorhandler(500)
def error_servidor(e):
    db.session.rollback()
    flash('Ocurrió un error interno en el servidor.')
    return redirect(url_for('inicio'))

# -----------------------------------------------------------------------------
# DECORADORES DE AUTORIZACIÓN Y ROLES
# -----------------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión para continuar.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(rol_requerido):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('usuario_rol') != rol_requerido:
                flash('Acceso denegado: No tienes los permisos necesarios.')
                return redirect(url_for('inicio'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# -----------------------------------------------------------------------------
# MODELOS DE BASE DE DATOS
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
    foto_perfil = db.Column(db.String(300), default='https://res.cloudinary.com/demo/image/upload/v1312461204/sample.jpg')
    descripcion = db.Column(db.Text, default='¡Hola! Estoy usando WarDog Store.')

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=1)
    descripcion = db.Column(db.Text, default='Sin especificaciones.')
    envio = db.Column(db.String(100), default='Envío Estándar')
    
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
        
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and check_password_hash(usuario.password, password):
            session['usuario_id'] = usuario.id
            session['usuario_nombre'] = usuario.nombre
            session['usuario_rol'] = usuario.rol
            return redirect(url_for('inicio'))
        flash('Credenciales incorrectas.')
    return render_template('login.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        rol = request.form.get('rol', '').strip()
        
        if Usuario.query.filter_by(email=email).first():
            flash('El correo ya está registrado.')
            return redirect(url_for('registro'))
        
        hashed = generate_password_hash(password, method='scrypt')
        nuevo = Usuario(nombre=nombre, email=email, password=hashed, rol=rol)
        db.session.add(nuevo)
        db.session.commit()
        
        session['usuario_id'] = nuevo.id
        session['usuario_nombre'] = nuevo.nombre
        session['usuario_rol'] = nuevo.rol
        return redirect(url_for('inicio'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# -----------------------------------------------------------------------------
# RUTAS DE VITRINA Y PERFIL
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
                flash('Tipo de imagen no permitido.')
                return redirect(url_for('vista_perfil'))
            try:
                upload_result = cloudinary.uploader.upload(archivo)
                usuario.foto_perfil = upload_result.get('secure_url')
            except Exception as e:
                print(f"ERROR CLOUDINARY PERFIL: {e}")
                flash('Error al subir la imagen a la nube.')

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
                item['imagen'] = 'https://res.cloudinary.com/demo/image/upload/v1312461204/sample.jpg'

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
        flash('La cantidad debe ser mayor a cero.')
        return redirect(url_for('detalle_producto', id=id))

    if 'carrito' not in session:
        session['carrito'] = []

    carrito = session['carrito']
    encontrado = False
    foto_ruta = producto.imagenes[0].ruta if producto.imagenes else 'https://res.cloudinary.com/demo/image/upload/v1312461204/sample.jpg'

    cantidad_en_carrito = 0
    for item in carrito:
        if item['id'] == producto.id:
            cantidad_en_carrito = item['cantidad']
            break

    total_proyectado = cantidad_en_carrito + cantidad_solicitada

    if total_proyectado > producto.stock:
        flash(f'Stock insuficiente. Stock disponible: {producto.stock}.')
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
    flash('Producto agregado al carrito.')
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
            elif accion == 'restar':
                if item['cantidad'] > 1:
                    item['cantidad'] -= 1
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
        try:
            for item in carrito:
                producto = Producto.query.get(item['id'])
                if producto:
                    producto.stock -= item['cantidad']

            db.session.commit()
            session.pop('carrito', None)
            return render_template('pasarela_pago.html', pago_exitoso=True, metodo_pago=metodo_pago, usuario=usuario, total_pagar=total_pagar, carrito=[])
        except Exception as e:
            db.session.rollback()
            print(f"ERROR EN PAGO: {e}")
            flash('Ocurrió un error al procesar el pago.')
            return redirect(url_for('vista_cliente'))

    return render_template('pasarela_pago.html', carrito=carrito_validado, total_pagar=total_pagar, usuario=usuario)

# -----------------------------------------------------------------------------
# PANEL DE VENDEDOR Y GESTIÓN DE PRODUCTOS E IMÁGENES (CON CLOUDINARY)
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
    precio = float(request.form.get('precio', 0))
    stock = int(request.form.get('stock', 1))
    descripcion = request.form.get('descripcion', '').strip()
    envio = request.form.get('envio', '').strip()

    archivos = request.files.getlist('imagenes_archivos')
    
    try:
        nuevo_prod = Producto(
            nombre=nombre, precio=precio, stock=stock,
            descripcion=descripcion, envio=envio, vendedor_id=session['usuario_id']
        )
        db.session.add(nuevo_prod)
        db.session.commit()

        for archivo in archivos:
            if archivo and archivo.filename != '':
                if es_imagen_permitida(archivo.filename):
                    try:
                        upload_result = cloudinary.uploader.upload(archivo)
                        secure_url = upload_result.get('secure_url')
                        nueva_foto = FotoProducto(ruta=secure_url, producto_id=nuevo_prod.id)
                        db.session.add(nueva_foto)
                    except Exception as e:
                        print(f"ERROR CLOUDINARY PRODUCTO: {e}")

        if not nuevo_prod.imagenes:
            foto_default = FotoProducto(ruta='https://res.cloudinary.com/demo/image/upload/v1312461204/sample.jpg', producto_id=nuevo_prod.id)
            db.session.add(foto_default)

        db.session.commit()
        flash('Producto publicado exitosamente en la nube.')
    except Exception as e:
        db.session.rollback()
        print(f"ERROR AL SUBIR PRODUCTO: {e}")
        flash('Ocurrió un error al publicar el producto.')

    return redirect(url_for('vista_vendedor'))

@app.route('/vendedor/producto/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('vendedor')
def editar_producto(id):
    producto = Producto.query.get_or_404(id)
    
    if producto.vendedor_id != session['usuario_id']:
        flash('Acceso denegado.')
        return redirect(url_for('vista_vendedor'))

    if request.method == 'POST':
        producto.nombre = request.form.get('nombre', '').strip()
        producto.precio = float(request.form.get('precio', 0))
        producto.stock = int(request.form.get('stock', 0))
        producto.envio = request.form.get('envio', '').strip()
        producto.descripcion = request.form.get('descripcion', '').strip()

        archivos = request.files.getlist('nuevas_imagenes')
        for archivo in archivos:
            if archivo and archivo.filename != '':
                if es_imagen_permitida(archivo.filename):
                    try:
                        upload_result = cloudinary.uploader.upload(archivo)
                        secure_url = upload_result.get('secure_url')
                        nueva_foto = FotoProducto(ruta=secure_url, producto_id=producto.id)
                        db.session.add(nueva_foto)
                    except Exception as e:
                        print(f"ERROR CLOUDINARY EDITAR: {e}")

        try:
            db.session.commit()
            flash('Producto actualizado correctamente.')
        except Exception as e:
            db.session.rollback()
            print(f"ERROR AL EDITAR: {e}")
            flash('Error al guardar los cambios.')

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
        try:
            db.session.delete(foto)
            db.session.commit()
            flash('Imagen eliminada correctamente.')
        except Exception as e:
            db.session.rollback()
            print(f"ERROR AL ELIMINAR FOTO: {e}")
            flash('Error al eliminar la imagen.')

        return redirect(url_for('editar_producto', id=producto.id))

    flash('Acceso denegado.')
    return redirect(url_for('vista_vendedor'))

@app.route('/vendedor/producto/eliminar/<int:id>', methods=['POST'])
@login_required
@role_required('vendedor')
def eliminar_producto(id):
    producto = Producto.query.get_or_404(id)
    
    if producto.vendedor_id != session['usuario_id']:
        flash('Acceso denegado.')
        return redirect(url_for('vista_vendedor'))

    try:
        db.session.delete(producto)
        db.session.commit()
        flash('Producto eliminado con éxito.')
    except Exception as e:
        db.session.rollback()
        print(f"ERROR AL ELIMINAR PRODUCTO: {e}")
        flash('Error al eliminar el producto.')

    return redirect(url_for('vista_vendedor'))

if __name__ == '__main__':
    app.run(debug=True)