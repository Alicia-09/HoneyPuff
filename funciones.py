from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, ConnectionFailure
from bson.objectid import ObjectId
from datetime import datetime
from typing import Optional, Dict
from cryptography.fernet import Fernet



clave = b'w4D1DFuM0HB_AQvNKVUGyqYOBfmD-ViDaod-b2C4y7g='

f = Fernet(clave)



class GestorTareas:

    def _init_(self):

        try:


            uri = "mongodb+srv://mely2:mely19@mely1.lnfi7bk.mongodb.net/?appName=mely1"

            self.cliente = MongoClient(
                uri,
                serverSelectionTimeoutMS=5000
            )

            self.cliente.admin.command('ping')

            self.db = self.cliente['HoneyPuff']

            self.usuarios = self.db['usuarios']

            self.usuarios.create_index(
                "email",
                unique=True
            )

            print("✅ Conectado a Mongo Atlas")

        except ConnectionFailure:

            print("❌ Error conexión MongoDB")

            raise


    def encriptar_password(self, password):

        password_bytes = password.encode()

        password_encriptado = f.encrypt(
            password_bytes
        )

        return password_encriptado.decode()

  

    def desencriptar_password(self, password_encriptado):

        password_bytes = password_encriptado.encode()

        password_desencriptado = f.decrypt(
            password_bytes
        )

        return password_desencriptado.decode()

  

    def crear_usuario(
        self,
        nombre,
        email,
        password
    ) -> Optional[str]:

        try:

            password_encriptado = self.encriptar_password(
                password
            )

            resultado = self.usuarios.insert_one({

                "nombreUsuario": nombre,

                "email": email,

                "password": password_encriptado,

                "fecha_registro": datetime.now()

            })

            return str(resultado.inserted_id)

        except DuplicateKeyError:

            print("❌ Ese correo ya existe")

            return None



    def obtener_usuario2(
        self,
        email,
        pass1
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

         
            if password_guardada == pass1:

                usuario["_id"] = str(usuario["_id"])

                return usuario

            return None

        except Exception as e:

            print(f"Error login: {e}")

            return None



    def obtener_usuario(self, usuario_id):

        usuario = self.usuarios.find_one({

            "_id": ObjectId(usuario_id)

        })

        if usuario:

            usuario["_id"] = str(usuario["_id"])

        return usuario



    def cerrar_conexion(self):

        if self.cliente:

            self.cliente.close()

            print("🔌 Conexión cerrada")  