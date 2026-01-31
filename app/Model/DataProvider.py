import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional

class DataProvider:
    def __init__(self, db_path: str = "DB/pallets.db"):
        self.db_path = db_path
        self._create_database()
    
    def _create_database(self):
        """Crear la base de datos y la tabla si no existen"""
        Path("DB").mkdir(exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pallets (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    Largo REAL NOT NULL,
                    Ancho REAL NOT NULL,
                    Posicion INTEGER NOT NULL,
                    Alto REAL NOT NULL,
                    Calidad TEXT NOT NULL,
                    Peso REAL NOT NULL,
                    Prioridad INTEGER NOT NULL,
                    X REAL NOT NULL,
                    Y REAL NOT NULL,
                    Visibilidad BOOLEAN NOT NULL
                )
            """)
            conn.commit()
    
    def get_all_pallets(self) -> List[Dict[str, Any]]:
        """Obtener todos los pallets de la base de datos"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pallets")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_pallet_by_id(self, pallet_id: int) -> Optional[Dict[str, Any]]:
        """Obtener un pallet por su ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pallets WHERE ID = ?", (pallet_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_pallet(self, pallet_id: int, **kwargs):
        """Actualizar las propiedades de un pallet"""
        if not kwargs:
            return
        
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values())
        values.append(pallet_id)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE pallets SET {set_clause} WHERE ID = ?", values)
            conn.commit()
    
    def insert_pallet(self, **kwargs) -> int:
        """Insertar un nuevo pallet y retornar su ID"""
        keys = ", ".join(kwargs.keys())
        placeholders = ", ".join(["?" for _ in kwargs])
        values = list(kwargs.values())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"INSERT INTO pallets ({keys}) VALUES ({placeholders})", values)
            conn.commit()
            return cursor.lastrowid
    
    def delete_pallet(self, pallet_id: int):
        """Eliminar un pallet por su ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pallets WHERE ID = ?", (pallet_id,))
            conn.commit()