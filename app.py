from flask import Flask, render_template,request,flash,url_for,redirect,session
import requests 

from GestorTareas import GestorTareas
app = Flask(__name__)
app.secret_key = "ibdr091903."

@app.route("/")
def home():
    return render_template("login.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/inicio")
def inicio():
    
    gestor = GestorTareas()

    tareas = gestor.obtener_tareas_usuario(session["usuario_id"])

    return render_template("inicio.html",tareas=tareas)

@app.route("/logout")
def logout():
    return render_template("login.html")

    
@app.route('/ValidaSesion', methods=['GET', 'POST'])
def ValidaSesion():
    if request.method == "POST":
        email = request.form.get('Email', '').strip()
        contra = request.form.get('Contra', '').strip()

        if not email or not contra:
            flash('Por favor ingresa email y contraseña', 'error')
            return redirect(url_for('login'))

        gestor = GestorTareas()
        usuario = gestor.obtener_usuario2(email, contra)

        if not usuario:
            flash('Usuario o contraseña incorrectos', 'error')
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
        contraConfirm = request.form.get("ContraConfirm") 

        if contra != contraConfirm:
            flash("La contraseña no coincide", "error")
            return render_template("registro.html")
        
        gestor = GestorTareas()
        resultado = gestor.crear_usuario(nombre, email, contra)
        
        if not resultado:
            flash("Ya existe una cuenta con ese correo", "error")
            return render_template("registro.html")

        flash(f"Cuenta creada correctamente para el usuario:{nombre} {apellido}", "success")
        return redirect(url_for("login"))

    return render_template("registro.html")

@app.route("/crear_tarea", methods=["POST"])
def crear_tarea():

    titulo = request.form.get("titulo")
    descripcion = request.form.get("descripcion")
    fecha_limite = request.form.get("fecha_limite")
    prioridad = request.form.get("prioridad")
    
    if not titulo or not prioridad:
            flash('Por favor ingresa una tarea ', 'error')
            return redirect(url_for('inicio'))
        
    gestor = GestorTareas()

    gestor.crear_tarea(
        session["usuario_id"],
        titulo,
        descripcion,
        fecha_limite,
        prioridad
    )

    return redirect(url_for("inicio"))

@app.route("/completar/<id>")
def completar(id):

    gestor = GestorTareas()

    gestor.actualizar_estado_tarea(
        id,
        "completada"
    )

    return redirect(url_for("inicio"))

@app.route("/eliminar_tarea/<id>")
def eliminar_tarea(id):

    gestor = GestorTareas()

    gestor.eliminar_tarea(id)

    return redirect(url_for("inicio"))

if __name__ == "__main__":
    app.run(debug=True)