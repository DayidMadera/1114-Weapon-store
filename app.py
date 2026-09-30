import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'clave_secreta_mercadolibre_super_segura'

@app.template_filter('formato_precio')
def formato_precio(valor):
    try:
        # Convierte el valor a entero y aplica punto como separador de miles
        return f"{int(valor):,}".replace(",", ".")
    except (ValueError, TypeError):
        return valor

UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# -----------------------------------------------------------------------------
# MODELOS DE LA BASE DE DATOS
# -----------------------------------------------------------------------------
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(20), nullable=False)
    foto_perfil = db.Column(db.String(300), default='/static/uploads/default.png')
    descripcion = db.Column(db.Text, default='¡Hola! Estoy usando Mercado Libre.')

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=1)
    descripcion = db.Column(db.Text, default='Sin especificaciones detalladas.')
    envio = db.Column(db.String(100), default='Envío Nacional Estándar')
    
    vendedor_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    vendedor = db.relationship('Usuario', backref=db.backref('productos', lazy=True))
    
    # Relación con múltiples fotos
    imagenes = db.relationship('FotoProducto', backref='producto', cascade='all, delete-orphan', lazy=True)

class FotoProducto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ruta = db.Column(db.String(300), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)

with app.app_context():
    db.create_all()

# -----------------------------------------------------------------------------
# AUTENTICACIÓN
# -----------------------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

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
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password')
        rol = request.form.get('rol')

        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            flash('El correo ya está registrado.')
            return redirect(url_for('registro'))

        hashed_password = generate_password_hash(password, method='scrypt')
        nuevo_usuario = Usuario(nombre=nombre, email=email, password=hashed_password, rol=rol)
        
        db.session.add(nuevo_usuario)
        db.session.commit()

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
# RUTAS DE VISTAS, PERFIL Y PRODUCTOS
# -----------------------------------------------------------------------------
@app.route('/')
def inicio():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    usuario = Usuario.query.get(session['usuario_id'])
    productos = Producto.query.all()
    carrito = session.get('carrito', [])
    total_items = sum(item['cantidad'] for item in carrito)
    return render_template('index.html', productos=productos, total_items=total_items, usuario=usuario)

@app.route('/producto/<int:id>')
def detalle_producto(id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    usuario = Usuario.query.get(session['usuario_id'])
    producto = Producto.query.get_or_404(id)
    
    # Información total de catálogo y stock total en tienda
    total_productos_tienda = Producto.query.count()
    total_unidades_tienda = db.session.query(db.func.sum(Producto.stock)).scalar() or 0

    return render_template(
        'producto_detalle.html', 
        producto=producto, 
        usuario=usuario,
        total_productos_tienda=total_productos_tienda,
        total_unidades_tienda=total_unidades_tienda
    )

@app.route('/perfil')
def vista_perfil():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    usuario = Usuario.query.get(session['usuario_id'])
    
    # Información adicional para el perfil
    mis_productos_count = Producto.query.filter_by(vendedor_id=usuario.id).count() if usuario.rol == 'vendedor' else 0
    total_catalogo_count = Producto.query.count()

    return render_template(
        'perfil.html', 
        usuario=usuario, 
        mis_productos_count=mis_productos_count,
        total_catalogo_count=total_catalogo_count
    )

@app.route('/editar_perfil', methods=['POST'])
def editar_perfil():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    usuario = Usuario.query.get(session['usuario_id'])
    descripcion = request.form.get('descripcion')
    
    if 'foto_archivo' in request.files:
        archivo = request.files['foto_archivo']
        if archivo and archivo.filename != '':
            nombre_archivo = secure_filename(f"user_{usuario.id}_{archivo.filename}")
            ruta_guardado = os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo)
            archivo.save(ruta_guardado)
            usuario.foto_perfil = f"/static/uploads/{nombre_archivo}"

    if descripcion:
        usuario.descripcion = descripcion

    db.session.commit()
    flash('Perfil actualizado con éxito.')
    return redirect(url_for('vista_perfil'))

# -----------------------------------------------------------------------------
# CARRITO Y VENDEDOR
# -----------------------------------------------------------------------------
@app.route('/cliente')
def vista_cliente():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    usuario = Usuario.query.get(session['usuario_id'])
    carrito = session.get('carrito', [])
    total_pagar = sum(item['precio'] * item['cantidad'] for item in carrito)
    return render_template('cliente.html', carrito=carrito, total_pagar=total_pagar, usuario=usuario)

@app.route('/agregar_al_carrito/<int:id>', methods=['POST'])
def agregar_al_carrito(id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    producto = Producto.query.get_or_404(id)
    if producto.stock <= 0:
        return redirect(url_for('inicio'))

    if 'carrito' not in session:
        session['carrito'] = []

    carrito = session['carrito']
    encontrado = False
    for item in carrito:
        if item['id'] == producto.id:
            if item['cantidad'] < producto.stock:
                item['cantidad'] += 1
            encontrado = True
            break
            
    if not encontrado:
        carrito.append({
            'id': producto.id,
            'nombre': producto.nombre,
            'precio': producto.precio,
            'cantidad': 1
        })

    session.modified = True
    return redirect(url_for('vista_cliente'))

@app.route('/vaciar_carrito', methods=['POST'])
def vaciar_carrito():
    session.pop('carrito', None)
    return redirect(url_for('vista_cliente'))

@app.route('/procesar_compra', methods=['POST'])
def procesar_compra():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    usuario = Usuario.query.get(session['usuario_id'])
    carrito = session.get('carrito', [])
    if not carrito:
        return redirect(url_for('vista_cliente'))

    for item in carrito:
        producto = Producto.query.get(item['id'])
        if producto:
            producto.stock = max(0, producto.stock - item['cantidad'])
    
    db.session.commit()
    session.pop('carrito', None)
    return render_template('cliente.html', compra_exitosa=True, carrito=[], total_pagar=0, usuario=usuario)

@app.route('/vendedor')
def vista_vendedor():
    if session.get('usuario_rol') != 'vendedor':
        flash('Acceso denegado: Esta área es exclusiva para vendedores.')
        return redirect(url_for('login'))

    usuario = Usuario.query.get(session['usuario_id'])
    productos = Producto.query.filter_by(vendedor_id=usuario.id).all()
    return render_template('vendedor.html', productos=productos, usuario=usuario)

@app.route('/vendedor/producto/nuevo', methods=['POST'])
def agregar_producto():
    if session.get('usuario_rol') != 'vendedor':
        return redirect(url_for('login'))

    nombre = request.form.get('nombre')
    precio = float(request.form.get('precio', 0))
    stock = int(request.form.get('stock', 1))
    descripcion = request.form.get('descripcion', 'Sin especificaciones detalladas.')
    envio = request.form.get('envio', 'Envío Nacional Estándar')
    vendedor_id = session['usuario_id']

    nuevo_prod = Producto(
        nombre=nombre,
        precio=precio,
        stock=stock,
        descripcion=descripcion,
        envio=envio,
        vendedor_id=vendedor_id
    )
    db.session.add(nuevo_prod)
    db.session.commit()

    # Procesar subida de MÚLTIPLES imágenes
    archivos = request.files.getlist('imagenes_archivos')
    for i, archivo in enumerate(archivos):
        if archivo and archivo.filename != '':
            nombre_archivo = secure_filename(f"prod_{nuevo_prod.id}_{i}_{archivo.filename}")
            ruta_guardado = os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo)
            archivo.save(ruta_guardado)
            nueva_foto = FotoProducto(ruta=f"/static/uploads/{nombre_archivo}", producto_id=nuevo_prod.id)
            db.session.add(nueva_foto)

    # Si no se subió ninguna imagen, colocar la imagen por defecto
    if not nuevo_prod.imagenes:
        foto_default = FotoProducto(ruta='/static/uploads/default_product.png', producto_id=nuevo_prod.id)
        db.session.add(foto_default)

    db.session.commit()
    return redirect(url_for('vista_vendedor'))

@app.route('/vendedor/producto/editar/<int:id>', methods=['GET', 'POST'])
def editar_producto(id):
    if session.get('usuario_rol') != 'vendedor':
        return redirect(url_for('login'))

    producto = Producto.query.get_or_404(id)
    if producto.vendedor_id != session['usuario_id']:
        flash('No tienes permiso para editar este producto.')
        return redirect(url_for('vista_vendedor'))

    if request.method == 'POST':
        producto.nombre = request.form.get('nombre')
        producto.precio = float(request.form.get('precio', 0))
        producto.stock = int(request.form.get('stock', 1))
        producto.envio = request.form.get('envio')
        producto.descripcion = request.form.get('descripcion')

        # Procesar nuevas imágenes si se seleccionaron
        archivos = request.files.getlist('imagenes_archivos')
        subio_nuevas = any(a and a.filename != '' for a in archivos)
        
        if subio_nuevas:
            # Reemplazar imágenes existentes
            FotoProducto.query.filter_by(producto_id=producto.id).delete()
            for i, archivo in enumerate(archivos):
                if archivo and archivo.filename != '':
                    nombre_archivo = secure_filename(f"prod_{producto.id}_{i}_{archivo.filename}")
                    ruta_guardado = os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo)
                    archivo.save(ruta_guardado)
                    nueva_foto = FotoProducto(ruta=f"/static/uploads/{nombre_archivo}", producto_id=producto.id)
                    db.session.add(nueva_foto)

        db.session.commit()
        flash('Producto actualizado correctamente.')
        return redirect(url_for('vista_vendedor'))

    usuario = Usuario.query.get(session['usuario_id'])
    return render_template('editar_producto.html', producto=producto, usuario=usuario)

@app.route('/vendedor/producto/eliminar/<int:id>', methods=['POST'])
def eliminar_producto(id):
    if session.get('usuario_rol') != 'vendedor':
        return redirect(url_for('login'))

    producto = Producto.query.get_or_404(id)
    db.session.delete(producto)
    db.session.commit()
    return redirect(url_for('vista_vendedor'))

if __name__ == '__main__':
    app.run(debug=True)
