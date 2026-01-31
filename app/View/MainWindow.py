from PyQt5.QtWidgets import QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsRectItem, QGraphicsPixmapItem, QFileDialog, QTableWidgetItem, QMessageBox, QHeaderView
from PyQt5.QtCore import Qt, pyqtSignal, QPointF
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
        
        # Ajustar el tamaño del panel lateral
        self.ui.splitter.setSizes([800, 400])  # Más espacio para el área de trabajo
        
        # Configurar el display de I/O desde el inicio (pero con valores en 0)
        self.setup_io_display()
        
        # Asegurar que el grupo de I/O esté visible desde el inicio
        self.ui.groupIO.setVisible(True)
    
    def setup_io_display(self):
        """Configurar la visualización de entradas/salidas"""
        # Limpiar el layout existente en groupIO
        while self.ui.ioLayout.count():
            item = self.ui.ioLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Crear y añadir el widget de I/O
        from Controller.IOController import IOController
        self.io_controller = IOController()
        io_widget = self.io_controller.get_widget()
        self.ui.ioLayout.addWidget(io_widget)
        
        # Inicialmente mostrar todos los puntos en 0 (rojos)
        # No iniciar el monitoreo automático hasta que se cargue una imagen
        # El widget ya se inicializa con todos los puntos en rojo (estado False)
    
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
                
                # Hacer que todas las propiedades sean editables excepto ID
                if propiedad != "ID":
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    
                self.ui.propiedadesTable.setItem(row, 1, item)
        
        # Reconectar señal
        self.ui.propiedadesTable.itemChanged.connect(self.on_propiedades_changed)
    
    def on_propiedades_changed(self, item: QTableWidgetItem):
        """Cuando se edita una propiedad en la tabla"""
        if item.column() == 1:  # Solo en columna de valores
            row = item.row()
            propiedad = self.ui.propiedadesTable.item(row, 0).text()
            valor = item.text()
            
            # Verificar que no sea la propiedad ID (no editable)
            if propiedad == "ID":
                return
            
            # Convertir al tipo correcto
            try:
                if propiedad in ["Largo", "Ancho", "Posicion", "Alto", "Peso"]:
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
        
        # Limpiar tabla de propiedades
        for row in range(self.ui.propiedadesTable.rowCount()):
            self.ui.propiedadesTable.setItem(row, 1, QTableWidgetItem(""))
        
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