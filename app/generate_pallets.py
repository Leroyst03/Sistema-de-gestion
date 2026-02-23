import random
from Model.DataProvider import DataProvider

# Tamaño del mapa
MAP_WIDTH = 979
MAP_HEIGHT = 599

def generar_pallet():
    """Genera un pallet con datos válidos para la DB."""
    return {
        "Largo": round(random.uniform(0.8, 1.4), 2),
        "Ancho": round(random.uniform(0.8, 1.2), 2),
        "Posicion": random.randint(1, 300),
        "Alto": round(random.uniform(0.5, 2.0), 2),
        "Calidad": random.choice(["A", "B", "C"]),
        "Peso": round(random.uniform(50, 1200), 1),
        "Prioridad": random.randint(1, 5),

        # Coordenadas dentro del mapa
        "X": round(random.uniform(0, MAP_WIDTH), 2),
        "Y": round(random.uniform(0, MAP_HEIGHT), 2),

        # SQLite usa 0/1 para booleanos
        "Visibilidad": random.choice([0, 1])
    }

def poblar_db(cantidad=50):
    db = DataProvider("DB/pallets.db")
    print(f"Insertando {cantidad} pallets en pallets.db...\n")

    for i in range(cantidad):
        pallet = generar_pallet()
        new_id = db.insert_pallet(**pallet)
        print(f"[{i+1}/{cantidad}] Pallet insertado con ID {new_id}")

    print("\n✔ Inserción completada.")

if __name__ == "__main__":
    poblar_db(5)
