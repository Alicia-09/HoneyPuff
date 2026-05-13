from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, ConnectionFailure
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import os
from cryptography.fernet import Fernet 

clave = b'w4D1DFuM0HB_AQvNKVUGyqYOBfmD-ViDaod-b2C4y7g='
f = Fernet(clave)

class GestorTareas:
    def __init__(self, uri: str = 'mongodb://localhost:27017/'):
        """Inicializar conexión a MongoDB"""
        try:
            self.cliente = MongoClient(uri, serverSelectionTimeoutMS=5000)
            self.cliente.admin.command('ping')
            self.db = self.cliente['gestor_tareas']
            self.tareas = self.db['tareas']
            self.usuarios = self.db['usuarios']
            
            # Crear índices necesarios
            self._crear_indices()
            print("✅ Conectado a MongoDB")
        except ConnectionFailure:
            print("❌ Error: No se pudo conectar a MongoDB")
            raise
    
    def _crear_indices(self):
        """Crear índices para mejorar rendimiento"""
        self.usuarios.create_index("email", unique=True)
        self.tareas.create_index([("usuario_id", 1), ("fecha_creacion", -1)])
        self.tareas.create_index("estado")
    
    def encriptar_password(self, password):
        password_bytes = password.encode()
        """Convierte texto a bytes"""
        password_encriptado = f.encrypt(password_bytes)
        """Encripta la contraseña"""
        return password_encriptado.decode()
    """la vuelve a convertir en texto y se guarda en mongo"""
    
    def desencriptar_password(self, password_encriptado):
        """Recibe la contra encriptada de la bd"""
        password_bytes = password_encriptado.encode()
        """la convierte en bytes"""
        password_desencriptado = f.decrypt(password_bytes)
        """la desencripta"""
        return password_desencriptado.decode()
    """la regresa como texto normal"""

    def crear_usuario(self, nombre: str, email: str, password: str) -> Optional[str]:
        """Crear un nuevo usuario"""
        """agregue contra"""
        try:
            password_encriptado = self.encriptar_password(password)

            resultado = self.usuarios.insert_one({
                "nombre": nombre,
                "email": email,
                "password": password_encriptado,
                """Guardamos la contra encriptada"""  
                "fecha_registro": datetime.now(),
                "activo": True
            })
            return str(resultado.inserted_id)
        except DuplicateKeyError:
            print(f"❌ Error: El email {email} ya está registrado")
            return None
    
    def obtener_usuario2(self, email: str, pass1: str) -> Optional[Dict]:
        try:
            usuario = self.usuarios.find_one({"email": email})
            
            if not usuario:
                return None
            """desencriptamos la contra guardada"""
            password_guardada = self.desencriptar_password(usuario ["password"])
            """comparamos contraseñas"""
            if password_guardada == pass1:
                usuario['_id'] = str(usuario['_id'])
                return usuario

            return None

        except Exception as e:
            print(f"Error al obtener usuario: {e}")
            return None
    
    def obtener_usuario(self, usuario_id: str):

        usuario = self.usuarios.find_one({
        "_id": ObjectId(usuario_id)})

        if usuario:
           usuario["_id"] = str(usuario["_id"])

        return usuario

    def crear_tarea(self, usuario_id: str, titulo: str, descripcion: str = "", 
                    fecha_limite: Optional[datetime] = None, prioridad: str = "media") -> Optional[str]:
        """Crear una nueva tarea para un usuario"""
        # Verificar que el usuario existe
        if not self.obtener_usuario(usuario_id):
            print(f"❌ Error: Usuario {usuario_id} no existe")
            return None
        
        tarea = {
            "usuario_id": ObjectId(usuario_id),
            "titulo": titulo,
            "descripcion": descripcion,
            "estado": "pendiente",
            "prioridad": prioridad,
            "fecha_creacion": datetime.now(),
            "fecha_limite": fecha_limite or datetime.now() + timedelta(days=7),
            "completada": False,
            "etiquetas": []
        }
        
        resultado = self.tareas.insert_one(tarea)
        return str(resultado.inserted_id)
    
    def obtener_tareas_usuario(self, usuario_id: str, estado: Optional[str] = None) -> List[Dict]:
        """Obtener tareas de un usuario, opcionalmente filtradas por estado"""
        filtro = {"usuario_id": ObjectId(usuario_id)}
        if estado:
            filtro["estado"] = estado
        
        tareas = self.tareas.find(filtro).sort("fecha_creacion", -1)
        resultado = []
        for t in tareas:
            t['_id'] = str(t['_id'])
            t['usuario_id'] = str(t['usuario_id'])
            resultado.append(t)
        return resultado
    
    def actualizar_estado_tarea(self, tarea_id: str, nuevo_estado: str) -> bool:
        """Actualizar el estado de una tarea"""
        estados_validos = ["pendiente", "en_progreso", "completada", "cancelada"]
        if nuevo_estado not in estados_validos:
            print(f"❌ Error: Estado '{nuevo_estado}' no válido")
            return False
        
        resultado = self.tareas.update_one(
            {"_id": ObjectId(tarea_id)},
            {
                "$set": {
                    "estado": nuevo_estado,
                    "completada": nuevo_estado == "completada",
                    "fecha_actualizacion": datetime.now()
                }
            }
        )
        return resultado.modified_count > 0
    
    def agregar_etiqueta(self, tarea_id: str, etiqueta: str) -> bool:
        """Agregar etiqueta a una tarea"""
        resultado = self.tareas.update_one(
            {"_id": ObjectId(tarea_id)},
            {"$addToSet": {"etiquetas": etiqueta}}
        )
        return resultado.modified_count > 0
    
    def eliminar_tarea(self, tarea_id: str) -> bool:
        """Eliminar una tarea"""
        resultado = self.tareas.delete_one({"_id": ObjectId(tarea_id)})
        return resultado.deleted_count > 0
    
    def estadisticas_usuario(self, usuario_id: str) -> Dict:
        """Obtener estadísticas de tareas de un usuario"""
        pipeline = [
            {"$match": {"usuario_id": ObjectId(usuario_id)}},
            {"$group": {
                "_id": "$estado",
                "cantidad": {"$sum": 1},
                "fecha_ultima": {"$max": "$fecha_creacion"}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        resultados = list(self.tareas.aggregate(pipeline))
        
        # Formatear resultados
        estadisticas = {
            "total": 0,
            "por_estado": {},
            "ultima_actividad": None
        }
        
        for r in resultados:
            estado = r['_id']
            cantidad = r['cantidad']
            estadisticas["por_estado"][estado] = cantidad
            estadisticas["total"] += cantidad
            
            if not estadisticas["ultima_actividad"] or r['fecha_ultima'] > estadisticas["ultima_actividad"]:
                estadisticas["ultima_actividad"] = r['fecha_ultima']
        
        return estadisticas
    
    def buscar_tareas(self, texto: str) -> List[Dict]:
        """Buscar tareas por texto en título o descripción"""
        # Requiere índice de texto en 'titulo' y 'descripcion'
        tareas = self.tareas.find({
            "$text": {"$search": texto}
        }).sort({"score": {"$meta": "textScore"}})
        
        resultado = []
        for t in tareas:
            t['_id'] = str(t['_id'])
            t['usuario_id'] = str(t['usuario_id'])
            resultado.append(t)
        return resultado
    
    def tareas_urgentes(self, horas: int = 24) -> List[Dict]:
        """Encontrar tareas que vencen en las próximas N horas"""
        ahora = datetime.now()
        limite = ahora + timedelta(hours=horas)
        
        tareas = self.tareas.find({
            "estado": {"$ne": "completada"},
            "fecha_limite": {"$gte": ahora, "$lte": limite}
        }).sort("fecha_limite", 1)
        
        resultado = []
        for t in tareas:
            t['_id'] = str(t['_id'])
            t['usuario_id'] = str(t['usuario_id'])
            resultado.append(t)
        return resultado
    
    def cerrar_conexion(self):
        """Cerrar conexión a MongoDB"""
        if self.cliente:
            self.cliente.close()
            print("🔌 Conexión cerrada")

            from datetime import datetime

# Ejemplo de uso
def ejemplo_uso():
    # Inicializar gestor
    gestor = GestorTareas()
    
    # Crear usuario
    usuario_id = gestor.crear_usuario("Ana García", "ana@email.com", "1234")
    print(f"Usuario creado con ID: {usuario_id}")
    
    if usuario_id:
        # Crear tareas
        tarea1 = gestor.crear_tarea(
            usuario_id, 
            "Aprender MongoDB", 
            "Completar tutorial de PyMongo",
            datetime.now() + timedelta(days=3)
        )
        print(f"Tarea creada: {tarea1}")
        
        tarea2 = gestor.crear_tarea(
            usuario_id,
            "Hacer ejercicio",
            "Ir al gimnasio 3 veces esta semana"
        )
        
        # Agregar etiqueta
        gestor.agregar_etiqueta(tarea1, "programación")
        gestor.agregar_etiqueta(tarea1, "estudio")
        
        # Listar tareas
        tareas = gestor.obtener_tareas_usuario(usuario_id)
        print(f"\nTareas de {usuario_id}:")
        for t in tareas:
            print(f"  - {t['titulo']} [{t['estado']}]")
        
        # Actualizar estado
        gestor.actualizar_estado_tarea(tarea1, "en_progreso")
        
        # Estadísticas
        stats = gestor.estadisticas_usuario(usuario_id)
        print(f"\nEstadísticas: {stats}")
        
        # Tareas urgentes
        urgentes = gestor.tareas_urgentes(72)
        print(f"\nTareas urgentes próximos 3 días: {len(urgentes)}")
    
    # Cerrar conexión
    gestor.cerrar_conexion()
    
if __name__ == "__main__":
    ejemplo_uso()