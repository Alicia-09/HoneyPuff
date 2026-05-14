from flask import Flask, render_template, request, redirect, url_for, flash, session
from funciones import HoneyPuffDB

app = Flask(__name__)
app.secret_key = "ibdr091903."

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

        password = db.recuperar_password(email)

        if password:

            flash(f"Tu contraseña es: {password}")

            return redirect(url_for("login"))

        flash("Correo no encontrado")

    return render_template("recuperar.html")


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