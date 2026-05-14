from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, ConnectionFailure
from bson.objectid import ObjectId
from datetime import datetime
from typing import Optional, Dict
from cryptography.fernet import Fernet

clave = b'w4D1DFuM0HB_AQvNKVUGyqYOBfmD-ViDaod-b2C4y7g='

f = Fernet(clave)

class HoneyPuffDB:

    def __init__(self):
        try:
            uri = "mongodb+srv://mely2:mely19@mely1.lnfi7bk.mongodb.net/?appName=mely1"
            self.cliente = MongoClient(uri,serverSelectionTimeoutMS=5000)

            self.cliente.admin.command('ping')
            self.db = self.cliente['HoneyPuff']
            self.usuarios = self.db['usuarios']
            self._crear_indices()
            print("✅ Conectado a Mongo Atlas")

        except ConnectionFailure:
            print("❌ Error conexión MongoDB")
            raise

    def _crear_indices(self):
        self.usuarios.create_index("email",unique=True)

    def encriptar_password(self, password):
        password_bytes = password.encode()
        password_encriptado = f.encrypt(password_bytes)
        return password_encriptado.decode()

    def desencriptar_password(self, password_encriptado):
        password_bytes = password_encriptado.encode()
        password_desencriptado = f.decrypt(password_bytes)
        return password_desencriptado.decode()
    

    def crear_usuario(self, nombre: str,apellido: str,email: str,password: str) -> Optional[str]:
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

    def cerrar_conexion(self):
        if self.cliente:
            self.cliente.close()
            print("🔌 Conexión cerrada")