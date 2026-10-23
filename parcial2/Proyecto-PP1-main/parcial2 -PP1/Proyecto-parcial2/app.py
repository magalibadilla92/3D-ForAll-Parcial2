
import os
import secrets
from pathlib import Path
from datetime import datetime

from flask import Flask, request, send_from_directory, render_template
from markupsafe import escape
from werkzeug.utils import secure_filename
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from peewee import (
    SqliteDatabase,
    Model,
    AutoField,
    CharField,
    TextField,
    DateTimeField
)

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__, template_folder=str(BASE_DIR))

# Clave de sesión: en producción configurarla como variable de entorno.
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)

# CSRF: protege los formularios POST
csrf = CSRFProtect(app)

# Limita la frecuencia de solicitudes
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

# Tamaño máximo total: 40 MB
app.config["MAX_CONTENT_LENGTH"] = 40 * 1024 * 1024

CARPETA_CARGAS = BASE_DIR / "uploads"
CARPETA_CARGAS.mkdir(exist_ok=True)

CAMPOS_IMAGENES = [
    "vistaFrontal",
    "vistaTrasera",
    "vistaSuperior",
    "vistaInferior"
]

EXTENSIONES_PERMITIDAS = {"jpg", "jpeg", "png"}

# Base de datos SQLite con Peewee
db = SqliteDatabase(BASE_DIR / "modelos.db")


class BaseModel(Model):
    class Meta:
        database = db


class Modelo(BaseModel):
    id = AutoField()
    nombre = CharField(max_length=100)
    categoria = CharField(max_length=80)
    descripcion = TextField()
    vista_frontal = CharField(max_length=255)
    vista_trasera = CharField(max_length=255)
    vista_superior = CharField(max_length=255)
    vista_inferior = CharField(max_length=255)
    fecha_creacion = DateTimeField(default=datetime.now)


db.connect(reuse_if_open=True)
db.create_tables([Modelo])


# Cabeceras de seguridad para todas las respuestas
@app.after_request
def agregar_cabeceras_seguridad(respuesta):
    respuesta.headers["X-Frame-Options"] = "DENY"

    # CSP: restringe de dónde pueden cargarse recursos.
    # 'unsafe-inline' se mantiene porque las páginas actuales
    # usan estilos y scripts incorporados en el HTML.
    respuesta.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "img-src 'self' data:; "
        "font-src 'self' https://cdn.jsdelivr.net; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "frame-ancestors 'none'"
    )

    return respuesta


@app.route("/")
def inicio():
    # Renderiza index.html como plantilla para generar el token CSRF
    return render_template("index.html")


@app.route("/subir-modelo", methods=["POST"])
@limiter.limit("5 per minute")
def subir_modelo():
    nombre = request.form.get("nombreModelo", "").strip()
    categoria = request.form.get("categoriaModelo", "").strip()
    descripcion = request.form.get("descripcionModelo", "").strip()

    if not nombre or not categoria or not descripcion:
        return "Error: completá el nombre, la categoría y la descripción.", 400

    nombres_guardados = {}

    for campo in CAMPOS_IMAGENES:
        archivo = request.files.get(campo)

        if not archivo or archivo.filename == "":
            return f"Error: falta la imagen {campo}.", 400

        if "." not in archivo.filename:
            return "Error: las imágenes deben ser JPG o PNG.", 400

        extension = archivo.filename.rsplit(".", 1)[-1].lower()

        if extension not in EXTENSIONES_PERMITIDAS:
            return "Error: las imágenes deben ser JPG o PNG.", 400

        archivo.seek(0, 2)
        tamano = archivo.tell()
        archivo.seek(0)

        if tamano > 10 * 1024 * 1024:
            return "Error: cada imagen debe pesar como máximo 10 MB.", 400

        nombre_seguro = secure_filename(archivo.filename)
        nombre_final = f"{campo}_{nombre_seguro}"

        archivo.save(CARPETA_CARGAS / nombre_final)
        nombres_guardados[campo] = nombre_final

    Modelo.create(
        nombre=nombre,
        categoria=categoria,
        descripcion=descripcion,
        vista_frontal=nombres_guardados["vistaFrontal"],
        vista_trasera=nombres_guardados["vistaTrasera"],
        vista_superior=nombres_guardados["vistaSuperior"],
        vista_inferior=nombres_guardados["vistaInferior"]
    )

    return """
    <h1>¡Modelo registrado!</h1>
    <p>Las imágenes se guardaron y los datos se registraron en la base de datos.</p>
    <p>Este prototipo todavía no genera el modelo 3D.</p>
    <a href="/">Volver al sitio</a>
    """


@app.route("/modelos")
def listar_modelos():
    modelos = Modelo.select()

    lista_html = "<h1>Modelos registrados</h1><ul>"

    for modelo in modelos:
        # Escapar texto ingresado por el usuario para evitar inyectar HTML
        nombre_seguro = escape(modelo.nombre)
        categoria_segura = escape(modelo.categoria)

        lista_html += f"<li>{nombre_seguro} — {categoria_segura}</li>"

    lista_html += "</ul><a href='/'>Volver al sitio</a>"

    return lista_html


@app.route("/<path:pagina>")
def mostrar_pagina(pagina):
    # Las páginas HTML se renderizan como plantillas (incluye el token CSRF)
    if pagina.endswith(".html"):
        return render_template(pagina)

    # Archivos como app.js se sirven normalmente
    return send_from_directory(BASE_DIR, pagina)


if __name__ == "__main__":
    app.run(debug=True)
