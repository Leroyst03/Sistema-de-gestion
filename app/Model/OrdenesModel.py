import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional

class OrdenesModel:
    def __init__(self, db_path: str = "DB/ordenes.db"):
        self.db_path = db_path
        self._create_database()
    
    def _create_database(self):
        """Crear la base de datos y la tabla si no existen"""
        Path("DB").mkdir(exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ordenes (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    Origen INTEGER NOT NULL,
                    Destino INTEGER NOT NULL,
                    Pallet_ID INTEGER,
                    FOREIGN KEY (Pallet_ID) REFERENCES pallets(ID)
                )
            """)
            conn.commit()
    
    def get_all_orders(self) -> List[Dict[str, Any]]:
        """Obtener todas las órdenes de la base de datos"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ordenes ORDER BY Destino, ID")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_next_destination(self) -> int:
        """
        Obtener el próximo destino (1-11 cíclico puro).
        Este es un contador cíclico que siempre sigue la secuencia 1-11.
        NO busca huecos, simplemente asigna el siguiente en la secuencia.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Contar cuántas órdenes hay en total
            cursor.execute("SELECT COUNT(*) FROM ordenes")
            total_ordenes = cursor.fetchone()[0]
            
            if total_ordenes == 0:
                return 1  # Primera orden siempre destino 1
            
            # Obtener el último destino asignado (ordenado por ID, no por Destino)
            cursor.execute("SELECT Destino FROM ordenes ORDER BY ID DESC LIMIT 1")
            ultimo_destino = cursor.fetchone()[0]
            
            # Calcular próximo destino cíclico (1-11)
            siguiente_destino = ultimo_destino + 1
            if siguiente_destino > 11:
                siguiente_destino = 1
            
            return siguiente_destino
    
    def insert_order(self, origen: int, pallet_id: int = None) -> int:
        """Insertar una nueva orden y retornar su ID"""
        destino = self.get_next_destination()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO ordenes (Origen, Destino, Pallet_ID) VALUES (?, ?, ?)",
                (origen, destino, pallet_id)
            )
            conn.commit()
            return cursor.lastrowid
    
    def delete_order(self, order_id: int):
        """Eliminar una orden por su ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ordenes WHERE ID = ?", (order_id,))
            conn.commit()
    
    def update_destination(self, order_id: int, destino: int):
        """Actualizar el destino de una orden"""
        # Asegurarse de que el destino esté en rango 1-11
        if destino < 1 or destino > 11:
            raise ValueError(f"Destino {destino} fuera de rango. Debe estar entre 1 y 11.")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE ordenes SET Destino = ? WHERE ID = ?",
                (destino, order_id)
            )
            conn.commit()
    
    def swap_destinations(self, order_id1: int, order_id2: int):
        """Intercambiar destinos entre dos órdenes"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Obtener destinos actuales
            cursor.execute("SELECT Destino FROM ordenes WHERE ID = ?", (order_id1,))
            dest1 = cursor.fetchone()[0]
            
            cursor.execute("SELECT Destino FROM ordenes WHERE ID = ?", (order_id2,))
            dest2 = cursor.fetchone()[0]
            
            # Intercambiar
            cursor.execute("UPDATE ordenes SET Destino = ? WHERE ID = ?", (dest2, order_id1))
            cursor.execute("UPDATE ordenes SET Destino = ? WHERE ID = ?", (dest1, order_id2))
            conn.commit()
    
    def get_destination_sequence(self) -> List[int]:
        """
        Obtener la secuencia completa de destinos según se han asignado.
        Útil para depuración.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT Destino FROM ordenes ORDER BY ID")
            return [row[0] for row in cursor.fetchall()]
    
    def reset_destinations(self):
        """
        Reiniciar todos los destinos para que sigan una secuencia cíclica pura.
        Esto reorganiza las órdenes existentes para que tengan destinos 1-11 en orden.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Obtener todas las órdenes ordenadas por ID
            cursor.execute("SELECT ID FROM ordenes ORDER BY ID")
            orders = cursor.fetchall()
            
            # Asignar destinos cíclicos (1-11)
            for index, (order_id,) in enumerate(orders):
                destino = (index % 11) + 1  # Esto da 1, 2, 3, ..., 10, 11, 1, 2, ...
                cursor.execute(
                    "UPDATE ordenes SET Destino = ? WHERE ID = ?",
                    (destino, order_id)
                )
            
            conn.commit()