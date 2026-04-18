from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for
from flask_cors import CORS
import json
import os
import hashlib
import uuid
from functools import wraps
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'zniper-secreto-2026'
CORS(app)

# Configuración
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
if not os.path.exists(DATOS_FILE):
    with open(DATOS_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            "titulo": "Zniper Zraveling",
            "subtitulo": "fotografía de autor · calle como poema · instante como herida",
            "firma": "— mi ojo, mi sombra, mi ciudad —",
            "categorias": ["Soledades", "Silencios", "Miradas"],
            "fotos": [],
            "proximo_id": 1
        }, f, indent=2, ensure_ascii=False)

if not os.path.exists(CREDENCIALES_FILE):
    with open(CREDENCIALES_FILE, 'w') as f:
        json.dump({
            "nickname": "zniper",
            "password_hash": hashlib.sha256("zniper2026".encode()).hexdigest()
        }, f)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def cargar_datos():
    with open(DATOS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def guardar_datos(datos):
    with open(DATOS_FILE, 'w', encoding='utf-8') as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)

# ========== RUTAS PÚBLICAS ==========
@app.route('/')
def index():
    return send_from_directory('static', 'galeria.html')

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
    with open(CREDENCIALES_FILE) as f:
        cred = json.load(f)
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
        "fotos": datos["fotos"]
    })

@app.route('/api/datos', methods=['POST'])
@login_required
def update_datos():
    datos = cargar_datos()
    data = request.json
    if 'titulo' in data:
        datos['titulo'] = data['titulo']
    if 'subtitulo' in data:
        datos['subtitulo'] = data['subtitulo']
    if 'firma' in data:
        datos['firma'] = data['firma']
    if 'categorias' in data:
        datos['categorias'] = data['categorias']
    guardar_datos(datos)
    return jsonify({"success": True})

@app.route('/api/categorias/reordenar', methods=['POST'])
@login_required
def reordenar_categorias():
    datos = cargar_datos()
    nuevas_categorias = request.json.get('categorias', [])
    datos['categorias'] = nuevas_categorias
    guardar_datos(datos)
    return jsonify({"success": True})

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
    with open(CREDENCIALES_FILE) as f:
        cred = json.load(f)
    if 'nickname' in data and data['nickname']:
        cred['nickname'] = data['nickname']
    if 'password' in data and data['password']:
        cred['password_hash'] = hashlib.sha256(data['password'].encode()).hexdigest()
    with open(CREDENCIALES_FILE, 'w') as f:
        json.dump(cred, f)
    return jsonify({"success": True})

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 ZNIPER ZRAVELING - SERVIDOR COMPLETO")
    print("=" * 50)
    print("🔗 Galería: http://127.0.0.1:5002")
    print("🔐 Admin: http://127.0.0.1:5002/admin")
    print("📝 Login: http://127.0.0.1:5002/login")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5002, debug=True)
