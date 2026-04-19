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

DATOS_POR_DEFECTO = {
    "titulo": "Zniper Zraveling",
    "subtitulo": "fotografía de autor · calle como poema",
    "firma": "— mi ojo, mi sombra, mi ciudad —",
    "categorias": ["Soledades", "Silencios", "Miradas"],
    "fotos": [],
    "proximo_id": 1,
    "blog": [],
    "proximo_blog_id": 1,
    "series": [],
    "proximo_serie_id": 1,
    "paginas": [
        {"id": 1, "titulo": "Sobre mí", "slug": "sobre-mi", "tipo": "sobremi", "contenido": [], "visible": True}
    ],
    "proximo_pagina_id": 2,
    "comentarios": [],
    "proximo_comentario_id": 1,
    "moderacion_comentarios": False,
    "texto_pie": "Zniper Traveling © 2025 · @zniipertraveling",
    "redes_sociales": [
        {"nombre": "Instagram", "url": "https://instagram.com/zniipertraveling", "icono": "📷"}
    ],
    "inicio": {
        "titulo": "Bienvenido a mi mundo visual",
        "pensamiento": "",
        "num_fotos": 4,
        "mostrar_subtitulo": True,
        "mostrar_blog_caja": True,
        "num_entradas_blog": 3,
        "etiqueta_fotos": "Reciente",
        "etiqueta_blog": "Bitácora",
        "etiqueta_pensamiento": "Pensamiento"
    }
}

CREDENCIALES_POR_DEFECTO = {"nickname": "zniper", "password_hash": hashlib.sha256("zniper2026".encode()).hexdigest()}

def cargar_datos():
    if not os.path.exists(DATOS_FILE):
        with open(DATOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(DATOS_POR_DEFECTO, f, indent=2, ensure_ascii=False)
    with open(DATOS_FILE, 'r', encoding='utf-8') as f:
        datos = json.load(f)
    if migrar_datos(datos):
        guardar_datos(datos)
    return datos

def guardar_datos(datos):
    with open(DATOS_FILE, 'w', encoding='utf-8') as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)

def migrar_datos(datos):
    """Completa campos nuevos y migra blog/páginas sin romper datos viejos."""
    changed = False
    ini_def = DATOS_POR_DEFECTO["inicio"]
    if "inicio" not in datos or not isinstance(datos["inicio"], dict):
        datos["inicio"] = dict(ini_def)
        changed = True
    else:
        for k, v in ini_def.items():
            if k not in datos["inicio"]:
                datos["inicio"][k] = v
                changed = True
    for art in datos.get("blog", []):
        if not art.get("bloques"):
            bl = []
            if art.get("texto"):
                bl.append({"tipo": "texto", "texto": art["texto"]})
            if art.get("imagen"):
                bl.append({"tipo": "imagen", "archivo": art["imagen"], "pie": ""})
            if not bl:
                bl = [{"tipo": "texto", "texto": ""}]
            art["bloques"] = bl
            changed = True
    if "texto_pie" not in datos:
        datos["texto_pie"] = DATOS_POR_DEFECTO["texto_pie"]
        changed = True
    for pag in datos.get("paginas", []):
        if pag.get("tipo") == "normal":
            if pag.get("contenido") and isinstance(pag["contenido"], str) and pag["contenido"].strip() and not pag.get("bloques"):
                pag["bloques"] = [{"tipo": "texto", "texto": pag["contenido"]}]
                changed = True
            elif not pag.get("bloques"):
                pag["bloques"] = [{"tipo": "texto", "texto": ""}]
                changed = True
        if pag.get("tipo") == "sobremi":
            if pag.get("contenido") and not pag.get("bloques"):
                bl = []
                for bloque in pag["contenido"]:
                    if bloque.get("imagen"):
                        bl.append({"tipo": "imagen", "archivo": bloque["imagen"], "pie": ""})
                    if bloque.get("texto"):
                        bl.append({"tipo": "texto", "texto": bloque["texto"]})
                if not bl:
                    bl = [{"tipo": "texto", "texto": ""}]
                pag["bloques"] = bl
                changed = True
            elif not pag.get("bloques"):
                pag["bloques"] = [{"tipo": "texto", "texto": ""}]
                changed = True
    return changed

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
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated

# Rutas públicas
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/admin')
@login_required
def admin():
    return send_from_directory('static', 'admin.html')

@app.route('/login')
def login_page():
    return send_from_directory('static', 'login.html')

@app.route('/blog/<int:id>')
def blog_articulo(id):
    return send_from_directory('static', 'articulo.html')

@app.route('/serie/<int:id>')
def serie_pagina(id):
    return send_from_directory('static', 'serie.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# API
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
        "series": datos["series"],
        "paginas": datos["paginas"],
        "comentarios": datos["comentarios"],
        "moderacion_comentarios": datos.get("moderacion_comentarios", False),
        "redes_sociales": datos.get("redes_sociales", []),
        "texto_pie": datos.get("texto_pie", "Zniper Traveling © 2025"),
        "inicio": datos.get("inicio", {"titulo": "Bienvenido"})
    })

@app.route('/api/datos', methods=['POST'])
@login_required
def update_datos():
    datos = cargar_datos()
    data = request.json
    for key in ['titulo', 'subtitulo', 'firma', 'categorias', 'moderacion_comentarios', 'redes_sociales', 'texto_pie', 'inicio']:
        if key in data:
            datos[key] = data[key]
    guardar_datos(datos)
    return jsonify({"success": True})

# CRUD Fotos
@app.route('/api/fotos', methods=['POST'])
@login_required
def add_foto():
    datos = cargar_datos()
    data = request.json
    nueva = {
        "id": datos["proximo_id"],
        "titulo": data.get('titulo', 'Sin título'),
        "categoria": data.get('categoria', datos['categorias'][0] if datos['categorias'] else 'General'),
        "archivo": data.get('archivo'),
        "orientacion": data.get('orientacion', 'horizontal')
    }
    datos["fotos"].append(nueva)
    datos["proximo_id"] += 1
    guardar_datos(datos)
    return jsonify({"success": True, "foto": nueva})

@app.route('/api/fotos/<int:foto_id>', methods=['PUT'])
@login_required
def update_foto(foto_id):
    datos = cargar_datos()
    data = request.json
    for foto in datos["fotos"]:
        if foto["id"] == foto_id:
            foto.update(data)
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

@app.route('/api/categorias/reasignar', methods=['POST'])
@login_required
def reasignar_categoria():
    """Elimina una categoría y mueve sus fotos a otra."""
    datos = cargar_datos()
    data = request.json or {}
    vieja = data.get("eliminar")
    nueva = data.get("nueva")
    if not vieja or not nueva or vieja == nueva:
        return jsonify({"error": "Parámetros inválidos"}), 400
    cats = datos.get("categorias", [])
    if len(cats) <= 1:
        return jsonify({"error": "Debe existir al menos una categoría"}), 400
    if vieja not in cats:
        return jsonify({"error": "Categoría inexistente"}), 400
    if nueva not in cats or nueva == vieja:
        return jsonify({"error": "Elige otra categoría válida para reasignar las fotos"}), 400
    datos["categorias"] = [c for c in cats if c != vieja]
    for f in datos.get("fotos", []):
        if f.get("categoria") == vieja:
            f["categoria"] = nueva
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

# CRUD Blog
@app.route('/api/blog', methods=['POST'])
@login_required
def add_blog():
    datos = cargar_datos()
    data = request.json
    bloques = data.get('bloques')
    if not bloques:
        bloques = [{"tipo": "texto", "texto": data.get('texto', '')}]
        if data.get('imagen'):
            bloques.append({"tipo": "imagen", "archivo": data['imagen'], "pie": ""})
    texto_plano = "\n\n".join(
        b.get("texto", "") for b in bloques if b.get("tipo") in ("texto", "titulo")
    )
    primera_img = next(
        (b.get("archivo") for b in bloques if b.get("tipo") == "imagen" and b.get("archivo")),
        ""
    )
    nuevo = {
        "id": datos["proximo_blog_id"],
        "titulo": data.get('titulo', 'Sin título'),
        "texto": texto_plano,
        "imagen": primera_img,
        "bloques": bloques,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    datos["blog"].append(nuevo)
    datos["proximo_blog_id"] += 1
    guardar_datos(datos)
    return jsonify({"success": True, "articulo": nuevo})

def _sincronizar_blog_legacy(art):
    bl = art.get("bloques") or []
    art["texto"] = "\n\n".join(
        b.get("texto", "") for b in bl if b.get("tipo") in ("texto", "titulo")
    )
    art["imagen"] = next(
        (b.get("archivo") for b in bl if b.get("tipo") == "imagen" and b.get("archivo")),
        ""
    )

@app.route('/api/blog/<int:id>', methods=['GET'])
def get_blog_articulo(id):
    datos = cargar_datos()
    art = next((a for a in datos.get("blog", []) if a["id"] == id), None)
    if not art:
        return jsonify({"error": "No encontrado"}), 404
    return jsonify(art)

@app.route('/api/blog/<int:id>', methods=['PUT'])
@login_required
def update_blog(id):
    datos = cargar_datos()
    data = request.json
    for art in datos["blog"]:
        if art["id"] == id:
            art.update(data)
            if "bloques" in data:
                _sincronizar_blog_legacy(art)
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

@app.route('/api/blog/reordenar', methods=['POST'])
@login_required
def reordenar_blog():
    datos = cargar_datos()
    ids = request.json.get('ids', [])
    blog_dict = {a["id"]: a for a in datos["blog"]}
    datos["blog"] = [blog_dict[i] for i in ids if i in blog_dict]
    guardar_datos(datos)
    return jsonify({"success": True})

# CRUD Series (completo)
@app.route('/api/series', methods=['POST'])
@login_required
def add_serie():
    datos = cargar_datos()
    data = request.json
    nueva = {
        "id": datos["proximo_serie_id"],
        "titulo": data.get('titulo', 'Serie sin título'),
        "descripcion": data.get('descripcion', ''),
        "fotos": data.get('fotos', []),
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    datos["series"].append(nueva)
    datos["proximo_serie_id"] += 1
    guardar_datos(datos)
    return jsonify({"success": True, "serie": nueva})

@app.route('/api/series/<int:id>', methods=['GET'])
def get_serie(id):
    datos = cargar_datos()
    serie = next((s for s in datos.get("series", []) if s["id"] == id), None)
    if not serie:
        return jsonify({"error": "Serie no encontrada"}), 404
    return jsonify(serie)

@app.route('/api/series/<int:id>', methods=['PUT'])
@login_required
def update_serie(id):
    datos = cargar_datos()
    data = request.json
    for serie in datos["series"]:
        if serie["id"] == id:
            serie.update(data)
            break
    guardar_datos(datos)
    return jsonify({"success": True})

@app.route('/api/series/<int:id>', methods=['DELETE'])
@login_required
def delete_serie(id):
    datos = cargar_datos()
    datos["series"] = [s for s in datos["series"] if s["id"] != id]
    guardar_datos(datos)
    return jsonify({"success": True})

@app.route('/api/series/reordenar', methods=['POST'])
@login_required
def reordenar_series():
    datos = cargar_datos()
    ids = request.json.get('ids', [])
    s_dict = {s["id"]: s for s in datos["series"]}
    datos["series"] = [s_dict[i] for i in ids if i in s_dict]
    guardar_datos(datos)
    return jsonify({"success": True})

@app.route('/api/series/<int:id>/fotos/reordenar', methods=['POST'])
@login_required
def reordenar_fotos_serie(id):
    datos = cargar_datos()
    orden = request.json.get('orden')
    if not isinstance(orden, list):
        return jsonify({"error": "orden inválido"}), 400
    for serie in datos["series"]:
        if serie["id"] == id:
            fotos = serie.get("fotos") or []
            if len(orden) != len(fotos) or set(orden) != set(range(len(fotos))):
                return jsonify({"error": "orden incompleto"}), 400
            serie["fotos"] = [fotos[i] for i in orden]
            break
    else:
        return jsonify({"error": "Serie no encontrada"}), 404
    guardar_datos(datos)
    return jsonify({"success": True})

# CRUD Páginas
@app.route('/api/paginas', methods=['POST'])
@login_required
def add_pagina():
    datos = cargar_datos()
    data = request.json
    slug = data.get('slug', data.get('titulo', '').lower().replace(' ', '-'))
    tipo = data.get('tipo', 'normal')
    if tipo == 'sobremi':
        contenido = []
    elif tipo == 'normal':
        contenido = ''
    else:
        contenido = data.get('contenido', '')
    nueva = {
        "id": datos["proximo_pagina_id"],
        "titulo": data.get('titulo', 'Nueva página'),
        "slug": slug,
        "tipo": tipo,
        "contenido": contenido,
        "parametros": data.get('parametros', {}),
        "visible": data.get('visible', True)
    }
    if tipo == 'normal':
        nueva["bloques"] = data.get('bloques', [{"tipo": "texto", "texto": ""}])
    elif tipo == 'sobremi':
        nueva["bloques"] = data.get('bloques', [{"tipo": "texto", "texto": ""}])
    elif tipo in ('lista_blog', 'lista_series'):
        nueva["contenido"] = ''
        nueva["parametros"] = data.get('parametros', {})
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
        "aprobado": not datos.get("moderacion_comentarios", False),
        "respuestas": []
    }
    datos["comentarios"].append(nuevo)
    datos["proximo_comentario_id"] += 1
    guardar_datos(datos)
    return jsonify({"success": True, "comentario": nuevo})

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
        "nickname": data.get('nickname', 'Zniper'),
        "texto": data.get('texto', ''),
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    for com in datos["comentarios"]:
        if com["id"] == id:
            com["respuestas"].append(respuesta)
            break
    guardar_datos(datos)
    return jsonify({"success": True})

# Subida de imágenes
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

# Credenciales
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
