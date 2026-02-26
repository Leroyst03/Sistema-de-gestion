import sys
from PyQt5.QtWidgets import QApplication, QMessageBox, QSizePolicy
from PyQt5.QtCore import QObject

from Model.DataProvider import DataProvider
from View.MainWindow import MainWindow
from Controller.OrdenesController import OrdenesController

class MainController(QObject):
    def __init__(self):
        super().__init__()
        self.app = QApplication(sys.argv)
        self.cargar_estilos()
        
        self.view = MainWindow()
        self.model = DataProvider()
        self.ordenes_controller = OrdenesController(self.model)
        
        # Conectar señales del controlador de órdenes para actualizar vista
        self.ordenes_controller.order_added.connect(self.on_pallet_ocupado_changed)
        self.ordenes_controller.order_deleted.connect(self.on_pallet_ocupado_changed)
        
        self.setup_ordenes_widget()
        self.conectar_señales()
        
        self.current_pallet_id = None
        self.current_image_path = None
        self.pallets_data = []
        
        self.view.show()
        sys.exit(self.app.exec_())
    
    def cargar_estilos(self):
        try:
            with open("Static/Styles/estilos.qss", "r") as f:
                estilo = f.read()
                self.app.setStyleSheet(estilo)
        except FileNotFoundError:
            print("Archivo de estilos no encontrado, usando estilos por defecto")
    
    def setup_ordenes_widget(self):
        while self.view.ui.ordenesLayout.count():
            item = self.view.ui.ordenesLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        ordenes_widget = self.ordenes_controller.get_widget()
        ordenes_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.view.ui.ordenesLayout.addWidget(ordenes_widget)
    
    def conectar_señales(self):
        self.view.salir_app.connect(self.on_salir)
        self.view.pallet_seleccionado.connect(self.on_pallet_seleccionado)
        self.view.propiedades_actualizadas.connect(self.on_propiedades_actualizadas)
        self.view.imagen_cargada.connect(self.on_imagen_cargada)
        self.view.add_to_orders_clicked.connect(self.on_add_to_orders_clicked)
    
    def cargar_pallets(self):
        if not self.current_image_path:
            return
        self.pallets_data = self.model.get_all_pallets()
        for pallet in self.pallets_data:
            self.view.dibujar_pallet(pallet)
    
    def on_imagen_cargada(self, image_path: str):
        self.view.limpiar_escena()
        if self.view.cargar_imagen_fondo(image_path):
            self.current_image_path = image_path
            if hasattr(self.view, 'io_controller'):
                self.view.io_controller.start_monitoring()
            self.view.mostrar_panel_ordenes()
            self.cargar_pallets()
            self.ordenes_controller.load_orders()
            QMessageBox.information(self.view, "Éxito", "Mapa cargado correctamente")
    
    def on_pallet_seleccionado(self, pallet_id: str):
        self.current_pallet_id = pallet_id
        pallet_data = self.model.get_pallet_by_id(pallet_id)
        if pallet_data:
            self.view.mostrar_propiedades_pallet(pallet_data)
            self.ordenes_controller.set_current_pallet(pallet_id)
    
    def on_add_to_orders_clicked(self):
        if not self.current_image_path:
            QMessageBox.warning(self.view, "Mapa no cargado", "Por favor, cargue un mapa primero antes de añadir órdenes.")
            return
        if self.current_pallet_id:
            self.ordenes_controller.add_order()
        else:
            QMessageBox.warning(self.view, "Sin pallet seleccionado", "Por favor, seleccione un pallet primero.")
    
    def on_propiedades_actualizadas(self, propiedades: dict):
        if self.current_pallet_id:
            if "X" in propiedades or "Y" in propiedades:
                QMessageBox.warning(self.view, "Error", "Las coordenadas X e Y no se pueden editar directamente")
                return
            
            self.model.update_pallet(self.current_pallet_id, **propiedades)
            pallet_data = self.model.get_pallet_by_id(self.current_pallet_id)
            
            if "Ocupado" in propiedades and pallet_data:
                self.view.actualizar_pallet_visual(self.current_pallet_id, pallet_data)
                for i, pallet in enumerate(self.pallets_data):
                    if pallet["ID"] == self.current_pallet_id:
                        self.pallets_data[i].update(propiedades)
                        break
            
            QMessageBox.information(self.view, "Éxito", "Propiedades actualizadas correctamente")
    
    def on_pallet_ocupado_changed(self, pallet_id: str):
        """Actualizar la vista de un pallet cuando cambia su estado de ocupado por órdenes"""
        pallet_data = self.model.get_pallet_by_id(pallet_id)
        if pallet_data:
            self.view.actualizar_pallet_visual(pallet_id, pallet_data)
            # Actualizar también el cache local
            for i, pallet in enumerate(self.pallets_data):
                if pallet["ID"] == pallet_id:
                    self.pallets_data[i] = pallet_data
                    break
            # Si el pallet es el actualmente seleccionado, actualizar la tabla de propiedades
            if self.current_pallet_id == pallet_id:
                self.view.mostrar_propiedades_pallet(pallet_data)
    
    def on_salir(self):
        reply = QMessageBox.question(self.view, 'Salir', '¿Está seguro de salir de la aplicación?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.app.quit()