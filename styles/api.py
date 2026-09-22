from flask import Blueprint, request, jsonify
from app import db
from app.models import Armas, Ordenes, DetallesOrden

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/checkout', methods=['POST'])
def checkout():
    data = request.get_json()
    items = data.get('items', [])

    if not items:
        return jsonify({'error': 'El carrito está vacío'}), 400

    # Simulación de usuario_id (en un flujo real se obtiene de session/JWT)
    usuario_id = 1  

    total_orden = 0
    detalles_a_crear = []

    # 1. Validar existencias y calcular total
    for item in items:
        producto = Armas.query.get(item['id'])
        if not producto:
            return jsonify({'error': f'Producto ID {item["id"]} no encontrado'}), 404

        if producto.stock < item['cantidad']:
            return jsonify({'error': f'Stock insuficiente para {producto.nombre}'}), 400

        subtotal = float(producto.precio) * item['cantidad']
        total_orden += subtotal

        # Guardar para procesar luego de verificar todos
        detalles_a_crear.append({
            'producto': producto,
            'cantidad': item['cantidad'],
            'precio_unitario': producto.precio
        })

    # 2. Crear la orden en la BD y actualizar stock
    try:
        nueva_orden = Ordenes(
            usuario_id=usuario_id,
            total=total_orden,
            estado='pagada'
        )
        db.session.add(nueva_orden)
        db.session.flush() # Para obtener el ID generado de la orden

        for detalle in detalles_a_crear:
            # Descontar stock
            detalle['producto'].stock -= detalle['cantidad']
            
            # Registrar detalle de orden
            nuevo_detalle = DetallesOrden(
                orden_id=nueva_orden.id,
                producto_id=detalle['producto'].id,
                cantidad=detalle['cantidad'],
                precio_unitario=detalle['precio_unitario']
            )
            db.session.add(nuevo_detalle)

        db.session.commit()
        return jsonify({'message': 'Orden procesada correctamente', 'orden_id': nueva_orden.id}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Ocurrió un error al guardar la orden: ' + str(e)}), 500