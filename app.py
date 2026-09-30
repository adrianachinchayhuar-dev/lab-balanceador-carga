import os

from flask import Flask, flash, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = "clave_lab_secret"
PORT = os.environ.get("PORT", "8080")
USUARIOS = {"admin": "1234"}
TAREAS = []


def usuario_autenticado():
    return "user" in session


def backend_label():
    return f"APP {PORT[-1]} · Puerto {PORT}" if PORT[-1].isdigit() else f"Puerto {PORT}"


@app.context_processor
def inject_backend_info():
    return {"port": PORT, "backend_label": backend_label()}


@app.route("/")
def index():
    if usuario_autenticado():
        return render_template("dashboard.html", tareas=TAREAS)
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
        TAREAS.append(tarea)
        flash(f"✓ Tarea creada correctamente: {tarea}", "success")
    return redirect(url_for("index"))


@app.route("/crud/update/<int:item_id>", methods=["POST"])
def update(item_id):
    if not usuario_autenticado():
        return redirect(url_for("login"))
    if not 0 <= item_id < len(TAREAS):
        flash("La tarea que intentas editar no existe.", "warning")
        return redirect(url_for("index"))
    tarea = request.form.get("tarea", "").strip()
    if not tarea:
        flash("La tarea no puede estar vacía.", "warning")
    else:
        TAREAS[item_id] = tarea
        flash("✓ Tarea actualizada correctamente.", "success")
    return redirect(url_for("index"))


@app.route("/crud/edit/<int:item_id>")
def edit(item_id):
    if not usuario_autenticado():
        return redirect(url_for("login"))
    if not 0 <= item_id < len(TAREAS):
        flash("La tarea que intentas editar no existe.", "warning")
        return redirect(url_for("index"))
    return render_template("edit.html", item_id=item_id, tarea=TAREAS[item_id])


@app.route("/crud/delete/<int:item_id>", methods=["GET", "POST"])
def delete(item_id):
    if not usuario_autenticado():
        return redirect(url_for("login"))
    if not 0 <= item_id < len(TAREAS):
        flash("La tarea que intentas eliminar no existe.", "warning")
    else:
        TAREAS.pop(item_id)
        flash("✓ Tarea eliminada correctamente.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
