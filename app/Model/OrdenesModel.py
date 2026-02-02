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
            cursor.execute("SELECT * FROM ordenes ORDER BY Destino")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_next_destination(self) -> int:
        """Obtener el próximo destino disponible (del 1 al 11, cíclico)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(Destino) FROM ordenes")
            result = cursor.fetchone()[0]
            
            if result is None:
                return 1
            else:
                next_dest = result + 1
                return next_dest if next_dest <= 11 else 1
    
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