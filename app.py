from flask import Flask, render_template, request, redirect, url_for, flash, session
from config import APIKEY
from funciones import HoneyPuffDB
from flask_mail import Mail, Message
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.secret_key = APIKEY


from config import (
    CORREO,
    PASSWORD_CORREO
)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = CORREO
app.config['MAIL_PASSWORD'] = PASSWORD_CORREO
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

mail = Mail(app)
db = HoneyPuffDB()


@app.route("/")
def login():
    return render_template("login.html")


@app.route('/ValidaSesion', methods=['GET', 'POST'])
def ValidaSesion():

    if request.method == "POST":

        email = request.form.get('Email', '').strip()
        contra = request.form.get('Contra', '').strip()

        if not email or not contra:

            flash('Por favor ingresa correo y contraseña', 'error')

            return redirect(url_for('login'))

        usuario = db.validar_usuario(email, contra)

        if not usuario:

            flash('Correo o contraseña incorrectos', 'error')

            return redirect(url_for('login'))

        session['usuario_email'] = email
        session['usuario'] = usuario['nombre']
        session['usuario_id'] = usuario['_id']
        session['loggeado'] = True

        flash(f"Bienvenido {usuario['nombre']}!", 'success')

        return redirect(url_for('elejir'))

    return redirect(url_for('login'))


@app.route("/registro", methods=["GET", "POST"])
def registro():

    if request.method == "POST":

        nombre = request.form.get("Nombre")
        apellido = request.form.get("Apellido")
        email = request.form.get("Email")
        contra = request.form.get("Contra")

        usuario_creado = db.crear_usuario(
            nombre,
            apellido,
            email,
            contra
        )

        if usuario_creado:

            flash("Cuenta creada correctamente")

            return redirect(url_for("login"))

        flash("Ese correo ya existe")

        return redirect(url_for("registro"))

    return render_template("registro.html")


@app.route("/recuperar", methods=["GET", "POST"])
def recuperar():

    if request.method == "POST":

        email = request.form.get("Email")

        usuario = db.usuarios.find_one({"email": email})

        if not usuario:

            flash("Correo no encontrado", "error")

            return redirect(url_for("recuperar"))

        codigo = random.randint(100000, 999999)

        db.guardar_codigo_recuperacion(email, codigo)

        msg = Message(
            'Recuperación HoneyPuff',
            sender=app.config['MAIL_USERNAME'],
            recipients=[email]
        )

        msg.body = f'''
Tu código de recuperación es:

{codigo}

El código expirará en 5 minutos.
'''

        mail.send(msg)

        flash("Código enviado al correo", "success")

        return redirect(url_for("verificar_codigo"))

    return render_template("recuperar.html")


@app.route("/verificar_codigo", methods=["GET", "POST"])
def verificar_codigo():

    if request.method == "POST":

        email = request.form.get("Email")
        codigo = request.form.get("Codigo")

        usuario = db.usuarios.find_one({
            "email": email
        })

        if not usuario:
            flash("Correo no encontrado", "error")
            return redirect(url_for("verificar_codigo"))

        if "codigo_recuperacion" not in usuario:
            flash("No hay código registrado", "error")
            return redirect(url_for("verificar_codigo"))

        if usuario["codigo_recuperacion"] != codigo:
            flash("Código incorrecto", "error")
            return redirect(url_for("verificar_codigo"))

        if datetime.now() > usuario["expira_codigo"]:
            flash("El código expiró", "error")
            return redirect(url_for("recuperar"))

        session["recuperacion_email"] = email
        flash("Código verificado correctamente", "success")

        return redirect(url_for("cambiar_password"))

    return render_template("verificar_codigo.html")


@app.route("/cambiar_password", methods=["GET", "POST"])
def cambiar_password():

    if "recuperacion_email" not in session:
        return redirect(url_for("recuperar"))

    if request.method == "POST":

        nueva_password = request.form.get("NuevaPassword")
        confirmar_password = request.form.get("ConfirmarPassword")

        if nueva_password != confirmar_password:
            flash("Las contraseñas no coinciden", "error")
            return redirect(url_for("cambiar_password"))

        password_encriptado = db.encriptar_password(
            nueva_password
        )

        db.usuarios.update_one(
            {
                "email": session["recuperacion_email"]
            },
            {
                "$set": {
                    "password": password_encriptado
                },
                "$unset": {
                    "codigo_recuperacion": "",
                    "expira_codigo": ""
                }
            }
        )

        session.pop("recuperacion_email")

        flash("Contraseña actualizada correctamente", "success")

        return redirect(url_for("login"))

    return render_template("cambiar_password.html")


@app.route("/inicio")
def inicio():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "inicio.html",
        usuario=session["usuario"]
    )


@app.route("/elejir")
def elejir():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    return render_template("elejir.html")

@app.route("/elejir_oso")
def elejir_oso():
    if "usuario_id" not in session:
        return redirect(url_for("login"))
    return render_template("elejir_oso.html")

@app.route("/elejir_gato")
def elejir_gato():
    if "usuario_id" not in session:
        return redirect(url_for("login"))
    return render_template("elejir_gato.html")

@app.route("/elejir_abeja")
def elejir_abeja():
    if "usuario_id" not in session:
        return redirect(url_for("login"))
    return render_template("elejir_abeja.html")



@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)