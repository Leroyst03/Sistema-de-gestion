import random
import uuid
from Model.DataProvider import DataProvider

# Tamaño del mapa en píxeles
MAP_WIDTH_PX = 979
MAP_HEIGHT_PX = 599

# Escala: metros por píxel
ESCALA = 0.05

# Tamaño del mapa en metros
MAP_WIDTH_M = MAP_WIDTH_PX * ESCALA    # 48.95 m
MAP_HEIGHT_M = MAP_HEIGHT_PX * ESCALA  # 29.95 m

def generar_pallet():
    """Genera un pallet con datos válidos para la DB. Incluye un ID hexadecimal único."""
    return {
        "ID": uuid.uuid4().hex[:8],                     # ID hexadecimal de 8 caracteres
        "Largo": round(random.uniform(0.8, 1.4), 2),
        "Ancho": round(random.uniform(0.8, 1.2), 2),
        "Posicion": random.randint(1, 300),
        "Alto": round(random.uniform(0.5, 2.0), 2),
        "Calidad": 0,                                  # Calidad inicial en 0
        "Peso": round(random.uniform(50, 1200), 1),
        "Prioridad": random.randint(1, 5),
        "X": round(random.uniform(0, MAP_WIDTH_M), 2),
        "Y": round(random.uniform(0, MAP_HEIGHT_M), 2),
        "Ocupado": random.choice([0, 1])                 # ← Cambiado a Ocupado
    }

def poblar_db(cantidad=50):
    db = DataProvider("DB/pallets.db")
    print(f"Insertando {cantidad} pallets en pallets.db...\n")

    for i in range(cantidad):
        pallet = generar_pallet()
        new_id = db.insert_pallet(**pallet)
        print(f"[{i+1}/{cantidad}] Pallet insertado con ID {new_id} (X={pallet['X']} m, Y={pallet['Y']} m)")

    print("\n✔ Inserción completada.")

if __name__ == "__main__":
    poblar_db(5)   # Cambia la cantidad de pallets a generar según tus necesidades