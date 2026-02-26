from PyQt5.QtWidgets import QScrollArea, QFrame, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsRectItem, QGraphicsPixmapItem, QFileDialog, QTableWidgetItem, QMessageBox, QHeaderView, QPushButton, QSizePolicy, QSplitter
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QBrush, QColor, QPen, QPainter, QWheelEvent, QCursor
from View.ui_mainwindow import Ui_MainWindow

class GraphicsView(QGraphicsView):
    """QGraphicsView personalizado para manejar zoom y desplazamiento"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self._zoom = 0
        
    def wheelEvent(self, event: QWheelEvent):
        """Manejar zoom con la rueda del ratón"""
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor
        
        old_pos = self.mapToScene(event.pos())
        
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
            self._zoom += 1
        else:
            zoom_factor = zoom_out_factor
            self._zoom -= 1
        
        if self._zoom > 10:
            self._zoom = 10
            return
        elif self._zoom < -5:
            self._zoom = -5
            return
            
        self.scale(zoom_factor, zoom_factor)
        
        new_pos = self.mapToScene(event.pos())
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())

class MainWindow(QMainWindow):
    # Señales
    salir_app = pyqtSignal()
    pallet_seleccionado = pyqtSignal(str)
    propiedades_actualizadas = pyqtSignal(dict)
    imagen_cargada = pyqtSignal(str)
    add_to_orders_clicked = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.escala = 0.05
        
        self.graphics_view = GraphicsView(self.ui.scrollAreaWidgetContentsWork)
        self.ui.workLayout.replaceWidget(self.ui.marco_trabajo, self.graphics_view)
        self.ui.marco_trabajo.deleteLater()
        
        self.scene = QGraphicsScene()
        self.graphics_view.setScene(self.scene)
        
        self.background_item = None
        self.has_image = False
        
        self.ui.actionAbrir.triggered.connect(self.on_abrir)
        self.ui.actionSalir.triggered.connect(self.on_salir)
        
        self.setup_propiedades_table()
        
        self.pallet_items = {}
        
        self.setup_splitter_layout()
        self.setup_io_display()
        self.ui.groupIO.setVisible(True)
        self.setup_panel_sizes()
        
        self.current_pallet_id = None
        self.add_to_orders_button = None
        
        self.resizeEvent = self.on_resize
    
    def setup_splitter_layout(self):
        self.ui.splitter.setSizes([700, 300])
        self.ui.splitter.setMinimumSize(800, 600)
        self.ui.splitter.setStretchFactor(0, 3)
        self.ui.splitter.setStretchFactor(1, 1)
        self.ui.splitter.setChildrenCollapsible(False)
    
    def setup_panel_sizes(self):
        self.ui.groupOrdenes.setMinimumHeight(150)
        self.ui.groupOrdenes.setMaximumHeight(400)
        self.ui.groupIO.setMinimumHeight(180)
        self.ui.groupIO.setMaximumHeight(220)
        self.ui.groupPropiedadesPallet.setMinimumHeight(200)
        self.ui.groupPropiedadesPallet.setMaximumHeight(350)
        
        self.ui.groupOrdenes.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.ui.groupIO.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.ui.groupPropiedadesPallet.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        
        self.ui.ordenesLayout.setAlignment(Qt.AlignTop)
        self.ui.ioLayout.setAlignment(Qt.AlignTop)
        self.ui.propiedadesLayout.setAlignment(Qt.AlignTop)
    
    def on_resize(self, event):
        current_width = self.width()
        if current_width > 0:
            work_width = int(current_width * 0.7)
            panel_width = int(current_width * 0.3)
            self.ui.splitter.setSizes([work_width, panel_width])
        super().resizeEvent(event)
    
    def setup_io_display(self):
        while self.ui.ioLayout.count():
            item = self.ui.ioLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        from Controller.IOController import IOController
        self.io_controller = IOController()
        io_widget = self.io_controller.get_widget()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(io_widget)
        
        self.ui.ioLayout.addWidget(scroll)
    
    def mostrar_panel_ordenes(self):
        self.ui.groupOrdenes.setVisible(True)
        if self.has_image:
            total_panel_height = self.ui.sidePanel.height()
            if total_panel_height > 600:
                self.ui.groupOrdenes.setMinimumHeight(int(total_panel_height * 0.4))
                self.ui.groupIO.setMinimumHeight(int(total_panel_height * 0.2))
                self.ui.groupPropiedadesPallet.setMinimumHeight(int(total_panel_height * 0.4))
    
    def setup_propiedades_table(self):
        propiedades = [
            ("ID", "str"),
            ("Largo", "float"),
            ("Ancho", "float"),
            ("Posicion", "float"),
            ("Alto", "float"),
            ("Calidad", "str"),
            ("Peso", "float"),
            ("Prioridad", "int"),
            ("Ocupado", "bool")
        ]
        
        self.ui.propiedadesTable.setRowCount(len(propiedades))
        self.ui.propiedadesTable.horizontalHeader().setStretchLastSection(True)
        self.ui.propiedadesTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.ui.propiedadesTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.ui.propiedadesTable.verticalHeader().setDefaultSectionSize(30)
        
        for row, (propiedad, tipo) in enumerate(propiedades):
            item = QTableWidgetItem(propiedad)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.ui.propiedadesTable.setItem(row, 0, item)
            value_item = QTableWidgetItem()
            self.ui.propiedadesTable.setItem(row, 1, value_item)
    
    def cargar_imagen_fondo(self, image_path: str):
        if self.background_item:
            self.scene.removeItem(self.background_item)
        
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            QMessageBox.warning(self, "Error", "No se pudo cargar la imagen")
            return False
        
        self.background_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.background_item)
        self.scene.setSceneRect(self.background_item.boundingRect())
        self.graphics_view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        self.has_image = True
        return True
    
    def dibujar_pallet(self, pallet_data: dict):
        if not self.has_image:
            return
        
        pallet_id = pallet_data["ID"]
        x_metro = pallet_data["X"]
        y_metro = pallet_data["Y"]
        x = x_metro / self.escala
        y = y_metro / self.escala
        ocupado = bool(pallet_data["Ocupado"])
        
        ANCHO_PRINCIPAL = 60
        ALTO_PRINCIPAL = 30
        ANCHO_SECUNDARIO = 20
        ALTO_SECUNDARIO = 40
        
        # --- CAMBIO: Invertir colores según estado ocupado ---
        if ocupado:
            # Ocupado: gris
            color_principal = QColor(128, 128, 128)
            color_secundario = QColor(128, 128, 128)
        else:
            # Libre: colores normales
            color_principal = QColor(0, 51, 102)    # Azul oscuro
            color_secundario = QColor(120, 60, 20)  # Marrón claro
        # ----------------------------------------------------
        
        pen_negro = QPen(Qt.black, 1)
        
        rect_horizontal = QGraphicsRectItem(0, 0, ANCHO_PRINCIPAL, ALTO_PRINCIPAL)
        rect_horizontal.setPos(x - ANCHO_PRINCIPAL/2, y - ALTO_PRINCIPAL/2)
        rect_horizontal.setBrush(QBrush(color_principal))
        rect_horizontal.setPen(pen_negro)
        rect_horizontal.setData(0, pallet_id)
        rect_horizontal.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
        rect_horizontal.setCursor(QCursor(Qt.PointingHandCursor))
        
        rect_vertical = QGraphicsRectItem(0, 0, ANCHO_SECUNDARIO, ALTO_SECUNDARIO)
        rect_vertical.setPos(x - ANCHO_SECUNDARIO/2, y - ALTO_SECUNDARIO/2)
        rect_vertical.setBrush(QBrush(color_secundario))
        rect_vertical.setPen(pen_negro)
        rect_vertical.setData(0, pallet_id)
        rect_vertical.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
        rect_vertical.setCursor(QCursor(Qt.PointingHandCursor))
        
        tooltip_text = f"Pallet ID: {pallet_id}\nCalidad: {pallet_data.get('Calidad', 'N/A')}\nOcupado: {'Sí' if ocupado else 'No'}"
        rect_horizontal.setToolTip(tooltip_text)
        rect_vertical.setToolTip(tooltip_text)
        
        self.scene.addItem(rect_horizontal)
        self.scene.addItem(rect_vertical)
        
        self.pallet_items[pallet_id] = [rect_horizontal, rect_vertical]
        
        rect_horizontal.mousePressEvent = lambda event, pid=pallet_id: self.on_pallet_clicked(event, pid)
        rect_vertical.mousePressEvent = lambda event, pid=pallet_id: self.on_pallet_clicked(event, pid)
        
        rect_horizontal.hoverEnterEvent = lambda event, pid=pallet_id: self.on_pallet_hover_enter(event, pid)
        rect_horizontal.hoverLeaveEvent = lambda event, pid=pallet_id: self.on_pallet_hover_leave(event, pid)
        rect_vertical.hoverEnterEvent = lambda event, pid=pallet_id: self.on_pallet_hover_enter(event, pid)
        rect_vertical.hoverLeaveEvent = lambda event, pid=pallet_id: self.on_pallet_hover_leave(event, pid)
        
        rect_horizontal.setAcceptHoverEvents(True)
        rect_vertical.setAcceptHoverEvents(True)
    
    def on_pallet_hover_enter(self, event, pallet_id):
        event.accept()
    
    def on_pallet_hover_leave(self, event, pallet_id):
        event.accept()
    
    def on_pallet_clicked(self, event, pallet_id):
        for pid, items in self.pallet_items.items():
            for item in items:
                item.setSelected(False)
                item.setPen(QPen(Qt.black, 1))
        
        if pallet_id in self.pallet_items:
            for item in self.pallet_items[pallet_id]:
                item.setSelected(True)
                item.setPen(QPen(Qt.black, 1))
        
        self.pallet_seleccionado.emit(pallet_id)
        self.current_pallet_id = pallet_id
        event.accept()
    
    def mostrar_propiedades_pallet(self, pallet_data: dict):
        try:
            self.ui.propiedadesTable.itemChanged.disconnect()
        except:
            pass
        
        propiedades_mostrar = {
            "ID": pallet_data.get("ID", ""),
            "Largo": str(pallet_data.get("Largo", "")),
            "Ancho": str(pallet_data.get("Ancho", "")),
            "Posicion": str(pallet_data.get("Posicion", "")),
            "Alto": str(pallet_data.get("Alto", "")),
            "Calidad": str(pallet_data.get("Calidad", "")),
            "Peso": str(pallet_data.get("Peso", "")),
            "Prioridad": str(pallet_data.get("Prioridad", "")),
            "Ocupado": str(pallet_data.get("Ocupado", ""))
        }
        
        for row in range(self.ui.propiedadesTable.rowCount()):
            propiedad = self.ui.propiedadesTable.item(row, 0).text()
            if propiedad in propiedades_mostrar:
                valor = propiedades_mostrar[propiedad]
                item = QTableWidgetItem(valor)
                if propiedad not in ["ID", "Posicion"]:
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.ui.propiedadesTable.setItem(row, 1, item)
        
        if not self.add_to_orders_button:
            self.add_to_orders_button = QPushButton("Añadir a la lista de órdenes")
            self.add_to_orders_button.setStyleSheet("""
                QPushButton {
                    background-color: #2b2b2b;
                    color: #e0e0e0;
                    border: 1px solid #444;
                    border-radius: 4px;
                    padding: 10px;
                    font-weight: bold;
                    font-size: 11px;
                    margin-top: 15px;
                    min-height: 35px;
                }
                QPushButton:hover {
                    background-color: #3a3a3a;
                    border-color: #555;
                }
                QPushButton:pressed {
                    background-color: #1a73e8;
                    border-color: #1a73e8;
                }
                QPushButton:disabled {
                    background-color: #1e1e1e;
                    color: #666;
                    border-color: #333;
                }
            """)
            self.add_to_orders_button.clicked.connect(self.add_to_orders_clicked.emit)
            self.ui.propiedadesLayout.addWidget(self.add_to_orders_button)
        
        self.add_to_orders_button.setEnabled(True)
        self.ui.propiedadesTable.itemChanged.connect(self.on_propiedades_changed)
    
    def on_propiedades_changed(self, item: QTableWidgetItem):
        if item.column() == 1:
            row = item.row()
            propiedad = self.ui.propiedadesTable.item(row, 0).text()
            valor = item.text()
            
            if propiedad in ["ID", "Posicion"]:
                return
            
            try:
                if propiedad in ["Largo", "Ancho", "Alto", "Peso"]:
                    valor = float(valor)
                elif propiedad == "Prioridad":
                    valor = int(valor)
                elif propiedad == "Ocupado":
                    if valor.lower() in ["1", "true", "verdadero", "sí", "si"]:
                        valor = 1
                    elif valor.lower() in ["0", "false", "falso", "no"]:
                        valor = 0
                    else:
                        valor = int(float(valor))
            except ValueError:
                QMessageBox.warning(self, "Error", f"Valor inválido para {propiedad}")
                return
            
            self.propiedades_actualizadas.emit({propiedad: valor})
    
    def limpiar_escena(self):
        self.scene.clear()
        self.pallet_items.clear()
        self.background_item = None
        self.has_image = False
        self.current_pallet_id = None
        
        for row in range(self.ui.propiedadesTable.rowCount()):
            self.ui.propiedadesTable.setItem(row, 1, QTableWidgetItem(""))
        
        if self.add_to_orders_button:
            self.add_to_orders_button.setEnabled(False)
        
        self.ui.groupOrdenes.setMinimumHeight(150)
        
        if hasattr(self, 'io_controller'):
            self.io_controller.stop_monitoring()
            self.io_controller.reset_display()
    
    def actualizar_pallet_visual(self, pallet_id: str, pallet_data: dict):
        if pallet_id in self.pallet_items:
            for item in self.pallet_items[pallet_id]:
                if item.scene():
                    self.scene.removeItem(item)
            del self.pallet_items[pallet_id]
        
        if self.has_image:
            self.dibujar_pallet(pallet_data)
    
    def on_abrir(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar imagen de mapa", "", "Imágenes (*.png *.jpg *.bmp)"
        )
        if file_path:
            self.imagen_cargada.emit(file_path)
    
    def on_salir(self):
        self.salir_app.emit()