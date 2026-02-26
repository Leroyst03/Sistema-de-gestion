from PyQt5.QtCore import QObject, pyqtSignal
from Model.OrdenesModel import OrdenesModel
from Model.DataProvider import DataProvider
from View.OrdenesWidget import OrdenesWidget

class OrdenesController(QObject):
    # Señales para notificar cambios en órdenes
    order_added = pyqtSignal(str)   # pallet_id
    order_deleted = pyqtSignal(str) # pallet_id

    def __init__(self, data_provider: DataProvider = None):
        super().__init__()
        self.model = OrdenesModel()
        self.data_provider = data_provider or DataProvider()
        self.view = OrdenesWidget()
        
        self.current_pallet_id = None
        self.current_pallet_position = None
        
        self.ordenes_cargadas = False
        
        self.view.add_order_requested.connect(self.add_order)
        self.view.delete_order_requested.connect(self.delete_order)
        self.view.move_up_requested.connect(self.move_order_up)
        self.view.move_down_requested.connect(self.move_order_down)
        self.view.selection_changed.connect(self.on_order_selected)
    
    def set_current_pallet(self, pallet_id: str):
        self.current_pallet_id = pallet_id
        if pallet_id:
            pallet_data = self.data_provider.get_pallet_by_id(pallet_id)
            if pallet_data:
                self.current_pallet_position = pallet_data.get("Posicion")
    
    def add_order(self):
        if not self.ordenes_cargadas:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self.view, "Mapa no cargado", "Por favor, cargue un mapa primero antes de añadir órdenes.")
            return
        
        if not self.current_pallet_id or not self.current_pallet_position:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self.view, "Sin pallet seleccionado", "Por favor, seleccione un pallet primero para obtener su posición.")
            return
        
        try:
            # Verificar si el pallet ya está en una orden
            orders = self.model.get_all_orders()
            existing_order = next((order for order in orders 
                                 if order.get("Pallet_ID") == self.current_pallet_id), None)
            
            if existing_order:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self.view,
                    "Pallet ya en órdenes",
                    "Este pallet ya se encuentra en la lista de órdenes."
                )
                return
            
            # Verificar si el pallet ya está ocupado (por ejemplo, manualmente)
            pallet_data = self.data_provider.get_pallet_by_id(self.current_pallet_id)
            if pallet_data and pallet_data.get("Ocupado") == 1:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self.view,
                    "Pallet ocupado",
                    "Este pallet ya se encuentra ocupado. No se puede añadir a la lista."
                )
                return
            
            # Insertar nueva orden
            order_id = self.model.insert_order(
                origen=self.current_pallet_position,
                pallet_id=self.current_pallet_id
            )
            
            # Marcar el pallet como ocupado
            self.data_provider.update_pallet(self.current_pallet_id, Ocupado=1)
            
            # Notificar que se añadió la orden
            self.order_added.emit(self.current_pallet_id)
            
            # Refrescar la lista de órdenes en la vista
            self.refresh_orders_list()
            
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self.view, "Error al añadir orden", f"No se pudo añadir la orden: {str(e)}")
    
    def delete_order(self, order_id: int):
        try:
            # Obtener el pallet_id antes de eliminar la orden
            orders = self.model.get_all_orders()
            order = next((o for o in orders if o["ID"] == order_id), None)
            if order:
                pallet_id = order.get("Pallet_ID")
                # Eliminar la orden
                self.model.delete_order(order_id)
                # Si la orden tenía un pallet asociado, marcarlo como no ocupado
                if pallet_id:
                    self.data_provider.update_pallet(pallet_id, Ocupado=0)
                    self.order_deleted.emit(pallet_id)
                # Actualizar vista
                self.view.remove_order_item(order_id)
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self.view, "Error al eliminar orden", f"No se pudo eliminar la orden: {str(e)}")
    
    def move_order_up(self, order_id: int):
        try:
            orders = self.model.get_all_orders()
            current_index = -1
            for i, order in enumerate(orders):
                if order["ID"] == order_id:
                    current_index = i
                    break
            if current_index > 0:
                prev_order = orders[current_index - 1]
                self.model.swap_destinations(order_id, prev_order["ID"])
                self.refresh_orders_list()
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self.view, "Error al mover orden", f"No se pudo mover la orden: {str(e)}")
    
    def move_order_down(self, order_id: int):
        try:
            orders = self.model.get_all_orders()
            current_index = -1
            for i, order in enumerate(orders):
                if order["ID"] == order_id:
                    current_index = i
                    break
            if current_index < len(orders) - 1:
                next_order = orders[current_index + 1]
                self.model.swap_destinations(order_id, next_order["ID"])
                self.refresh_orders_list()
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self.view, "Error al mover orden", f"No se pudo mover la orden: {str(e)}")
    
    def on_order_selected(self, order_id: int):
        pass
    
    def load_orders(self):
        """Cargar todas las órdenes en la vista y sincronizar estado ocupado"""
        self.ordenes_cargadas = True
        orders = self.model.get_all_orders()
        for order in orders:
            self.view.add_order_item(
                order_id=order["ID"],
                origen=order["Origen"],
                destino=order["Destino"]
            )
            # Asegurar que el pallet asociado esté marcado como ocupado
            pallet_id = order.get("Pallet_ID")
            if pallet_id:
                self.data_provider.update_pallet(pallet_id, Ocupado=1)
                self.order_added.emit(pallet_id)
    
    def refresh_orders_list(self):
        orders = self.model.get_all_orders()
        self.view.clear_orders()
        for order in orders:
            self.view.add_order_item(
                order_id=order["ID"],
                origen=order["Origen"],
                destino=order["Destino"]
            )
    
    def clear_orders(self):
        """Limpiar todas las órdenes de la vista (usado al cerrar mapa)"""
        self.ordenes_cargadas = False
        self.view.clear_orders()
    
    def get_widget(self):
        return self.view