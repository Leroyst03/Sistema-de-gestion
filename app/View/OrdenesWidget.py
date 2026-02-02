from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QAbstractItemView, 
                             QHeaderView, QSizePolicy)
from PyQt5.QtCore import pyqtSignal, Qt


class OrdenesWidget(QWidget):
    # Señales
    add_order_requested = pyqtSignal()
    delete_order_requested = pyqtSignal(int)
    move_up_requested = pyqtSignal(int)
    move_down_requested = pyqtSignal(int)
    selection_changed = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)
        
        # Tabla de órdenes (SIN columna visible de ID)
        self.order_table = QTableWidget()
        self.order_table.setColumnCount(3)
        self.order_table.setHorizontalHeaderLabels(["Origen", "Destino", "Pallet"])
        self.order_table.setAlternatingRowColors(True)
        self.order_table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 3px;
                font-size: 11px;
                gridline-color: #333;
                min-height: 150px;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QTableWidget::item:selected {
                background-color: #1a73e8;
                color: white;
            }
            QTableWidget QTableWidgetItem:alternate {
                background-color: #2b2b2b;
                color: #e0e0e0;
            }
            QTableWidget QTableWidgetItem {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
        """)
        self.order_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.order_table.setSelectionMode(QAbstractItemView.SingleSelection)
        
        header = self.order_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #2b2b2b;
                color: #e0e0e0;
                padding: 4px;
                border: none;
                border-right: 1px solid #444;
                border-bottom: 1px solid #444;
                font-size: 10px;
                font-weight: bold;
            }
        """)
        
        self.order_table.verticalHeader().setDefaultSectionSize(30)
        self.order_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        layout.addWidget(self.order_table)
        
        # Botones
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.up_button = QPushButton("▲ Subir")
        self.down_button = QPushButton("▼ Bajar")
        self.delete_button = QPushButton("✕ Eliminar")
        
        button_style = """
            QPushButton {
                background-color: #2b2b2b;
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 11px;
                min-width: 80px;
                font-weight: bold;
            }
            QPushButton:hover:enabled {
                background-color: #3a3a3a;
                border-color: #555;
            }
            QPushButton:pressed:enabled {
                background-color: #1a73e8;
                border-color: #1a73e8;
            }
            QPushButton:disabled {
                background-color: #1e1e1e;
                color: #666;
                border-color: #333;
            }
        """
        
        for button in [self.up_button, self.down_button, self.delete_button]:
            button.setEnabled(False)
            button.setStyleSheet(button_style)
            button_layout.addWidget(button)
        
        layout.addLayout(button_layout)
        
        # Conectar señales
        self.delete_button.clicked.connect(self.on_delete_clicked)
        self.up_button.clicked.connect(self.on_up_clicked)
        self.down_button.clicked.connect(self.on_down_clicked)
        self.order_table.itemSelectionChanged.connect(self.on_selection_changed)
    
    # ----------------- Handlers de botones -----------------
    def _get_selected_order_id(self):
        """Obtener el ID de la orden seleccionada (guardado en UserRole de la columna 0)."""
        current_row = self.order_table.currentRow()
        if current_row < 0:
            return None
        origen_item = self.order_table.item(current_row, 0)
        if origen_item:
            return origen_item.data(Qt.UserRole)
        return None

    def on_delete_clicked(self):
        order_id = self._get_selected_order_id()
        if order_id is not None:
            self.delete_order_requested.emit(order_id)
    
    def on_up_clicked(self):
        order_id = self._get_selected_order_id()
        if order_id is not None:
            self.move_up_requested.emit(order_id)
    
    def on_down_clicked(self):
        order_id = self._get_selected_order_id()
        if order_id is not None:
            self.move_down_requested.emit(order_id)
    
    def on_selection_changed(self):
        has_selection = self.order_table.currentRow() >= 0
        self.up_button.setEnabled(has_selection)
        self.down_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        
        if has_selection:
            order_id = self._get_selected_order_id()
            if order_id is not None:
                self.selection_changed.emit(order_id)
    
    # ----------------- API pública -----------------
    def clear_orders(self):
        self.order_table.setRowCount(0)
    
    def add_order_item(self, order_id: int, origen: int, destino: int, pallet_id: int = None):
        """Añadir una orden a la tabla (ID solo en UserRole)."""
        row = self.order_table.rowCount()
        self.order_table.insertRow(row)
        
        # Origen (aquí guardamos el ID en UserRole)
        origen_item = QTableWidgetItem(str(origen))
        origen_item.setData(Qt.UserRole, order_id)
        origen_item.setFlags(origen_item.flags() & ~Qt.ItemIsEditable)
        self.order_table.setItem(row, 0, origen_item)
        
        # Destino
        destino_item = QTableWidgetItem(str(destino))
        destino_item.setFlags(destino_item.flags() & ~Qt.ItemIsEditable)
        self.order_table.setItem(row, 1, destino_item)
        
        # Pallet
        pallet_text = str(pallet_id) if pallet_id else "N/A"
        pallet_item = QTableWidgetItem(pallet_text)
        pallet_item.setFlags(pallet_item.flags() & ~Qt.ItemIsEditable)
        self.order_table.setItem(row, 2, pallet_item)
    
    def remove_order_item(self, order_id: int):
        """Remover una orden por ID (buscando en UserRole de la columna 0)."""
        for row in range(self.order_table.rowCount()):
            origen_item = self.order_table.item(row, 0)
            if origen_item and origen_item.data(Qt.UserRole) == order_id:
                self.order_table.removeRow(row)
                break
    
    def update_order_item(self, order_id: int, origen: int, destino: int, pallet_id: int = None):
        """Actualizar una orden existente."""
        for row in range(self.order_table.rowCount()):
            origen_item = self.order_table.item(row, 0)
            if origen_item and origen_item.data(Qt.UserRole) == order_id:
                # Origen
                origen_item.setText(str(origen))
                
                # Destino
                destino_item = QTableWidgetItem(str(destino))
                destino_item.setFlags(destino_item.flags() & ~Qt.ItemIsEditable)
                self.order_table.setItem(row, 1, destino_item)
                
                # Pallet
                pallet_text = str(pallet_id) if pallet_id else "N/A"
                pallet_item = QTableWidgetItem(pallet_text)
                pallet_item.setFlags(pallet_item.flags() & ~Qt.ItemIsEditable)
                self.order_table.setItem(row, 2, pallet_item)
                break
    
    def refresh_table(self):
        self.order_table.viewport().update()
