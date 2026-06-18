from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import pymysql
from datetime import datetime
import re
from functools import wraps
import uuid

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'

# ============================================
# CONFIGURACIÓN DE BASE DE DATOS MySQL
# ============================================
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'mercadoconecta360',
    'charset': 'utf8mb4'
}

def get_db_connection():
    """Obtener conexión a la base de datos MySQL"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except pymysql.Error as e:
        print(f"❌ Error de conexión a MySQL: {e}")
        return None

# ============================================
# FUNCIONES DE ACCESO A DATOS
# ============================================

def load_users():
    """Cargar usuarios desde MySQL"""
    conn = get_db_connection()
    if not conn:
        return {}
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM usuarios")
        users = cursor.fetchall()
        users_dict = {}
        for user in users:
            email = user['email']
            users_dict[email] = {
                'nombre': user['nombre'],
                'email': user['email'],
                'password': user['password'],
                'fecha_registro': user['fecha_registro'].isoformat() if user['fecha_registro'] else None,
                'is_merchant': bool(user['is_merchant']),
                'store_name': user['store_name'],
                'store_category': user['store_category'],
                'store_address': user['store_address'],
                'rating': float(user['rating']) if user['rating'] else 4.5
            }
        return users_dict
    except pymysql.Error as e:
        print(f"❌ Error al cargar usuarios: {e}")
        return {}
    finally:
        conn.close()

def save_users(users_dict):
    """Guardar usuarios en MySQL"""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        for email, data in users_dict.items():
            cursor.execute("""
                INSERT INTO usuarios (nombre, email, password, is_merchant, store_name, store_category, store_address, rating, fecha_registro)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    nombre = VALUES(nombre),
                    password = VALUES(password),
                    is_merchant = VALUES(is_merchant),
                    store_name = VALUES(store_name),
                    store_category = VALUES(store_category),
                    store_address = VALUES(store_address),
                    rating = VALUES(rating)
            """, (
                data['nombre'],
                email,
                data['password'],
                1 if data.get('is_merchant', False) else 0,
                data.get('store_name'),
                data.get('store_category'),
                data.get('store_address'),
                data.get('rating', 4.5),
                data.get('fecha_registro', datetime.now().isoformat())
            ))
        conn.commit()
        return True
    except pymysql.Error as e:
        print(f"❌ Error al guardar usuarios: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def load_products():
    """Cargar productos desde MySQL"""
    conn = get_db_connection()
    if not conn:
        return {}
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM productos ORDER BY created_at DESC")
        products = cursor.fetchall()
        products_dict = {}
        for p in products:
            pid = p['id']
            products_dict[pid] = {
                'name': p['name'],
                'price': float(p['price']),
                'description': p['description'],
                'category': p['category'],
                'icon': p['icon'] or '📦',
                'merchant_email': p['merchant_email'],
                'store_name': p['store_name'],
                'negocio_id': p['negocio_id'],
                'created_at': p['created_at'].isoformat() if p['created_at'] else None
            }
        return products_dict
    except pymysql.Error as e:
        print(f"❌ Error al cargar productos: {e}")
        return {}
    finally:
        conn.close()

def save_products(products_dict):
    """Guardar productos en MySQL"""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        for pid, data in products_dict.items():
            cursor.execute("""
                INSERT INTO productos (id, name, price, description, category, icon, merchant_email, store_name, negocio_id, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    name = VALUES(name),
                    price = VALUES(price),
                    description = VALUES(description),
                    category = VALUES(category),
                    icon = VALUES(icon),
                    store_name = VALUES(store_name),
                    negocio_id = VALUES(negocio_id)
            """, (
                pid,
                data['name'],
                data['price'],
                data.get('description'),
                data.get('category'),
                data.get('icon', '📦'),
                data['merchant_email'],
                data.get('store_name'),
                data.get('negocio_id'),
                data.get('created_at', datetime.now().isoformat())
            ))
        conn.commit()
        return True
    except pymysql.Error as e:
        print(f"❌ Error al guardar productos: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def load_contacts():
    """Cargar contactos desde MySQL"""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM contactos ORDER BY fecha DESC")
        contacts = cursor.fetchall()
        contacts_list = []
        for c in contacts:
            contacts_list.append({
                'nombre': c['nombre'],
                'email': c['email'],
                'telefono': c['telefono'],
                'asunto': c['asunto'],
                'mensaje': c['mensaje'],
                'fecha': c['fecha'].isoformat() if c['fecha'] else None
            })
        return contacts_list
    except pymysql.Error as e:
        print(f"❌ Error al cargar contactos: {e}")
        return []
    finally:
        conn.close()

def save_contacts(contacts_list):
    """Guardar contactos en MySQL"""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        for c in contacts_list:
            cursor.execute("""
                INSERT INTO contactos (nombre, email, telefono, asunto, mensaje, fecha)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                c['nombre'],
                c['email'],
                c.get('telefono'),
                c.get('asunto'),
                c['mensaje'],
                c.get('fecha', datetime.now().isoformat())
            ))
        conn.commit()
        return True
    except pymysql.Error as e:
        print(f"❌ Error al guardar contactos: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def load_negocios():
    """Cargar negocios desde MySQL"""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM negocios ORDER BY fecha_registro DESC")
        negocios = cursor.fetchall()
        negocios_list = []
        for n in negocios:
            negocios_list.append({
                'id': n['id'],
                'nombre': n['nombre'],
                'categoria': n['categoria'],
                'direccion': n['direccion'],
                'telefono': n['telefono'],
                'email': n['email'],
                'descripcion': n['descripcion'],
                'rating': str(n['rating']) if n['rating'] else '4.5',
                'fecha_registro': n['fecha_registro'].isoformat() if n['fecha_registro'] else None,
                'creado_por': n['creado_por'],
                'dueño': n['dueño']
            })
        return negocios_list
    except pymysql.Error as e:
        print(f"❌ Error al cargar negocios: {e}")
        return []
    finally:
        conn.close()

def save_negocios(negocios_list):
    """Guardar negocios en MySQL"""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        for n in negocios_list:
            cursor.execute("""
                INSERT INTO negocios (id, nombre, categoria, direccion, telefono, email, descripcion, rating, fecha_registro, creado_por, dueño)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    nombre = VALUES(nombre),
                    categoria = VALUES(categoria),
                    direccion = VALUES(direccion),
                    telefono = VALUES(telefono),
                    email = VALUES(email),
                    descripcion = VALUES(descripcion),
                    rating = VALUES(rating),
                    dueño = VALUES(dueño)
            """, (
                n['id'],
                n['nombre'],
                n.get('categoria'),
                n.get('direccion'),
                n.get('telefono'),
                n.get('email'),
                n.get('descripcion'),
                float(n.get('rating', 4.5)),
                n.get('fecha_registro', datetime.now().isoformat()),
                n.get('creado_por'),
                n.get('dueño')
            ))
        conn.commit()
        return True
    except pymysql.Error as e:
        print(f"❌ Error al guardar negocios: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def delete_negocio_from_db(negocio_id):
    """Eliminar un negocio de la base de datos"""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM productos WHERE negocio_id = %s", (negocio_id,))
        cursor.execute("DELETE FROM negocios WHERE id = %s", (negocio_id,))
        conn.commit()
        return cursor.rowcount > 0
    except pymysql.Error as e:
        print(f"❌ Error al eliminar negocio: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# ============================================
# FUNCIONES DE AUTENTICACIÓN
# ============================================

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            flash('⚠️ Acceso restringido - Inicia sesión para continuar', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

def merchant_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            flash('⚠️ Acceso restringido - Inicia sesión para continuar', 'error')
            return redirect(url_for('index'))
        if not session.get('is_merchant'):
            flash('🔒 Necesitas ser comerciante para acceder a esta sección', 'error')
            return redirect(url_for('register'))
        return f(*args, **kwargs)
    return decorated

# ============================================
# RUTAS DE LA APLICACIÓN
# ============================================

@app.route('/')
def index():
    products = load_products()
    users = load_users()
    
    merchant_list = []
    for email, data in users.items():
        if data.get('is_merchant', False):
            merchant_list.append({
                'store_name': data.get('store_name', 'Tienda sin nombre'),
                'category': data.get('store_category', 'General'),
                'rating': data.get('rating', '4.5')
            })
    
    products_list = []
    for pid, p in products.items():
        p['id'] = pid
        products_list.append(p)
    
    return render_template('index.html',
                          session=session,
                          error=None,
                          products=products_list[:12],
                          merchants=merchant_list[:6],
                          search_results=None,
                          search_query=None)

@app.route('/search')
def search():
    query = request.args.get('q', '').strip().lower()
    products = load_products()
    users = load_users()
    
    results = []
    for pid, p in products.items():
        if query in p.get('name', '').lower() or query in p.get('store_name', '').lower():
            p['id'] = pid
            results.append(p)
    
    merchant_list = []
    for email, data in users.items():
        if data.get('is_merchant', False):
            merchant_list.append({
                'store_name': data.get('store_name', 'Tienda'),
                'category': data.get('store_category', 'General'),
                'rating': data.get('rating', '4.5')
            })
    
    products_list = []
    for pid, p in products.items():
        p['id'] = pid
        products_list.append(p)
    
    return render_template('index.html',
                          session=session,
                          error=None,
                          products=products_list[:12],
                          merchants=merchant_list[:6],
                          search_results=results,
                          search_query=query)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        is_merchant = request.form.get('is_merchant') == 'yes'
        
        if not nombre or not email or not password:
            flash('⚠️ Todos los campos son obligatorios', 'error')
            return render_template('register.html')
        
        if password != confirm:
            flash('❌ Las contraseñas no coinciden', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('❌ Mínimo 6 caracteres para la contraseña', 'error')
            return render_template('register.html')
        
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            flash('❌ Email inválido', 'error')
            return render_template('register.html')
        
        users = load_users()
        if email in users:
            flash('❌ Este correo ya está registrado', 'error')
            return render_template('register.html')
        
        user_data = {
            'nombre': nombre,
            'email': email,
            'password': password,
            'fecha_registro': datetime.now().isoformat(),
            'is_merchant': is_merchant
        }
        
        negocio_id = None
        
        if is_merchant:
            store_name = request.form.get('store_name', '').strip()
            if not store_name:
                flash('❌ El nombre de la tienda es obligatorio', 'error')
                return render_template('register.html')
            
            store_category = request.form.get('store_category', '')
            store_address = request.form.get('store_address', '')
            
            user_data.update({
                'store_name': store_name,
                'store_category': store_category,
                'store_address': store_address,
                'rating': 4.5
            })
            
            negocios = load_negocios()
            negocio_id = str(uuid.uuid4())[:8]
            
            existing_ids = [n['id'] for n in negocios]
            while negocio_id in existing_ids:
                negocio_id = str(uuid.uuid4())[:8]
            
            negocios.append({
                'id': negocio_id,
                'nombre': store_name,
                'categoria': store_category,
                'direccion': store_address,
                'telefono': '',
                'email': email,
                'descripcion': f'Negocio registrado por {nombre}',
                'rating': '4.5',
                'fecha_registro': datetime.now().isoformat(),
                'creado_por': email,
                'dueño': nombre
            })
            save_negocios(negocios)
        
        users[email] = user_data
        save_users(users)
        
        if is_merchant:
            flash(f'🚀 ¡Registro exitoso! Tu negocio "{store_name}" ha sido creado.', 'success')
        else:
            flash('🚀 ¡Registro exitoso! Bienvenido a T.C.E.', 'success')
        
        return render_template('register.html')
    
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '').strip()
    users = load_users()
    
    if email in users and users[email]['password'] == password:
        session['logged_in'] = True
        session['user_email'] = email
        session['user_nombre'] = users[email]['nombre']
        session['is_merchant'] = users[email].get('is_merchant', False)
        flash(f'🔥 ¡Bienvenido {session["user_nombre"]}!', 'success')
        return redirect(url_for('index'))
    else:
        flash('❌ Correo o contraseña incorrectos', 'error')
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    flash('👋 Sesión cerrada', 'success')
    return redirect(url_for('index'))

@app.route('/about')
def about():
    return render_template('about.html', session=session)

@app.route('/contacto', methods=['GET', 'POST'])
def contacto():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip()
        telefono = request.form.get('telefono', '').strip()
        asunto = request.form.get('asunto', '')
        mensaje = request.form.get('mensaje', '').strip()

        if not nombre or not email or not mensaje:
            flash('⚠️ Nombre, email y mensaje son obligatorios', 'error')
            return render_template('contacto.html', session=session)

        contacts = load_contacts()
        contacts.append({
            'nombre': nombre,
            'email': email,
            'telefono': telefono,
            'asunto': asunto,
            'mensaje': mensaje,
            'fecha': datetime.now().isoformat()
        })
        save_contacts(contacts)

        flash('✅ ¡Mensaje enviado! Te responderemos en menos de 24 horas.', 'success')
        return render_template('contacto.html', session=session)

    return render_template('contacto.html', session=session)

# ==================== RUTAS DE NEGOCIOS ====================

@app.route('/negocios')
def negocios():
    negocios_list = load_negocios()
    return render_template('negocios.html', session=session, negocios=negocios_list)

@app.route('/negocios/ver/<negocio_id>')
def ver_negocio(negocio_id):
    negocios = load_negocios()
    negocio = None
    for n in negocios:
        if n.get('id') == negocio_id:
            negocio = n
            break
    
    if not negocio:
        flash('❌ Negocio no encontrado', 'error')
        return redirect(url_for('negocios'))
    
    products = load_products()
    productos_del_negocio = []
    email_negocio = negocio.get('email', '')
    
    for pid, p in products.items():
        if p.get('merchant_email') == email_negocio or p.get('negocio_id') == negocio_id:
            p['id'] = pid
            productos_del_negocio.append(p)
    
    return render_template('ver_negocio.html', 
                          session=session, 
                          negocio=negocio, 
                          productos=productos_del_negocio)

@app.route('/negocios/agregar', methods=['GET', 'POST'])
def agregar_negocio():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        categoria = request.form.get('categoria', '')
        direccion = request.form.get('direccion', '').strip()
        telefono = request.form.get('telefono', '').strip()
        email = request.form.get('email', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        rating = request.form.get('rating', '4.5')
        dueño = request.form.get('dueño', '').strip() or session.get('user_nombre', 'Anónimo')

        if not nombre:
            flash('❌ El nombre del negocio es obligatorio', 'error')
            return render_template('agregar_negocio.html', session=session)

        negocios = load_negocios()
        nuevo_id = str(uuid.uuid4())[:8]
        
        existing_ids = [n['id'] for n in negocios]
        while nuevo_id in existing_ids:
            nuevo_id = str(uuid.uuid4())[:8]

        negocios.append({
            'id': nuevo_id,
            'nombre': nombre,
            'categoria': categoria,
            'direccion': direccion,
            'telefono': telefono,
            'email': email,
            'descripcion': descripcion,
            'rating': rating,
            'fecha_registro': datetime.now().isoformat(),
            'creado_por': session.get('user_email', 'anonimo'),
            'dueño': dueño
        })
        save_negocios(negocios)

        flash('✅ Negocio registrado exitosamente', 'success')
        return redirect(url_for('negocios'))

    return render_template('agregar_negocio.html', session=session)

@app.route('/negocios/editar/<negocio_id>', methods=['GET', 'POST'])
def editar_negocio(negocio_id):
    negocios = load_negocios()
    negocio = None
    for n in negocios:
        if n.get('id') == negocio_id:
            negocio = n
            break

    if not negocio:
        flash('❌ Negocio no encontrado', 'error')
        return redirect(url_for('negocios'))

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        categoria = request.form.get('categoria', '')
        direccion = request.form.get('direccion', '').strip()
        telefono = request.form.get('telefono', '').strip()
        email = request.form.get('email', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        rating = request.form.get('rating', '4.5')
        dueño = request.form.get('dueño', '').strip()

        if not nombre:
            flash('❌ El nombre del negocio es obligatorio', 'error')
            return render_template('editar_negocio.html', session=session, negocio=negocio)

        negocio['nombre'] = nombre
        negocio['categoria'] = categoria
        negocio['direccion'] = direccion
        negocio['telefono'] = telefono
        negocio['email'] = email
        negocio['descripcion'] = descripcion
        negocio['rating'] = rating
        if dueño:
            negocio['dueño'] = dueño
        negocio['fecha_edicion'] = datetime.now().isoformat()

        save_negocios(negocios)
        flash('✅ Negocio actualizado exitosamente', 'success')
        return redirect(url_for('negocios'))

    return render_template('editar_negocio.html', session=session, negocio=negocio)

@app.route('/negocios/eliminar/<negocio_id>')
def eliminar_negocio(negocio_id):
    if not session.get('logged_in') or not session.get('is_merchant'):
        flash('❌ No tienes permiso para eliminar negocios', 'error')
        return redirect(url_for('negocios'))
    
    eliminado = delete_negocio_from_db(negocio_id)
    
    if eliminado:
        flash('✅ Negocio eliminado correctamente de la base de datos', 'success')
    else:
        flash('❌ No se pudo eliminar el negocio o no existe', 'error')
    
    return redirect(url_for('negocios'))

# ==================== RUTAS DE COMERCIANTE ====================

@app.route('/merchant/dashboard')
@merchant_required
def merchant_dashboard():
    products = load_products()
    user_email = session.get('user_email')
    
    merchant_products = []
    for pid, p in products.items():
        if p.get('merchant_email') == user_email:
            p['id'] = pid
            merchant_products.append(p)
    
    return render_template('merchant/dashboard.html', session=session, products=merchant_products)

@app.route('/merchant/add_product', methods=['GET', 'POST'])
@merchant_required
def add_product():
    negocio_id = request.args.get('negocio_id', '')
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        price = request.form.get('price', '').strip()
        
        if not name or not price:
            flash('❌ Nombre y precio son obligatorios', 'error')
            return render_template('merchant/add_product.html', session=session, negocio_id=negocio_id)
        
        try:
            price = float(price)
        except ValueError:
            flash('❌ Precio inválido', 'error')
            return render_template('merchant/add_product.html', session=session, negocio_id=negocio_id)
        
        products = load_products()
        pid = str(uuid.uuid4())[:8]
        
        while pid in products:
            pid = str(uuid.uuid4())[:8]
        
        users = load_users()
        user_email = session.get('user_email')
        store_name = users.get(user_email, {}).get('store_name', 'Mi Tienda')
        
        negocio_nombre = store_name
        if negocio_id:
            negocios = load_negocios()
            for n in negocios:
                if n.get('id') == negocio_id:
                    negocio_nombre = n.get('nombre', store_name)
                    break
        
        products[pid] = {
            'name': name,
            'price': price,
            'description': request.form.get('description', ''),
            'category': request.form.get('category', ''),
            'icon': request.form.get('icon', '📦'),
            'merchant_email': user_email,
            'store_name': negocio_nombre,
            'negocio_id': negocio_id,
            'created_at': datetime.now().isoformat()
        }
        save_products(products)
        flash('✅ Producto agregado exitosamente', 'success')
        
        if negocio_id:
            return redirect(url_for('ver_negocio', negocio_id=negocio_id))
        return redirect(url_for('merchant_dashboard'))
    
    return render_template('merchant/add_product.html', session=session, negocio_id=negocio_id)

@app.route('/merchant/delete_product/<product_id>')
@merchant_required
def delete_product(product_id):
    products = load_products()
    if product_id in products and products[product_id].get('merchant_email') == session.get('user_email'):
        del products[product_id]
        save_products(products)
        flash('✅ Producto eliminado', 'success')
    else:
        flash('❌ Producto no encontrado', 'error')
    return redirect(url_for('merchant_dashboard'))

# ============================================
# INICIALIZACIÓN CON DATOS DE PRUEBA
# ============================================

def init_demo_data():
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM usuarios")
        result = cursor.fetchone()
        
        if result[0] == 0:
            print("📦 Insertando datos de demostración...")
            
            cursor.execute("""
                INSERT INTO usuarios (nombre, email, password, is_merchant, store_name, store_category, store_address, rating)
                VALUES ('Usuario Demo', 'demo@tce.com', '123456', 1, 'TCE Store', 'Tecnología', 'Digital Hub 404', 4.9)
            """)
            
            cursor.execute("""
                INSERT INTO negocios (id, nombre, categoria, direccion, telefono, email, descripcion, rating, creado_por, dueño)
                VALUES ('tce001', 'TCE Store', 'Tecnología', 'Digital Hub 404', '+52 55 4040 4040', 'demo@tce.com', 
                        'Tienda oficial de T.C.E - Productos exclusivos para la élite del código', 4.9, 'demo@tce.com', 'Usuario Demo')
            """)
            
            productos_demo = [
                ('prod1', 'TCE Hoodie Elite', 899.00, 'Hoodie exclusivo de la élite del código', 'Moda', '👕', 'demo@tce.com', 'TCE Store', 'tce001'),
                ('prod2', 'TCE Cap Pro', 299.00, 'Gorra oficial de los titanes', 'Moda', '🧢', 'demo@tce.com', 'TCE Store', 'tce001'),
                ('prod3', 'TCE Bottle Elite', 399.00, 'Botella térmica de edición limitada', 'Accesorios', '🍶', 'demo@tce.com', 'TCE Store', 'tce001')
            ]
            for p in productos_demo:
                cursor.execute("""
                    INSERT INTO productos (id, name, price, description, category, icon, merchant_email, store_name, negocio_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, p)
            
            conn.commit()
            print("✅ Datos de demostración insertados correctamente")
            print("🔑 Usuario Demo: demo@tce.com / 123456")
    except pymysql.Error as e:
        print(f"❌ Error al inicializar datos: {e}")
        conn.rollback()
    finally:
        conn.close()

# ============================================
# EJECUCIÓN DE LA APLICACIÓN
# ============================================

if __name__ == '__main__':
    init_demo_data()
    app.run(debug=True, host='0.0.0.0', port=5000)