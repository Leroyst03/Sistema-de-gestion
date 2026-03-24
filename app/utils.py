import sys
import os

def resource_path(relative_path):
    """Obtiene la ruta absoluta de un recurso, funcionando tanto en desarrollo como en el ejecutable."""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)