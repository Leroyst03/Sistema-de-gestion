#!/usr/bin/env python3
import sys
import os

# Añadir el directorio raíz al path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Punto de entrada de la aplicación"""
    from Controller.MainController import MainController
    
    # Crear y ejecutar el controlador principal
    controller = MainController()

if __name__ == "__main__":
    main()