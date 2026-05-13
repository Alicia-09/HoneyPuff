from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
import bcrypt

app = Flask(_name_)
app.secret_key = "ibdr091903."



MONGO_URI = "mongodb+srv://mely2:mely19@mely1.lnfi7bk.mongodb.net/?appName=mely1"

client = MongoClient(MONGO_URI)

db = client["HoneyPuff"]

usuarios = db["usuarios"]
mascotas = db["mascotas"]



@app.route("/")
def login():
    return render_template("login.html")


@app.route("/ValidaSesion", methods=["POST"])
def ValidaSesion():

    email = request.form.get("Email")
    contra = request.form.get("Contra")

    usuario = usuarios.find_one({
        "email": email
    })

    if not usuario:
        flash("Usuario no encontrado")
        return redirect(url_for("login"))

    if bcrypt.checkpw(
        contra.encode("utf-8"),
        usuario["password"]
    ):

        session["usuario_id"] = str(usuario["_id"])
        session["usuario"] = usuario["nombreUsuario"]

        flash("Bienvenido")
        return redirect(url_for("inicio"))

    flash("Contraseña incorrecta")

    return redirect(url_for("login"))


@app.route("/registro", methods=["GET", "POST"])
def registro():

    if request.method == "POST":

        nombreUsuario = request.form.get("Nombre")
        email = request.form.get("Email")
        contra = request.form.get("Contra")

        existe = usuarios.find_one({
            "email": email
        })

        if existe:
            flash("Ese correo ya existe")
            return redirect(url_for("registro"))

        password_hash = bcrypt.hashpw(
            contra.encode("utf-8"),
            bcrypt.gensalt()
        )

        usuarios.insert_one({
            "nombreUsuario": nombreUsuario,
            "email": email,
            "password": password_hash
        })

        flash("Cuenta creada correctamente")

        return redirect(url_for("login"))

    return render_template("registro.html")



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


if _name_ == "_main_":
    app.run(debug=True)