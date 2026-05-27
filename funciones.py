from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, ConnectionFailure
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from typing import Optional, Dict
from cryptography.fernet import Fernet

clave = b'w4D1DFuM0HB_AQvNKVUGyqYOBfmD-ViDaod-b2C4y7g='
f = Fernet(clave)

from config import (
    MONGO_ATLAS_URI
)

class HoneyPuffDB:

    def __init__(self):
        try:
            self.cliente = MongoClient(MONGO_ATLAS_URI, serverSelectionTimeoutMS=5000)
            self.cliente.admin.command("ping")

            self.db = self.cliente["HoneyPuff"]
            self.usuarios = self.db["usuarios"]
            self.mascotas = self.db["mascotas"]

            self._crear_indices()

            print("✅ Conectado a Mongo Atlas")

        except ConnectionFailure:
            print("❌ Error conexión MongoDB")
            raise

    def _crear_indices(self):
        self.usuarios.create_index("email", unique=True)

    def encriptar_password(self, password):
        password_bytes = password.encode()
        password_encriptado = f.encrypt(password_bytes)

        return password_encriptado.decode()

    def desencriptar_password(self, password_encriptado):
        password_bytes = password_encriptado.encode()
        password_desencriptado = f.decrypt(password_bytes)

        return password_desencriptado.decode()

    def crear_usuario(self, nombre: str, apellido: str, email: str, password: str) -> Optional[str]:
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

    def validar_usuario(self,email: str,password: str) -> Optional[Dict]:
        try:
            usuario = self.usuarios.find_one({"email": email})

            if not usuario:
                return None
            
            password_guardada = self.desencriptar_password(usuario["password"])

            if password_guardada == password:
                usuario["_id"] = str(usuario["_id"])
                return usuario
            
            return None
        
        except Exception as e:
            print(f"❌ Error login: {e}")
            return None

    def obtener_usuario(self, usuario_id):
        usuario = self.usuarios.find_one({"_id": ObjectId(usuario_id)})

        if usuario:
            usuario["_id"] = str(usuario["_id"])
        return usuario

    def recuperar_password(self, email):

        usuario = self.usuarios.find_one({"email": email})

        if not usuario:return None
        
        password = self.desencriptar_password(usuario["password"])

        return password

    def guardar_codigo_recuperacion(self, email, codigo):

        expira = datetime.now() + timedelta(minutes=5)

        self.usuarios.update_one(
            {"email": email},
            {
                "$set": {
                    "codigo_recuperacion": str(codigo),
                    "expira_codigo": expira
                }
            }
        )
        
    def registrar_mascota(self, nombre: str, fecha_nacimiento: str, lugar_nacimiento: str, usuario_id: str = None):

        mascotas = {
           "nombre": nombre,
           "fecha_nacimiento": fecha_nacimiento,
           "lugar_nacimiento": lugar_nacimiento,
           "fecha_registro": datetime.now()
        }

        if usuario_id:

            if ObjectId.is_valid(usuario_id):
                mascotas["usuario_id"] = ObjectId(usuario_id)

            else:
                mascotas["usuario_id"] = usuario_id

        resultado = self.mascotas.insert_one(mascotas)

        return str(resultado.inserted_id)

    def obtener_mascotas(self):

        lista_mascotas = []

        for mascota in self.mascotas.find():

            mascota["_id"] = str(mascota["_id"])

            if "usuario_id" in mascota:
                mascota["usuario_id"] = str(mascota["usuario_id"])

            lista_mascotas.append(mascota)

        return lista_mascotas

    def cerrar_conexion(self):
        if self.cliente:
            self.cliente.close()
            print("🔌 Conexión cerrada")