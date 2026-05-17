from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, ConnectionFailure
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from typing import Optional, Dict
from cryptography.fernet import Fernet

from config import (
    CLAVESITA,
    MONGO_ATLAS_URI,
    CORREO,
    PASSWORD_CORREO
)

import smtplib

from email.mime.text import MIMEText

clave = CLAVESITA

f = Fernet(clave)


class HoneyPuffDB:

    def __init__(self):

        try:

            uri = MONGO_ATLAS_URI

            self.cliente = MongoClient(
                uri,
                serverSelectionTimeoutMS=5000
            )

            self.cliente.admin.command('ping')

            self.db = self.cliente['HoneyPuff']

            self.usuarios = self.db['usuarios']

            self._crear_indices()

            print("✅ Conectado a Mongo Atlas")

        except ConnectionFailure:

            print("❌ Error conexión MongoDB")

            raise

    def _crear_indices(self):

        self.usuarios.create_index(
            "email",
            unique=True
        )

    def encriptar_password(self, password):

        password_bytes = password.encode()

        password_encriptado = f.encrypt(password_bytes)

        return password_encriptado.decode()

    def desencriptar_password(self, password_encriptado):

        password_bytes = password_encriptado.encode()

        password_desencriptado = f.decrypt(password_bytes)

        return password_desencriptado.decode()

    def crear_usuario(
        self,
        nombre: str,
        apellido: str,
        email: str,
        password: str
    ) -> Optional[str]:

        try:

            password_encriptado = self.encriptar_password(password)

            resultado = self.usuarios.insert_one({

                "nombre": nombre,

                "apellido": apellido,

                "email": email,

                "password": password_encriptado,

                "fecha_registro": datetime.now()

            })

            return str(resultado.inserted_id)

        except DuplicateKeyError:

            print("❌ Ese correo ya existe")

            return None

    def validar_usuario(
        self,
        email: str,
        password: str
    ) -> Optional[Dict]:

        try:

            usuario = self.usuarios.find_one({
                "email": email
            })

            if not usuario:
                return None

            password_guardada = self.desencriptar_password(
                usuario["password"]
            )

            if password_guardada == password:

                usuario["_id"] = str(usuario["_id"])

                return usuario

            return None

        except Exception as e:

            print(f"❌ Error login: {e}")

            return None

    def obtener_usuario(self, usuario_id):

        usuario = self.usuarios.find_one({
            "_id": ObjectId(usuario_id)
        })

        if usuario:

            usuario["_id"] = str(usuario["_id"])

        return usuario

    def buscar_usuario(self, email):

        return self.usuarios.find_one({
            "email": email
        })

    def guardar_codigo_recuperacion(
        self,
        email,
        codigo
    ):

        expiracion = datetime.now() + timedelta(minutes=5)

        self.usuarios.update_one(

            {
                "email": email
            },

            {
                "$set": {

                    "codigo_recuperacion": codigo,

                    "expiracion_codigo": expiracion

                }
            }
        )

    def validar_codigo(
        self,
        email,
        codigo
    ):

        usuario = self.usuarios.find_one({

            "email": email,

            "codigo_recuperacion": codigo

        })

        if not usuario:
            return False

        if datetime.now() > usuario["expiracion_codigo"]:
            return False

        return True

    def actualizar_password(
        self,
        email,
        nueva_password
    ):

        nueva_password_encriptada = self.encriptar_password(
            nueva_password
        )

        self.usuarios.update_one(

            {
                "email": email
            },

            {
                "$set": {
                    "password": nueva_password_encriptada
                }
            }
        )

    def eliminar_codigo(self, email):

        self.usuarios.update_one(

            {
                "email": email
            },

            {
                "$unset": {

                    "codigo_recuperacion": "",

                    "expiracion_codigo": ""

                }
            }
        )

    def enviar_codigo_email(
        self,
        destinatario,
        codigo
    ):

        mensaje = MIMEText(
            f"Tu código de recuperación es: {codigo}"
        )

        mensaje["Subject"] = "Recuperación de contraseña"

        mensaje["From"] = CORREO

        mensaje["To"] = destinatario

        servidor = smtplib.SMTP(
            "smtp.gmail.com",
            587
        )

        servidor.starttls()

        servidor.login(
            CORREO,
            PASSWORD_CORREO
        )

        servidor.send_message(mensaje)

        servidor.quit()

    def cerrar_conexion(self):

        if self.cliente:

            self.cliente.close()

            print("🔌 Conexión cerrada")