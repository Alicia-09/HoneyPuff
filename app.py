from flask import Flask, render_template, request, redirect, url_for, flash, session
from config import APIKEY
from funciones import HoneyPuffDB
import random
#practicamente ya esta listo solo falta que en config.py pongas la contraseña de aplicacion de tu correo y el correo desde el que se enviaran los correos de recuperacion, ademas de la clave secreta para las sesiones, puedes generar una clave secreta con cualquier generador de claves en linea, por ejemplo https://randomkeygen.com/ y ponerla en APIKEY, tambien debes instalar las dependencias con pip install -r requirements.txt y luego ejecutar este archivo con python app.py
#y que te fijes si las funciones estan bn nombradas y asi y pues si quieres cambiar eel diseño

app = Flask(__name__)
app.secret_key = APIKEY

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
        session['usuario_id'] = str(usuario['_id'])
        session['loggeado'] = True

        flash(f"Bienvenido {usuario['nombre']}!", 'success')

        return redirect(url_for('inicio'))

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
        usuario = db.buscar_usuario(email)

        if not usuario:
            flash("Correo no encontrado")
            return redirect(url_for("recuperar"))

        codigo = str(random.randint(100000, 999999))

        db.guardar_codigo_recuperacion(
            email,
            codigo
        )

        db.enviar_codigo_email(
            email,
            codigo
        )

        flash("Código enviado al correo")

        return redirect(url_for("resetear"))

    return render_template("recuperar.html")


@app.route("/resetear", methods=["GET", "POST"])
def resetear():

    if request.method == "POST":

        email = request.form.get("Email")
        codigo = request.form.get("Codigo")
        nueva = request.form.get("Nueva")
        confirmar = request.form.get("Confirmar")

        if nueva != confirmar:

            flash("Las contraseñas no coinciden")

            return redirect(url_for("resetear"))

        valido = db.validar_codigo(
            email,
            codigo
        )

        if not valido:
            flash("Código inválido")
            return redirect(url_for("resetear"))

        db.actualizar_password(
            email,
            nueva
        )

        db.eliminar_codigo(email)
        flash("Contraseña actualizada")

        return redirect(url_for("login"))

    return render_template("resetear.html")


@app.route("/inicio")
def inicio():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "inicio.html",
        usuario=session["usuario"]
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)