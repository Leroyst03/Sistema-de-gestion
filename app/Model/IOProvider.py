import sqlite3
from pathlib import Path

class IOProvider:
    def __init__(self, db_path: str = "DB/IO.db"):
        self.db_path = db_path
        self._create_database()
    
    def _create_database(self):
        """Crear la base de datos IO si no existe"""
        Path("DB").mkdir(exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS io_data (
                    Input INTEGER DEFAULT 0,
                    Output INTEGER DEFAULT 0
                )
            """)
            
            # Verificar si hay datos, si no los hay, insertar (0, 0)
            cursor.execute("SELECT COUNT(*) FROM io_data")
            count = cursor.fetchone()[0]
            if count == 0:
                cursor.execute("INSERT INTO io_data (Input, Output) VALUES (0, 0)")
            conn.commit()
    
    def get_io_data(self):
        """Obtener los valores de Input y Output"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT Input, Output FROM io_data LIMIT 1")
            result = cursor.fetchone()
            return result if result else (0, 0)
    
    def update_io_data(self, input_value: int = None, output_value: int = None):
        """Actualizar los valores de Input y/o Output"""
        updates = []
        values = []
        
        if input_value is not None:
            updates.append("Input = ?")
            values.append(input_value)
        
        if output_value is not None:
            updates.append("Output = ?")
            values.append(output_value)
        
        if not updates:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE io_data SET {', '.join(updates)}", values)
            conn.commit()
    
    def reset_io_data(self):
        """Resetear los valores de IO a 0"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE io_data SET Input = 0, Output = 0")
            conn.commit()