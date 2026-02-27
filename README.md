# 🏭 Sistema de Gestión de Pallets

Aplicación de escritorio desarrollada en **Python + PyQt5** para la gestión visual de pallets sobre un mapa de planta. Permite visualizar, seleccionar y gestionar pallets en tiempo real, asignarles órdenes de movimiento y monitorear señales de entradas/salidas digitales (I/O).

---

## 🖼️ Descripción general

El sistema carga un mapa de planta (imagen) como fondo y superpone sobre él los pallets almacenados en base de datos. El operario puede seleccionar un pallet, consultar y editar sus propiedades, añadirlo a una lista de órdenes de movimiento y observar el estado en tiempo real de las señales digitales del sistema.

La arquitectura sigue el patrón **MVC (Modelo - Vista - Controlador)**, separando claramente la lógica de negocio, la interfaz gráfica y el acceso a datos.

---

## 🛠️ Tecnologías utilizadas

- **Python 3.8+**
- **PyQt5** — Interfaz gráfica de escritorio
- **SQLite3** — Base de datos local (sin servidor)

---

## 📁 Estructura del proyecto

```
Sistema-de-gestion/
└── app/
    ├── main.py                         # Punto de entrada
    ├── Controller/
    │   ├── MainController.py           # Controlador principal
    │   ├── OrdenesController.py        # Lógica de órdenes de movimiento
    │   └── IOController.py             # Monitoreo de señales I/O
    ├── Model/
    │   ├── DataProvider.py             # CRUD de pallets (pallets.db)
    │   ├── OrdenesModel.py             # CRUD de órdenes (ordenes.db)
    │   └── IOProvider.py               # Lectura/escritura de I/O (IO.db)
    ├── View/
    │   ├── MainWindow.py               # Ventana principal con mapa interactivo
    │   ├── OrdenesWidget.py            # Panel de lista de órdenes
    │   ├── IOWidget.py                 # Panel de visualización de señales I/O
    │   └── ui_mainwindow.py            # UI generada por Qt Designer
    ├── DB/                             # Bases de datos SQLite (generadas automáticamente)
    │   ├── pallets.db
    │   ├── ordenes.db
    │   └── IO.db
    └── Static/
        └── Styles/
            └── estilos.qss             # Hoja de estilos de la aplicación
```

---

## ⚙️ Requisitos previos

- Python 3.8 o superior
- pip

---

## 🚀 Instalación y uso

1. **Clona el repositorio:**
   ```bash
   git clone https://github.com/Leroyst03/Sistema-de-gestion.git
   cd Sistema-de-gestion
   ```

2. **(Recomendado) Crea un entorno virtual:**
   ```bash
   python -m venv venv
   source venv/bin/activate        # Linux/macOS
   venv\Scripts\activate           # Windows
   ```

3. **Instala las dependencias:**
   ```bash
   pip install PyQt5
   ```

4. **Ejecuta la aplicación:**
   ```bash
   python app/main.py
   ```

---

## 🗄️ Bases de datos

El sistema utiliza tres bases de datos SQLite que se crean automáticamente en la carpeta `DB/` al iniciar la aplicación:

| Base de datos | Tabla | Descripción |
|---|---|---|
| `pallets.db` | `pallets` | Almacena todos los pallets con sus propiedades y coordenadas |
| `ordenes.db` | `ordenes` | Almacena las órdenes de movimiento origen→destino |
| `IO.db` | `io_data` | Almacena los valores binarios de entradas y salidas digitales |

### Esquema de `pallets`

| Campo | Tipo | Descripción |
|---|---|---|
| ID | TEXT (PK) | Identificador hexadecimal único |
| Largo, Ancho, Alto | REAL | Dimensiones físicas del pallet |
| Posicion | INTEGER | Posición lógica en planta |
| Calidad | INTEGER | Nivel de calidad |
| Peso | REAL | Peso del pallet |
| Prioridad | INTEGER | Prioridad de procesamiento |
| X, Y | REAL | Coordenadas en el mapa (en metros) |
| Ocupado | BOOLEAN | Estado de ocupación |

### Esquema de `ordenes`

| Campo | Tipo | Descripción |
|---|---|---|
| ID | TEXT (PK) | Clave hexadecimal |
| Origen | INTEGER | Posición de origen del pallet |
| Destino | INTEGER | Destino asignado (cíclico 1–11) |
| Pallet_ID | TEXT (FK) | Referencia al pallet asociado |

---

## 🧩 Funcionalidades principales

**Gestión visual del mapa**
- Carga de una imagen de planta (`.png`, `.jpg`, `.bmp`) como fondo
- Representación gráfica de los pallets sobre el mapa con zoom y desplazamiento
- Pallets libres en azul oscuro/marrón y ocupados en gris
- Selección de pallets con clic

**Propiedades de pallets**
- Visualización de todas las propiedades del pallet seleccionado en una tabla
- Edición directa de propiedades (largo, ancho, alto, peso, calidad, prioridad, ocupado)
- Las coordenadas X/Y son de solo lectura (se posicionan desde la base de datos)

**Gestión de órdenes**
- Añadir el pallet seleccionado a la lista de órdenes (marca el pallet como ocupado automáticamente)
- Reordenar órdenes con los botones subir/bajar (intercambia destinos)
- Eliminar órdenes (libera el pallet automáticamente)
- Destinos asignados de forma cíclica del 1 al 11

**Monitoreo de señales I/O**
- Panel con 5 entradas y 5 salidas digitales representadas como indicadores visuales (verde/rojo)
- Actualización automática cada 500ms desde la base de datos `IO.db`
- El monitoreo se activa al cargar un mapa y se detiene al cerrarlo

---

## 🏗️ Arquitectura (MVC)

```
MainController
├── MainWindow (Vista principal)
│   ├── GraphicsView      → Mapa interactivo con zoom
│   ├── propiedadesTable  → Propiedades del pallet seleccionado
│   └── IOWidget          → Indicadores de señales I/O
├── OrdenesController
│   ├── OrdenesModel      → CRUD en ordenes.db
│   └── OrdenesWidget     → Tabla de órdenes con botones
├── IOController
│   ├── IOProvider        → Lectura de IO.db
│   └── IOWidget          → Visualización de bits I/O
└── DataProvider          → CRUD en pallets.db
```

---
