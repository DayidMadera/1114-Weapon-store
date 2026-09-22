// Obtener carrito de localStorage o inicializarlo vacío
function getCart() {
    return JSON.parse(localStorage.getItem('cart')) || [];
}

function saveCart(cart) {
    localStorage.setItem('cart', JSON.stringify(cart));
}

// Agregar un producto al carrito
function agregarAlCarrito(id, nombre, precio) {
    let cart = getCart();
    let item = cart.find(p => p.id === id);

    if (item) {
        item.cantidad += 1;
    } else {
        cart.push({ id, nombre, precio: parseFloat(precio), cantidad: 1 });
    }

    saveCart(cart);
    alert(`${nombre} fue agregado al carrito.`);
    renderCart();
}

// Cambiar la cantidad de un ítem
function cambiarCantidad(id, cambio) {
    let cart = getCart();
    let item = cart.find(p => p.id === id);

    if (item) {
        item.cantidad += cambio;
        if (item.cantidad <= 0) {
            cart = cart.filter(p => p.id !== id);
        }
    }

    saveCart(cart);
    renderCart();
}

// Eliminar un producto del carrito
function eliminarDelCarrito(id) {
    let cart = getCart().filter(p => p.id !== id);
    saveCart(cart);
    renderCart();
}

// Renderizar la tabla del carrito
function renderCart() {
    const cart = getCart();
    const tbody = document.getElementById('cart-items');
    const totalElement = document.getElementById('cart-total');

    if (!tbody || !totalElement) return;

    tbody.innerHTML = '';
    let total = 0;

    if (cart.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center">El carrito está vacío.</td></tr>';
        totalElement.innerText = '$0.00';
        return;
    }

    cart.forEach(item => {
        let subtotal = item.precio * item.cantidad;
        total += subtotal;

        tbody.innerHTML += `
            <tr>
                <td>${item.nombre}</td>
                <td>$${item.precio.toFixed(2)}</td>
                <td>
                    <button class="btn btn-sm btn-outline-secondary" onclick="cambiarCantidad(${item.id}, -1)">-</button>
                    <span class="mx-2">${item.cantidad}</span>
                    <button class="btn btn-sm btn-outline-secondary" onclick="cambiarCantidad(${item.id}, 1)">+</button>
                </td>
                <td>$${subtotal.toFixed(2)}</td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="eliminarDelCarrito(${item.id})">Eliminar</button>
                </td>
            </tr>
        `;
    });

    totalElement.innerText = `$${total.toFixed(2)}`;
}

// Enviar carrito a la API para procesar el Checkout
async function procesarCompra() {
    const cart = getCart();
    if (cart.length === 0) {
        alert('Tu carrito está vacío.');
        return;
    }

    try {
        const response = await fetch('/api/checkout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ items: cart })
        });

        const data = await response.json();

        if (response.ok) {
            alert('¡Compra realizada con éxito! Código de Orden: #' + data.orden_id);
            localStorage.removeItem('cart');
            window.location.href = '/';
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        console.error('Error al procesar la compra:', error);
        alert('Hubo un problema de conexión al procesar la compra.');
    }
}

// Inicialización de escuchadores de eventos al cargar la página
document.addEventListener('DOMContentLoaded', () => {
    // Renderiza el carrito si existe la tabla
    renderCart();

    // Captura clics en botones con la clase 'btn-agregar'
    document.addEventListener('click', (e) => {
        if (e.target && e.target.classList.contains('btn-agregar')) {
            const btn = e.target;
            const id = parseInt(btn.getAttribute('data-id'));
            const nombre = btn.getAttribute('data-nombre');
            const precio = parseFloat(btn.getAttribute('data-precio'));

            agregarAlCarrito(id, nombre, precio);
        }
    });
});