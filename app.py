import os
import time

import mysql.connector
from flask import Flask, flash, redirect, render_template, request, session, url_for
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = "clave_lab_secret"
PORT = os.environ.get("PORT", "8080")
USUARIOS = {"admin": "1234"}

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "mysql"),
    "port": int(os.environ.get("DB_PORT", "3306")),
    "database": os.environ.get("DB_NAME", "lab_balanceador"),
    "user": os.environ.get("DB_USER", "lab_user"),
    "password": os.environ.get("DB_PASSWORD"),
}
DATABASE_READY = False


def usuario_autenticado():
    return "user" in session


def backend_label():
    return f"APP {PORT[-1]} · Puerto {PORT}" if PORT[-1].isdigit() else f"Puerto {PORT}"


def get_db_connection():
    """Connect to the Compose MySQL service, retrying while it initializes."""
    last_error = None
    for attempt in range(30):
        try:
            return mysql.connector.connect(**DB_CONFIG)
        except Error as error:
            last_error = error
            if attempt < 29:
                time.sleep(2)
    raise last_error


def initialize_database():
    global DATABASE_READY
    if DATABASE_READY:
        return

    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tareas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                descripcion VARCHAR(255) NOT NULL,
                estado VARCHAR(30) NOT NULL DEFAULT 'pendiente',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
            """
        )
        connection.commit()
        DATABASE_READY = True
    finally:
        cursor.close()
        connection.close()


def listar_tareas():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, descripcion, estado, created_at "
            "FROM tareas ORDER BY id DESC"
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def obtener_tarea(item_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, descripcion, estado, created_at FROM tareas WHERE id = %s",
            (item_id,),
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        connection.close()


def ejecutar_cambio(query, params):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(query, params)
        connection.commit()
        return cursor.rowcount
    except Error:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


@app.before_request
def ensure_database():
    initialize_database()


@app.context_processor
def inject_backend_info():
    return {"port": PORT, "backend_label": backend_label()}


@app.route("/")
def index():
    if usuario_autenticado():
        return render_template("dashboard.html", tareas=listar_tareas())
    return render_template("login.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username in USUARIOS and USUARIOS[username] == password:
            session["user"] = username
            return redirect(url_for("index"))
        flash("Usuario o contraseña incorrectos.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Sesión cerrada correctamente.", "success")
    return redirect(url_for("login"))


@app.route("/crud/create", methods=["POST"])
def create():
    if not usuario_autenticado():
        return redirect(url_for("login"))
    tarea = request.form.get("tarea", "").strip()
    if not tarea:
        flash("Escribe una tarea antes de agregarla.", "warning")
    else:
        ejecutar_cambio("INSERT INTO tareas (descripcion) VALUES (%s)", (tarea,))
        flash(f"✓ Tarea creada correctamente: {tarea}", "success")
    return redirect(url_for("index"))


@app.route("/crud/update/<int:item_id>", methods=["POST"])
def update(item_id):
    if not usuario_autenticado():
        return redirect(url_for("login"))
    tarea = request.form.get("tarea", "").strip()
    if not tarea:
        flash("La tarea no puede estar vacía.", "warning")
    elif obtener_tarea(item_id) is None:
        flash("La tarea que intentas editar no existe.", "warning")
    else:
        ejecutar_cambio(
            "UPDATE tareas SET descripcion = %s WHERE id = %s", (tarea, item_id)
        )
        flash("✓ Tarea actualizada correctamente.", "success")
    return redirect(url_for("index"))


@app.route("/crud/edit/<int:item_id>")
def edit(item_id):
    if not usuario_autenticado():
        return redirect(url_for("login"))
    tarea = obtener_tarea(item_id)
    if tarea is None:
        flash("La tarea que intentas editar no existe.", "warning")
        return redirect(url_for("index"))
    return render_template("edit.html", item_id=item_id, tarea=tarea["descripcion"])


@app.route("/crud/delete/<int:item_id>", methods=["GET", "POST"])
def delete(item_id):
    if not usuario_autenticado():
        return redirect(url_for("login"))
    if ejecutar_cambio("DELETE FROM tareas WHERE id = %s", (item_id,)) == 0:
        flash("La tarea que intentas eliminar no existe.", "warning")
    else:
        flash("✓ Tarea eliminada correctamente.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    initialize_database()
    app.run(host="0.0.0.0", port=5000)
