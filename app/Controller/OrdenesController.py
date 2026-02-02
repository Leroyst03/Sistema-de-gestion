from PyQt5.QtCore import QObject, QTimer
from Model.OrdenesModel import OrdenesModel
from Model.DataProvider import DataProvider
from View.OrdenesWidget import OrdenesWidget

class OrdenesController(QObject):
    def __init__(self, data_provider: DataProvider = None):
        super().__init__()
        self.model = OrdenesModel()
        self.data_provider = data_provider or DataProvider()
        self.view = OrdenesWidget()
        
        # Variable para almacenar el pallet seleccionado
        self.current_pallet_id = None
        self.current_pallet_position = None
        
        # Conectar señales
        self.view.add_order_requested.connect(self.add_order)
        self.view.delete_order_requested.connect(self.delete_order)
        self.view.move_up_requested.connect(self.move_order_up)
        self.view.move_down_requested.connect(self.move_order_down)
        self.view.selection_changed.connect(self.on_order_selected)
        
        # Cargar órdenes existentes
        self.load_orders()
    
    def set_current_pallet(self, pallet_id: int):
        """Establecer el pallet actual seleccionado"""
        self.current_pallet_id = pallet_id
        if pallet_id:
            pallet_data = self.data_provider.get_pallet_by_id(pallet_id)
            if pallet_data:
                self.current_pallet_position = pallet_data.get("Posicion")
    
    def add_order(self):
        """Añadir una nueva orden basada en el pallet seleccionado"""
        if not self.current_pallet_id or not self.current_pallet_position:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(
                self.view, 
                "Sin pallet seleccionado",
                "Por favor, seleccione un pallet primero para obtener su posición."
            )
            return
        
        try:
            # Insertar nueva orden
            order_id = self.model.insert_order(
                origen=self.current_pallet_position,
                pallet_id=self.current_pallet_id
            )
            
            # Actualizar vista
            orders = self.model.get_all_orders()
            self.view.clear_orders()
            for order in orders:
                self.view.add_order_item(
                    order_id=order["ID"],
                    origen=order["Origen"],
                    destino=order["Destino"],
                    pallet_id=order["Pallet_ID"]
                )
            
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self.view,
                "Error al añadir orden",
                f"No se pudo añadir la orden: {str(e)}"
            )
    
    def delete_order(self, order_id: int):
        """Eliminar una orden"""
        try:
            self.model.delete_order(order_id)
            self.view.remove_order_item(order_id)
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self.view,
                "Error al eliminar orden",
                f"No se pudo eliminar la orden: {str(e)}"
            )
    
    def move_order_up(self, order_id: int):
        """Mover orden hacia arriba en la lista (disminuir destino)"""
        try:
            orders = self.model.get_all_orders()
            current_index = -1
            
            # Encontrar índice actual
            for i, order in enumerate(orders):
                if order["ID"] == order_id:
                    current_index = i
                    break
            
            if current_index > 0:  # No es el primero
                prev_order = orders[current_index - 1]
                # Intercambiar destinos
                self.model.swap_destinations(order_id, prev_order["ID"])
                self.refresh_orders_list()
                
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self.view,
                "Error al mover orden",
                f"No se pudo mover la orden: {str(e)}"
            )
    
    def move_order_down(self, order_id: int):
        """Mover orden hacia abajo en la lista (aumentar destino)"""
        try:
            orders = self.model.get_all_orders()
            current_index = -1
            
            # Encontrar índice actual
            for i, order in enumerate(orders):
                if order["ID"] == order_id:
                    current_index = i
                    break
            
            if current_index < len(orders) - 1:  # No es el último
                next_order = orders[current_index + 1]
                # Intercambiar destinos
                self.model.swap_destinations(order_id, next_order["ID"])
                self.refresh_orders_list()
                
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self.view,
                "Error al mover orden",
                f"No se pudo mover la orden: {str(e)}"
            )
    
    def on_order_selected(self, order_id: int):
        """Manejador cuando se selecciona una orden"""
        # Aquí puedes implementar lógica adicional si es necesario
        pass
    
    def load_orders(self):
        """Cargar todas las órdenes en la vista"""
        orders = self.model.get_all_orders()
        for order in orders:
            self.view.add_order_item(
                order_id=order["ID"],
                origen=order["Origen"],
                destino=order["Destino"],
                pallet_id=order["Pallet_ID"]
            )
    
    def refresh_orders_list(self):
        """Refrescar la lista de órdenes"""
        orders = self.model.get_all_orders()
        self.view.clear_orders()
        for order in orders:
            self.view.add_order_item(
                order_id=order["ID"],
                origen=order["Origen"],
                destino=order["Destino"],
                pallet_id=order["Pallet_ID"]
            )
    
    def get_widget(self):
        """Obtener el widget para insertar en la interfaz principal"""
        return self.view