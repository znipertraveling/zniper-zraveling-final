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

# Datos por defecto (incluye página de inicio)
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
    "instagram": "https://instagram.com/znipertraveling",
    "inicio": {
        "bienvenida": "Bienvenido a mi mundo visual",
        "texto": "Soy un fotógrafo de calle obsesionado con el instante decisivo. Aquí encontrarás mi mirada, mis sombras, mis ciudades.",
        "imagen": ""  // URL de la foto de portada (opcional)
    }
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
    return send_from_directory('static', 'index.html')  # Nuevo archivo principal

@app.route('/inicio')
def inicio():
    return send_from_directory('static', 'inicio.html')

@app.route('/galeria')
def galeria():
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
        "instagram": datos.get("instagram", "https://instagram.com/znipertraveling"),
        "inicio": datos.get("inicio", {"bienvenida": "", "texto": "", "imagen": ""})
    })

@app.route('/api/datos', methods=['POST'])
@login_required
def update_datos():
    datos = cargar_datos()
    data = request.json
    for key in ['titulo', 'subtitulo', 'firma', 'categorias', 'moderacion_comentarios', 'instagram']:
        if key in data:
            datos[key] = data[key]
    if 'inicio' in data:
        datos['inicio'] = data['inicio']
    guardar_datos(datos)
    return jsonify({"success": True})

# (El resto de API: categorías, fotos, blog, páginas, comentarios, etc. se mantienen igual)
# Incluir aquí todas las demás rutas API que ya tenías (no las repito por longitud, pero deben estar)
# Por razones de espacio, asumiré que ya las tienes en tu archivo anterior.
# Si necesitas el bloque completo, dímelo y lo añado.

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=True)
