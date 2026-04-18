from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for
from flask_cors import CORS
import json
import os
import hashlib
import uuid
from functools import wraps
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'zniper-secreto-2026'
CORS(app)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

DATOS_FILE = 'datos.json'
CREDENCIALES_FILE = 'credenciales.json'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Datos por defecto
DATOS_POR_DEFECTO = {
    "titulo": "Zniper Zraveling",
    "subtitulo": "fotografía de autor · calle como poema · instante como herida",
    "firma": "— mi ojo, mi sombra, mi ciudad —",
    "categorias": ["Soledades", "Silencios", "Miradas"],
    "fotos": [],
    "proximo_id": 1,
    "blog": [],
    "proximo_blog_id": 1,
    "paginas": [
        {"id": 1, "titulo": "Sobre mí", "slug": "sobre-mi", "contenido": "Escribe aquí tu biografía...", "visible": True}
    ],
    "proximo_pagina_id": 2,
    "comentarios": [],
    "proximo_comentario_id": 1,
    "moderacion_comentarios": True,
    "instagram": "https://instagram.com/znipertraveling"
}

CREDENCIALES_POR_DEFECTO = {
    "nickname": "zniper",
    "password_hash": hashlib.sha256("zniper2026".encode()).hexdigest()
}

def cargar_datos():
    if not os.path.exists(DATOS_FILE):
        with open(DATOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(DATOS_POR_DEFECTO, f, indent=2, ensure_ascii=False)
    with open(DATOS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def guardar_datos(datos):
    with open(DATOS_FILE, 'w', encoding='utf-8') as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)

def cargar_credenciales():
    if not os.path.exists(CREDENCIALES_FILE):
        with open(CREDENCIALES_FILE, 'w') as f:
            json.dump(CREDENCIALES_POR_DEFECTO, f, indent=2)
    with open(CREDENCIALES_FILE, 'r') as f:
        return json.load(f)

def guardar_credenciales(credenciales):
    with open(CREDENCIALES_FILE, 'w') as f:
        json.dump(credenciales, f, indent=2)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# ========== RUTAS PÚBLICAS ==========
@app.route('/')
def index():
    return send_from_directory('static', 'galeria.html')

@app.route('/blog')
def blog():
    return send_from_directory('static', 'blog.html')

@app.route('/blog/<int:id>')
def articulo(id):
    return send_from_directory('static', 'articulo.html')

@app.route('/pagina/<slug>')
def pagina(slug):
    return send_from_directory('static', 'pagina.html')

@app.route('/login')
def login_page():
    return send_from_directory('static', 'login.html')

@app.route('/admin')
@login_required
def admin():
    return send_from_directory('static', 'admin.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# ========== API ==========
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    cred = cargar_credenciales()
    if data.get('nickname') == cred['nickname'] and hashlib.sha256(data.get('password', '').encode()).hexdigest() == cred['password_hash']:
        session['logged_in'] = True
        return jsonify({"success": True})
    return jsonify({"success": False}), 401

@app.route('/api/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/api/datos')
def get_datos():
    datos = cargar_datos()
    return jsonify({
        "titulo": datos["titulo"],
        "subtitulo": datos["subtitulo"],
        "firma": datos["firma"],
        "categorias": datos["categorias"],
        "fotos": datos["fotos"],
        "blog": datos["blog"],
        "paginas": datos["paginas"],
        "comentarios": datos["comentarios"],
        "moderacion_comentarios": datos.get("moderacion_comentarios", True),
        "instagram": datos.get("instagram", "https://instagram.com/znipertraveling")
    })

@app.route('/api/datos', methods=['POST'])
@login_required
def update_datos():
    datos = cargar_datos()
    data = request.json
    for key in ['titulo', 'subtitulo', 'firma', 'categorias', 'moderacion_comentarios', 'instagram']:
        if key in data:
            datos[key] = data[key]
    guardar_datos(datos)
    return jsonify({"success": True})

@app.route('/api/categorias/reordenar', methods=['POST'])
@login_required
def reordenar_categorias():
    datos = cargar_datos()
    datos['categorias'] = request.json.get('categorias', [])
    guardar_datos(datos)
    return jsonify({"success": True})

# Blog
@app.route('/api/blog', methods=['POST'])
@login_required
def add_blog():
    datos = cargar_datos()
    data = request.json
    nuevo = {
        "id": datos["proximo_blog_id"],
        "titulo": data.get('titulo', 'Sin título'),
        "texto": data.get('texto', ''),
        "imagen": data.get('imagen', ''),
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    datos["blog"].append(nuevo)
    datos["proximo_blog_id"] += 1
    guardar_datos(datos)
    return jsonify({"success": True, "articulo": nuevo})

@app.route('/api/blog/<int:id>', methods=['PUT'])
@login_required
def update_blog(id):
    datos = cargar_datos()
    data = request.json
    for art in datos["blog"]:
        if art["id"] == id:
            art.update(data)
            break
    guardar_datos(datos)
    return jsonify({"success": True})

@app.route('/api/blog/<int:id>', methods=['DELETE'])
@login_required
def delete_blog(id):
    datos = cargar_datos()
    datos["blog"] = [a for a in datos["blog"] if a["id"] != id]
    guardar_datos(datos)
    return jsonify({"success": True})

# Páginas
@app.route('/api/paginas', methods=['POST'])
@login_required
def add_pagina():
    datos = cargar_datos()
    data = request.json
    slug = data.get('slug', data.get('titulo', '').lower().replace(' ', '-'))
    nueva = {
        "id": datos["proximo_pagina_id"],
        "titulo": data.get('titulo', 'Nueva página'),
        "slug": slug,
        "contenido": data.get('contenido', ''),
        "visible": data.get('visible', True)
    }
    datos["paginas"].append(nueva)
    datos["proximo_pagina_id"] += 1
    guardar_datos(datos)
    return jsonify({"success": True, "pagina": nueva})

@app.route('/api/paginas/<int:id>', methods=['PUT'])
@login_required
def update_pagina(id):
    datos = cargar_datos()
    data = request.json
    for pag in datos["paginas"]:
        if pag["id"] == id:
            pag.update(data)
            if 'titulo' in data and 'slug' not in data:
                pag['slug'] = data['titulo'].lower().replace(' ', '-')
            break
    guardar_datos(datos)
    return jsonify({"success": True})

@app.route('/api/paginas/<int:id>', methods=['DELETE'])
@login_required
def delete_pagina(id):
    datos = cargar_datos()
    datos["paginas"] = [p for p in datos["paginas"] if p["id"] != id]
    guardar_datos(datos)
    return jsonify({"success": True})

# Comentarios
@app.route('/api/comentarios', methods=['POST'])
def add_comentario():
    datos = cargar_datos()
    data = request.json
    nuevo = {
        "id": datos["proximo_comentario_id"],
        "tipo": data.get('tipo'),
        "entidad_id": data.get('entidad_id'),
        "nickname": data.get('nickname', 'Anónimo'),
        "calificacion": data.get('calificacion', 0),
        "texto": data.get('texto', ''),
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "aprobado": datos.get("moderacion_comentarios", True),
        "respuestas": []
    }
    datos["comentarios"].append(nuevo)
    datos["proximo_comentario_id"] += 1
    guardar_datos(datos)
    return jsonify({"success": True, "comentario": nuevo})

@app.route('/api/comentarios/<int:id>/aprobar', methods=['POST'])
@login_required
def aprobar_comentario(id):
    datos = cargar_datos()
    for com in datos["comentarios"]:
        if com["id"] == id:
            com["aprobado"] = True
            break
    guardar_datos(datos)
    return jsonify({"success": True})

@app.route('/api/comentarios/<int:id>', methods=['DELETE'])
@login_required
def delete_comentario(id):
    datos = cargar_datos()
    datos["comentarios"] = [c for c in datos["comentarios"] if c["id"] != id]
    guardar_datos(datos)
    return jsonify({"success": True})

@app.route('/api/comentarios/<int:id>/responder', methods=['POST'])
@login_required
def responder_comentario(id):
    datos = cargar_datos()
    data = request.json
    respuesta = {
        "nickname": "Zniper",
        "texto": data.get('texto', ''),
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    for com in datos["comentarios"]:
        if com["id"] == id:
            com["respuestas"].append(respuesta)
            break
    guardar_datos(datos)
    return jsonify({"success": True})

# Fotos
@app.route('/api/fotos', methods=['POST'])
@login_required
def add_foto():
    datos = cargar_datos()
    data = request.json
    nueva_foto = {
        "id": datos["proximo_id"],
        "titulo": data.get('titulo', 'Sin título'),
        "categoria": data.get('categoria', datos['categorias'][0] if datos['categorias'] else 'General'),
        "archivo": data.get('archivo'),
        "orientacion": data.get('orientacion', 'horizontal')
    }
    datos["fotos"].append(nueva_foto)
    datos["proximo_id"] += 1
    guardar_datos(datos)
    return jsonify({"success": True, "foto": nueva_foto})

@app.route('/api/fotos/<int:foto_id>', methods=['PUT'])
@login_required
def update_foto(foto_id):
    datos = cargar_datos()
    data = request.json
    for foto in datos["fotos"]:
        if foto["id"] == foto_id:
            if 'titulo' in data:
                foto['titulo'] = data['titulo']
            if 'categoria' in data:
                foto['categoria'] = data['categoria']
            if 'orientacion' in data:
                foto['orientacion'] = data['orientacion']
            break
    guardar_datos(datos)
    return jsonify({"success": True})

@app.route('/api/fotos/<int:foto_id>', methods=['DELETE'])
@login_required
def delete_foto(foto_id):
    datos = cargar_datos()
    datos["fotos"] = [f for f in datos["fotos"] if f["id"] != foto_id]
    guardar_datos(datos)
    return jsonify({"success": True})

@app.route('/api/fotos/reordenar', methods=['POST'])
@login_required
def reordenar_fotos():
    datos = cargar_datos()
    nuevos_ids = request.json.get('ids', [])
    fotos_dict = {f["id"]: f for f in datos["fotos"]}
    datos["fotos"] = [fotos_dict[id_] for id_ in nuevos_ids if id_ in fotos_dict]
    guardar_datos(datos)
    return jsonify({"success": True})

@app.route('/api/subir-foto', methods=['POST'])
@login_required
def subir_foto():
    if 'foto' not in request.files:
        return jsonify({"error": "No se envió ninguna foto"}), 400
    file = request.files['foto']
    if file.filename == '':
        return jsonify({"error": "Archivo vacío"}), 400
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return jsonify({"success": True, "archivo": f"/uploads/{filename}"})
    return jsonify({"error": "Formato no permitido"}), 400

@app.route('/api/credenciales', methods=['POST'])
@login_required
def update_credenciales():
    data = request.json
    cred = cargar_credenciales()
    if 'nickname' in data and data['nickname']:
        cred['nickname'] = data['nickname']
    if 'password' in data and data['password']:
        cred['password_hash'] = hashlib.sha256(data['password'].encode()).hexdigest()
    guardar_credenciales(cred)
    return jsonify({"success": True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=True)
