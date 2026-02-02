from PyQt5.QtWidgets import QScrollArea, QFrame, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsRectItem, QGraphicsPixmapItem, QFileDialog, QTableWidgetItem, QMessageBox, QHeaderView, QPushButton, QSizePolicy, QSplitter, QVBoxLayout, QHBoxLayout, QFrame
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QSize
from PyQt5.QtGui import QPixmap, QBrush, QColor, QPen, QPainter, QWheelEvent, QCursor
import math


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
        
        # Guardar el punto de la escena bajo el cursor del mouse
        old_pos = self.mapToScene(event.pos())
        
        # Zoom
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
            self._zoom += 1
        else:
            zoom_factor = zoom_out_factor
            self._zoom -= 1
        
        # Limitar zoom
        if self._zoom > 10:
            self._zoom = 10
            return
        elif self._zoom < -5:
            self._zoom = -5
            return
            
        self.scale(zoom_factor, zoom_factor)
        
        # Obtener el nuevo punto
        new_pos = self.mapToScene(event.pos())
        
        # Mover la escena para mantener el punto bajo el cursor
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())

class MainWindow(QMainWindow):
    # Señales
    salir_app = pyqtSignal()
    pallet_seleccionado = pyqtSignal(int)
    propiedades_actualizadas = pyqtSignal(dict)
    imagen_cargada = pyqtSignal(str)
    add_to_orders_clicked = pyqtSignal()  # Nueva señal para añadir a órdenes
    
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # Configurar la vista gráfica personalizada
        self.graphics_view = GraphicsView(self.ui.scrollAreaWidgetContentsWork)
        self.ui.workLayout.replaceWidget(self.ui.marco_trabajo, self.graphics_view)
        self.ui.marco_trabajo.deleteLater()
        
        # Crear escena gráfica
        self.scene = QGraphicsScene()
        self.graphics_view.setScene(self.scene)
        
        # Imagen de fondo
        self.background_item = None
        self.has_image = False
        
        # Conectar menú - solo Abrir y Salir
        self.ui.actionAbrir.triggered.connect(self.on_abrir)
        self.ui.actionSalir.triggered.connect(self.on_salir)
        
        # Configurar tabla de propiedades
        self.setup_propiedades_table()
        
        # Pallets en la escena (ID -> [rect_horizontal, rect_vertical])
        self.pallet_items = {}
        
        # Configurar tamaños de splitters para mejor distribución
        self.setup_splitter_layout()
        
        # Configurar el display de I/O desde el inicio (pero con valores en 0)
        self.setup_io_display()
        
        # Asegurar que el grupo de I/O esté visible desde el inicio
        self.ui.groupIO.setVisible(True)
        
        # Configurar tamaños mínimos y máximos para paneles
        self.setup_panel_sizes()

        
        # Variable para almacenar el pallet seleccionado actualmente
        self.current_pallet_id = None
        
        # Inicializar botón de añadir a órdenes
        self.add_to_orders_button = None
        
        # Conectar el cambio de tamaño de ventana
        self.resizeEvent = self.on_resize
    
    def setup_splitter_layout(self):
        """Configurar el splitter principal para mejor distribución del espacio"""
        # Configurar proporciones iniciales (70% área trabajo, 30% panel lateral)
        self.ui.splitter.setSizes([700, 300])
        
        # Configurar tamaños mínimos
        self.ui.splitter.setMinimumSize(800, 600)
        
        # Hacer que el área de trabajo sea el que se expanda más
        self.ui.splitter.setStretchFactor(0, 3)  # Área trabajo tiene factor de estiramiento 3
        self.ui.splitter.setStretchFactor(1, 1)  # Panel lateral tiene factor de estiramiento 1
        
        # Configurar que se puedan colapsar paneles
        self.ui.splitter.setChildrenCollapsible(False)
    
    def setup_panel_sizes(self):
        """Configurar tamaños mínimos y máximos para los paneles laterales"""
        # Grupo de órdenes - oculto inicialmente, tamaño adaptable
        self.ui.groupOrdenes.setMinimumHeight(150)
        self.ui.groupOrdenes.setMaximumHeight(400)
        
        # Grupo de I/O - tamaño fijo
        self.ui.groupIO.setMinimumHeight(180)
        self.ui.groupIO.setMaximumHeight(220)
        
        # Grupo de propiedades - tamaño adaptable
        self.ui.groupPropiedadesPallet.setMinimumHeight(200)
        self.ui.groupPropiedadesPallet.setMaximumHeight(350)
        
        # Establecer políticas de tamaño para los widgets dentro del panel lateral
        self.ui.groupOrdenes.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.ui.groupIO.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.ui.groupPropiedadesPallet.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        
        # Configurar scroll areas para contenido largo
        self.ui.ordenesLayout.setAlignment(Qt.AlignTop)
        self.ui.ioLayout.setAlignment(Qt.AlignTop)
        self.ui.propiedadesLayout.setAlignment(Qt.AlignTop)
    
    def on_resize(self, event):
        """Manejador para cuando cambia el tamaño de la ventana"""
        # Mantener proporciones razonables al redimensionar
        current_width = self.width()
        if current_width > 0:
            # Mantener relación aproximadamente 70/30
            work_width = int(current_width * 0.7)
            panel_width = int(current_width * 0.3)
            self.ui.splitter.setSizes([work_width, panel_width])
        
        super().resizeEvent(event)
    

    def setup_io_display(self):
        """Configurar la visualización de entradas/salidas con scroll vertical"""
        # Limpiar el layout existente en groupIO
        while self.ui.ioLayout.count():
            item = self.ui.ioLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Crear y añadir el widget de I/O
        from Controller.IOController import IOController
        self.io_controller = IOController()
        io_widget = self.io_controller.get_widget()
        
        # Crear un scroll area que envuelva al widget de I/O
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        
        scroll.setWidget(io_widget)
        
        # Añadir el scroll al layout del panel IO
        self.ui.ioLayout.addWidget(scroll)

    
    def mostrar_panel_ordenes(self):
        """Mostrar el panel de órdenes después de cargar un mapa"""
        self.ui.groupOrdenes.setVisible(True)
        
        # Ajustar dinámicamente los tamaños cuando se muestra el panel de órdenes
        if self.has_image:
            # Redistribuir espacio entre los paneles laterales
            total_panel_height = self.ui.sidePanel.height()
            if total_panel_height > 600:
                # Si hay mucho espacio, distribuir proporcionalmente
                self.ui.groupOrdenes.setMinimumHeight(int(total_panel_height * 0.4))
                self.ui.groupIO.setMinimumHeight(int(total_panel_height * 0.2))
                self.ui.groupPropiedadesPallet.setMinimumHeight(int(total_panel_height * 0.4))
    
    def setup_propiedades_table(self):
        """Configurar la tabla de propiedades con las columnas necesarias"""
        # Solo mostrar propiedades editables, sin coordenadas X, Y
        propiedades = [
            ("ID", "int"),
            ("Largo", "float"),
            ("Ancho", "float"),
            ("Posicion", "float"),
            ("Alto", "float"),
            ("Calidad", "str"),
            ("Peso", "float"),
            ("Prioridad", "int"),
            ("Visibilidad", "bool")
        ]
        
        self.ui.propiedadesTable.setRowCount(len(propiedades))
        
        # Configurar el ancho de las columnas
        self.ui.propiedadesTable.horizontalHeader().setStretchLastSection(True)
        self.ui.propiedadesTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.ui.propiedadesTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        # Configurar altura de filas
        self.ui.propiedadesTable.verticalHeader().setDefaultSectionSize(30)
        
        for row, (propiedad, tipo) in enumerate(propiedades):
            item = QTableWidgetItem(propiedad)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.ui.propiedadesTable.setItem(row, 0, item)
            
            value_item = QTableWidgetItem()
            self.ui.propiedadesTable.setItem(row, 1, value_item)
    
    def cargar_imagen_fondo(self, image_path: str):
        """Cargar una imagen como fondo del área de trabajo"""
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
        """Dibujar un pallet en la escena - TAMAÑO FIJO"""
        # Solo dibujar si hay imagen cargada
        if not self.has_image:
            return
            
        pallet_id = pallet_data["ID"]
        x = pallet_data["X"]
        y = pallet_data["Y"]
        visibilidad = bool(pallet_data["Visibilidad"])
        
        # Tamaños fijos para todos los pallets
        ANCHO_PRINCIPAL = 60  # Rectángulo horizontal más ancho
        ALTO_PRINCIPAL = 30
        ANCHO_SECUNDARIO = 20  # Rectángulo vertical más delgado
        ALTO_SECUNDARIO = 40
        
        # Definir colores según visibilidad
        if visibilidad:
            color_principal = QColor(0, 51, 102)  # Azul oscuro
            color_secundario = QColor(120, 60, 20)  # Marrón claro
        else:
            color_principal = QColor(128, 128, 128)  # Gris
            color_secundario = QColor(128, 128, 128)  # Gris
        
        # Crear un lápiz (pen) negro para los bordes
        pen_negro = QPen(Qt.black, 1)
        
        # Rectángulo horizontal (principal) - más ancho
        rect_horizontal = QGraphicsRectItem(0, 0, ANCHO_PRINCIPAL, ALTO_PRINCIPAL)
        rect_horizontal.setPos(x - ANCHO_PRINCIPAL/2, y - ALTO_PRINCIPAL/2)
        rect_horizontal.setBrush(QBrush(color_principal))
        rect_horizontal.setPen(pen_negro)  # Borde negro
        rect_horizontal.setData(0, pallet_id)  # Almacenar ID
        rect_horizontal.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
        rect_horizontal.setCursor(QCursor(Qt.PointingHandCursor))  # Cursor de mano
        
        # Rectángulo vertical (secundario) - más delgado
        rect_vertical = QGraphicsRectItem(0, 0, ANCHO_SECUNDARIO, ALTO_SECUNDARIO)
        rect_vertical.setPos(x - ANCHO_SECUNDARIO/2, y - ALTO_SECUNDARIO/2)
        rect_vertical.setBrush(QBrush(color_secundario))
        rect_vertical.setPen(pen_negro)  # Borde negro
        rect_vertical.setData(0, pallet_id)
        rect_vertical.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
        rect_vertical.setCursor(QCursor(Qt.PointingHandCursor))  # Cursor de mano
        
        # Añadir tooltip para mejor UX
        tooltip_text = f"Pallet ID: {pallet_id}\nCalidad: {pallet_data.get('Calidad', 'N/A')}\nVisibilidad: {'Sí' if visibilidad else 'No'}"
        rect_horizontal.setToolTip(tooltip_text)
        rect_vertical.setToolTip(tooltip_text)
        
        # Añadir a la escena
        self.scene.addItem(rect_horizontal)
        self.scene.addItem(rect_vertical)
        
        # Almacenar referencias
        self.pallet_items[pallet_id] = [rect_horizontal, rect_vertical]
        
        # Conectar señal de selección
        rect_horizontal.mousePressEvent = lambda event, pid=pallet_id: self.on_pallet_clicked(event, pid)
        rect_vertical.mousePressEvent = lambda event, pid=pallet_id: self.on_pallet_clicked(event, pid)
        
        # Conectar eventos de hover para cambiar cursor y mantener borde negro
        rect_horizontal.hoverEnterEvent = lambda event, pid=pallet_id: self.on_pallet_hover_enter(event, pid)
        rect_horizontal.hoverLeaveEvent = lambda event, pid=pallet_id: self.on_pallet_hover_leave(event, pid)
        rect_vertical.hoverEnterEvent = lambda event, pid=pallet_id: self.on_pallet_hover_enter(event, pid)
        rect_vertical.hoverLeaveEvent = lambda event, pid=pallet_id: self.on_pallet_hover_leave(event, pid)
        
        # Habilitar eventos hover
        rect_horizontal.setAcceptHoverEvents(True)
        rect_vertical.setAcceptHoverEvents(True)
    
    def on_pallet_hover_enter(self, event, pallet_id):
        """Manejador cuando el ratón entra en un pallet"""
        # Solo cambiar el cursor, mantener borde negro
        # No cambiar el color del borde, mantenerlo negro
        event.accept()
    
    def on_pallet_hover_leave(self, event, pallet_id):
        """Manejador cuando el ratón sale de un pallet"""
        # El borde ya es negro, no hay que hacer nada
        event.accept()
    
    def on_pallet_clicked(self, event, pallet_id):
        """Manejador de clic en pallet"""
        # Deseleccionar todos los pallets primero
        for pid, items in self.pallet_items.items():
            for item in items:
                item.setSelected(False)
                # Asegurar que el borde sigue siendo negro incluso después de deseleccionar
                item.setPen(QPen(Qt.black, 1))
        
        # Seleccionar el pallet clicado
        if pallet_id in self.pallet_items:
            for item in self.pallet_items[pallet_id]:
                item.setSelected(True)
                # Mantener borde negro incluso cuando está seleccionado
                item.setPen(QPen(Qt.black, 1))
        
        self.pallet_seleccionado.emit(pallet_id)
        self.current_pallet_id = pallet_id
        event.accept()
    
    def mostrar_propiedades_pallet(self, pallet_data: dict):
        """Mostrar las propiedades de un pallet en la tabla"""
        # Desconectar señal temporalmente para evitar bucles
        try:
            self.ui.propiedadesTable.itemChanged.disconnect()
        except:
            pass
        
        # Solo mostrar las propiedades editables (sin X, Y)
        propiedades_mostrar = {
            "ID": str(pallet_data.get("ID", "")),
            "Largo": str(pallet_data.get("Largo", "")),
            "Ancho": str(pallet_data.get("Ancho", "")),
            "Posicion": str(pallet_data.get("Posicion", "")),
            "Alto": str(pallet_data.get("Alto", "")),
            "Calidad": str(pallet_data.get("Calidad", "")),
            "Peso": str(pallet_data.get("Peso", "")),
            "Prioridad": str(pallet_data.get("Prioridad", "")),
            "Visibilidad": str(pallet_data.get("Visibilidad", ""))
        }
        
        for row in range(self.ui.propiedadesTable.rowCount()):
            propiedad = self.ui.propiedadesTable.item(row, 0).text()
            if propiedad in propiedades_mostrar:
                valor = propiedades_mostrar[propiedad]
                item = QTableWidgetItem(valor)
                
                # Hacer que todas las propiedades sean editables excepto ID y Posicion
                if propiedad not in ["ID", "Posicion"]:
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    
                self.ui.propiedadesTable.setItem(row, 1, item)
        
        # Añadir botón para añadir a órdenes al final de la tabla
        # Primero verificamos si ya existe el botón
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
        
        # Habilitar el botón si hay un pallet seleccionado
        self.add_to_orders_button.setEnabled(True)
        
        # Reconectar señal
        self.ui.propiedadesTable.itemChanged.connect(self.on_propiedades_changed)
    
    def on_propiedades_changed(self, item: QTableWidgetItem):
        """Cuando se edita una propiedad en la tabla"""
        if item.column() == 1:  # Solo en columna de valores
            row = item.row()
            propiedad = self.ui.propiedadesTable.item(row, 0).text()
            valor = item.text()
            
            # Verificar que no sea la propiedad ID o Posicion (no editables)
            if propiedad in ["ID", "Posicion"]:
                return
            
            # Convertir al tipo correcto
            try:
                if propiedad in ["Largo", "Ancho", "Alto", "Peso"]:
                    valor = float(valor)
                elif propiedad == "Prioridad":
                    valor = int(valor)
                elif propiedad == "Visibilidad":
                    # Aceptar diferentes formatos de visibilidad
                    if valor.lower() in ["1", "true", "verdadero", "sí", "si"]:
                        valor = 1
                    elif valor.lower() in ["0", "false", "falso", "no"]:
                        valor = 0
                    else:
                        valor = int(float(valor))
                # Calidad se mantiene como string
            except ValueError:
                QMessageBox.warning(self, "Error", f"Valor inválido para {propiedad}")
                return
            
            # Emitir señal de actualización
            self.propiedades_actualizadas.emit({propiedad: valor})
    
   
    def limpiar_escena(self):
        """Limpiar todos los items de la escena"""
        self.scene.clear()
        self.pallet_items.clear()
        self.background_item = None
        self.has_image = False
        self.current_pallet_id = None
        
        # Limpiar tabla de propiedades
        for row in range(self.ui.propiedadesTable.rowCount()):
            self.ui.propiedadesTable.setItem(row, 1, QTableWidgetItem(""))
        
        # Deshabilitar botón de añadir a órdenes
        if self.add_to_orders_button:
            self.add_to_orders_button.setEnabled(False)
        
        # NOTA: Ahora también deberíamos limpiar las órdenes,
        # pero esto se manejará desde MainController
        
        # Restaurar tamaño mínimo del panel de órdenes
        self.ui.groupOrdenes.setMinimumHeight(150)
        
        # Detener el monitoreo de I/O cuando no hay imagen
        if hasattr(self, 'io_controller'):
            self.io_controller.stop_monitoring()
            
            # Resetear los puntos de I/O a 0 (rojos)
            self.io_controller.reset_display()
    
    def actualizar_pallet_visual(self, pallet_id: int, pallet_data: dict):
        """Actualizar visualmente un pallet después de cambiar sus propiedades"""
        # Eliminar pallet actual
        if pallet_id in self.pallet_items:
            for item in self.pallet_items[pallet_id]:
                if item.scene():
                    self.scene.removeItem(item)
            del self.pallet_items[pallet_id]
        
        # Redibujar pallet con nuevas propiedades
        if self.has_image:
            self.dibujar_pallet(pallet_data)
    
    # Handlers de menú
    def on_abrir(self):
        """Abrir diálogo para cargar imagen de mapa"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar imagen de mapa", "", "Imágenes (*.png *.jpg *.bmp)"
        )
        if file_path:
            self.imagen_cargada.emit(file_path)
    
    def on_salir(self):
        self.salir_app.emit()