from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QMessageBox
from Model.OrdenesModel import OrdenesModel
from View.OrdenesWidget import OrdenesWidget

class OrdenesController(QObject):
    def __init__(self, model):
        super().__init__()
        self.model = model  # DataProvider
        self.ordenes_model = OrdenesModel()
        self.view = OrdenesWidget()
        self.current_pallet = None
        
        # Conectar señales de la vista
        self.view.add_order_requested.connect(self.add_order)
        self.view.delete_order_requested.connect(self.delete_order)
        self.view.move_up_requested.connect(self.move_up)
        self.view.move_down_requested.connect(self.move_down)
        
        # Cargar órdenes iniciales
        self.load_orders()
    
    def get_widget(self):
        return self.view
    
    def set_current_pallet(self, pallet_id):
        self.current_pallet = pallet_id
    
    def load_orders(self):
        """Cargar todas las órdenes desde la base de datos y mostrarlas en la tabla."""
        self.view.clear_orders()
        orders = self.ordenes_model.get_all_orders()
        for order in orders:
            self.view.add_order_item(
                order_id=order['ID'],
                origen=order['Origen'],
                destino=order['Destino']
            )
    
    def add_order(self):
        if not self.current_pallet:
            QMessageBox.warning(self.view, "Sin pallet", "No hay ningún pallet seleccionado.")
            return
        
        # Obtener datos actualizados del pallet
        pallet_data = self.model.get_pallet_by_id(self.current_pallet)
        if not pallet_data:
            QMessageBox.warning(self.view, "Error", "El pallet seleccionado no existe.")
            return
        
        # Verificar calidad
        calidad = pallet_data.get("Calidad", 0)
        if calidad == 0:
            QMessageBox.warning(
                self.view,
                "Calidad inválida",
                "La calidad del pallet es 0. No se puede agregar a la lista de órdenes. Por favor, cambie la calidad a un valor diferente de 0."
            )
            return
        
        origen = pallet_data.get("Posicion")  # Asumiendo que 'Posicion' es el origen
        # Insertar orden en la base de datos
        self.ordenes_model.insert_order(origen, self.current_pallet)
        self.load_orders()  # Refrescar vista
    
    def delete_order(self, order_id: int):
        """Eliminar una orden por ID."""
        self.ordenes_model.delete_order(order_id)
        self.load_orders()
    
    def delete_order_by_pallet(self, pallet_id: str):
        """Eliminar todas las órdenes asociadas a un pallet específico."""
        orders = self.ordenes_model.get_all_orders()
        for order in orders:
            if order.get('Pallet_ID') == pallet_id:
                self.ordenes_model.delete_order(order['ID'])
        self.load_orders()
    
    def move_up(self, order_id: int):
        """Mover una orden hacia arriba (intercambiar destinos con la anterior)."""
        orders = self.ordenes_model.get_all_orders()
        ids = [o['ID'] for o in orders]
        if order_id in ids:
            idx = ids.index(order_id)
            if idx > 0:
                prev_id = ids[idx - 1]
                self.ordenes_model.swap_destinations(order_id, prev_id)
                self.load_orders()
    
    def move_down(self, order_id: int):
        """Mover una orden hacia abajo (intercambiar destinos con la siguiente)."""
        orders = self.ordenes_model.get_all_orders()
        ids = [o['ID'] for o in orders]
        if order_id in ids:
            idx = ids.index(order_id)
            if idx < len(ids) - 1:
                next_id = ids[idx + 1]
                self.ordenes_model.swap_destinations(order_id, next_id)
                self.load_orders()