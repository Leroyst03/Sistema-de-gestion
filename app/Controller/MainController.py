import sys
from PyQt5.QtWidgets import QApplication, QMessageBox, QSizePolicy
from PyQt5.QtCore import QObject, QTimer

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
        
        self.setup_ordenes_widget()
        self.conectar_señales()
        
        self.current_pallet_id = None
        self.current_image_path = None
        self.pallets_data = []  # Copia en memoria de los datos de los pallets
        
        # Temporizador para actualizar los pallets cada 500 ms
        self.pallet_timer = QTimer()
        self.pallet_timer.timeout.connect(self.update_pallets_display)
        
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
            # Iniciar el temporizador de actualización de pallets
            self.pallet_timer.start(500)
            QMessageBox.information(self.view, "Éxito", "Mapa cargado correctamente")
    
    def on_pallet_seleccionado(self, pallet_id: str):
        self.current_pallet_id = pallet_id
        pallet_data = self.model.get_pallet_by_id(pallet_id)
        if pallet_data:
            if pallet_data.get("Ocupado") == 1:
                self.view.mostrar_propiedades_pallet(pallet_data)
                self.ordenes_controller.set_current_pallet(pallet_id)
            else:
                # Pallet no ocupado: no mostrar propiedades y no permitir agregar a órdenes
                self.view.limpiar_propiedades_pallet()
                self.ordenes_controller.set_current_pallet(None)
    
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
            
            # Guardar el valor anterior de ocupado (si existe) para comparar
            pallet_anterior = self.model.get_pallet_by_id(self.current_pallet_id)
            ocupado_anterior = pallet_anterior.get("Ocupado") if pallet_anterior else None
            
            # Actualizar en base de datos
            self.model.update_pallet(self.current_pallet_id, **propiedades)
            
            # Obtener el nuevo estado
            pallet_data = self.model.get_pallet_by_id(self.current_pallet_id)
            
            # Actualizar la copia en memoria
            for i, pallet in enumerate(self.pallets_data):
                if pallet["ID"] == self.current_pallet_id:
                    self.pallets_data[i].update(propiedades)
                    break
            
            # Si se actualizó el campo Ocupado, redibujar
            if "Ocupado" in propiedades and pallet_data:
                self.view.actualizar_pallet_visual(self.current_pallet_id, pallet_data)
                
                # Si se cambió de ocupado=1 a ocupado=0, eliminar de la lista de órdenes si estaba
                nuevo_ocupado = propiedades["Ocupado"]
                if ocupado_anterior == 1 and nuevo_ocupado == 0:
                    self.ordenes_controller.delete_order_by_pallet(self.current_pallet_id)
                    # Si el pallet actual se desocupó, limpiar propiedades
                    if self.current_pallet_id == pallet_data["ID"]:
                        self.view.limpiar_propiedades_pallet()
                        self.ordenes_controller.set_current_pallet(None)
            
            QMessageBox.information(self.view, "Éxito", "Propiedades actualizadas correctamente")
    
    def update_pallets_display(self):
        """Actualiza la visualización de los pallets si hubo cambios en la base de datos."""
        if not self.current_image_path:
            return
        
        try:
            current_pallets = self.model.get_all_pallets()
        except Exception as e:
            print(f"Error al obtener pallets: {e}")
            return
        
        # Crear un diccionario de los pallets actuales para acceso rápido
        current_dict = {p["ID"]: p for p in current_pallets}
        
        # Verificar pallets que han cambiado o se han eliminado
        pallets_a_actualizar = []
        
        # Primero, verificar cambios en los pallets existentes
        for pallet in self.pallets_data:
            pallet_id = pallet["ID"]
            current = current_dict.get(pallet_id)
            if current is None:
                # El pallet fue eliminado de la base de datos
                pallets_a_actualizar.append((pallet_id, None))
            else:
                # Comparar campos relevantes: Ocupado y Calidad (y cualquier otro que afecte la vista)
                if (pallet.get("Ocupado") != current.get("Ocupado") or
                    pallet.get("Calidad") != current.get("Calidad")):
                    pallets_a_actualizar.append((pallet_id, current))
                # Actualizar la copia en memoria para futuras comparaciones
                pallet.update(current)
        
        # Verificar nuevos pallets (que no estaban en memoria)
        for pallet_id, current in current_dict.items():
            if not any(p["ID"] == pallet_id for p in self.pallets_data):
                # Es un nuevo pallet
                self.pallets_data.append(current)
                pallets_a_actualizar.append((pallet_id, current))
        
        # Aplicar las actualizaciones visuales
        for pallet_id, data in pallets_a_actualizar:
            if data is None:
                # Eliminar pallet de la vista
                # Como no tenemos un método directo para eliminar, podemos redibujar todos,
                # pero para eficiencia, eliminamos los items y luego los volvemos a dibujar
                if pallet_id in self.view.pallet_items:
                    for item in self.view.pallet_items[pallet_id]:
                        self.view.scene.removeItem(item)
                    del self.view.pallet_items[pallet_id]
            else:
                # Actualizar o dibujar nuevo pallet
                self.view.actualizar_pallet_visual(pallet_id, data)
    
    def on_salir(self):
        # Detener temporizadores
        self.pallet_timer.stop()
        if hasattr(self.view, 'io_controller'):
            self.view.io_controller.stop_monitoring()
        
        reply = QMessageBox.question(self.view, 'Salir', '¿Está seguro de salir de la aplicación?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.app.quit()