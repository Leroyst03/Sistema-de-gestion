import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QObject

from Model.DataProvider import DataProvider
from View.MainWindow import MainWindow

class MainController(QObject):
    def __init__(self):
        super().__init__()
        self.app = QApplication(sys.argv)
        
        # Cargar estilos
        self.cargar_estilos()
        
        # Inicializar componentes MVC
        self.view = MainWindow()
        self.model = DataProvider()
        
        # Conectar señales
        self.conectar_señales()
        
        # Variables de estado
        self.current_pallet_id = None
        self.current_image_path = None
        
        # Cache de datos de pallets
        self.pallets_data = []
        
        # Mostrar ventana
        self.view.show()
        sys.exit(self.app.exec_())
    
    def cargar_estilos(self):
        """Cargar archivo de estilos QSS"""
        try:
            with open("Static/Styles/estilos.qss", "r") as f:
                estilo = f.read()
                self.app.setStyleSheet(estilo)
        except FileNotFoundError:
            print("Archivo de estilos no encontrado, usando estilos por defecto")
    
    def conectar_señales(self):
        """Conectar todas las señales entre vista y controlador"""
        # Menú
        self.view.salir_app.connect(self.on_salir)
        
        # Pallets y mapa
        self.view.pallet_seleccionado.connect(self.on_pallet_seleccionado)
        self.view.propiedades_actualizadas.connect(self.on_propiedades_actualizadas)
        self.view.imagen_cargada.connect(self.on_imagen_cargada)
    
    def cargar_pallets(self):
        """Cargar todos los pallets de la base de datos y dibujarlos"""
        # Solo cargar si hay imagen
        if not self.current_image_path:
            return
            
        # Obtener pallets de la base de datos
        self.pallets_data = self.model.get_all_pallets()
        
        # Dibujar cada pallet
        for pallet in self.pallets_data:
            self.view.dibujar_pallet(pallet)
    
    def on_imagen_cargada(self, image_path: str):
        """Manejador para cargar nueva imagen"""
        # Limpiar la escena primero
        self.view.limpiar_escena()
        
        # Cargar la imagen
        if self.view.cargar_imagen_fondo(image_path):
            self.current_image_path = image_path
            
            # Iniciar el monitoreo de I/O (esto actualizará con valores reales)
            if hasattr(self.view, 'io_controller'):
                self.view.io_controller.start_monitoring()
            
            # Cargar pallets después de cargar la imagen
            self.cargar_pallets()
            
            QMessageBox.information(self.view, "Éxito", "Mapa cargado correctamente")
    
    def on_pallet_seleccionado(self, pallet_id: int):
        """Manejador cuando se selecciona un pallet"""
        self.current_pallet_id = pallet_id
        pallet_data = self.model.get_pallet_by_id(pallet_id)
        if pallet_data:
            self.view.mostrar_propiedades_pallet(pallet_data)
    
    def on_propiedades_actualizadas(self, propiedades: dict):
        """Manejador cuando se actualizan propiedades de un pallet"""
        if self.current_pallet_id:
            # No permitir actualizar coordenadas X, Y (son fijas)
            if "X" in propiedades or "Y" in propiedades:
                QMessageBox.warning(self.view, "Error", "Las coordenadas X e Y no se pueden editar directamente")
                return
            
            # Actualizar en base de datos
            self.model.update_pallet(self.current_pallet_id, **propiedades)
            
            # Actualizar el cache local
            pallet_data = self.model.get_pallet_by_id(self.current_pallet_id)
            
            # Si se actualizó la visibilidad, redibujar
            if "Visibilidad" in propiedades and pallet_data:
                # Actualizar visualmente solo el pallet modificado
                self.view.actualizar_pallet_visual(self.current_pallet_id, pallet_data)
                
                # Actualizar también en el cache
                for i, pallet in enumerate(self.pallets_data):
                    if pallet["ID"] == self.current_pallet_id:
                        self.pallets_data[i].update(propiedades)
                        break
            
            QMessageBox.information(self.view, "Éxito", "Propiedades actualizadas correctamente")
    
    def on_salir(self):
        """Manejador para Salir de la aplicación"""
        reply = QMessageBox.question(
            self.view, 'Salir',
            '¿Está seguro de salir de la aplicación?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.app.quit()