from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen

class IOPoint(QFrame):
    """Widget que representa un punto de entrada/salida individual"""
    def __init__(self, label: str = "", parent=None):
        super().__init__(parent)
        self.label = label
        self.state = False  # False = apagado, True = encendido
        self.setFixedSize(24, 24)  # Tamaño más pequeño para mejor ajuste
        self.setStyleSheet("""
            QFrame {
                border: 1px solid #444;
                border-radius: 12px;
                background-color: #1e1e1e;
            }
        """)
        
    def set_state(self, state: bool):
        """Establecer el estado del punto (encendido/apagado)"""
        self.state = state
        self.update()
    
    def paintEvent(self, event):
        """Dibujar el punto"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Dibujar punto según estado
        if self.state:
            painter.setBrush(QBrush(QColor(76, 175, 80)))  # Verde más suave
        else:
            painter.setBrush(QBrush(QColor(244, 67, 54)))  # Rojo más suave
        
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, 20, 20)
        
        # Dibujar etiqueta (número del bit)
        painter.setPen(QPen(Qt.white))
        painter.drawText(self.rect(), Qt.AlignCenter, self.label)

class IOWidget(QWidget):
    """Widget que muestra todos los puntos de entrada/salida"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """Configurar la interfaz del widget"""
        self.setStyleSheet("""
            QWidget {
                background-color: #111;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
                font-size: 10px;
            }
            QLabel#title {
                font-weight: bold;
                font-size: 11px;
                color: #1a73e8;
            }
            QFrame#separator {
                background-color: #444;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)
        
        # Contenedor principal
        main_layout = QHBoxLayout()
        main_layout.setSpacing(15)
        
        # Almacenar referencias a los puntos y etiquetas
        self.input_points = []
        self.output_points = []
        self.input_bin_labels = []
        self.output_bin_labels = []
        
        # Panel de Entradas (Inputs)
        input_panel, input_points, input_bin_labels = self.create_io_panel("ENTRADAS", 5)
        self.input_points = input_points
        self.input_bin_labels = input_bin_labels
        main_layout.addWidget(input_panel)
        
        # Separador vertical
        separator = QFrame()
        separator.setObjectName("separator")
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setMaximumWidth(1)
        main_layout.addWidget(separator)
        
        # Panel de Salidas (Outputs)
        output_panel, output_points, output_bin_labels = self.create_io_panel("SALIDAS", 5)
        self.output_points = output_points
        self.output_bin_labels = output_bin_labels
        main_layout.addWidget(output_panel)
        
        layout.addLayout(main_layout)
    
    def create_io_panel(self, title: str, count: int):
        """Crear un panel de entradas o salidas"""
        panel = QWidget()
        panel.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)
        
        panel_layout = QVBoxLayout(panel)
        panel_layout.setSpacing(5)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        
        # Título del panel
        title_label = QLabel(title)
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignCenter)
        panel_layout.addWidget(title_label)
        
        # Grid para los puntos
        grid = QGridLayout()
        grid.setSpacing(8)
        grid.setContentsMargins(0, 0, 0, 0)
        
        # Listas para almacenar referencias
        points = []
        bin_labels = []
        
        for i in range(count):
            # Etiqueta del bit
            bit_label = QLabel(f"Bit {i}")
            bit_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            grid.addWidget(bit_label, i, 0)
            
            # Punto
            point = IOPoint(str(i))
            grid.addWidget(point, i, 1)
            points.append(point)
            
            # Valor binario
            bin_label = QLabel("0")
            bin_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            bin_label.setStyleSheet("font-family: monospace; min-width: 15px;")
            grid.addWidget(bin_label, i, 2)
            bin_labels.append(bin_label)
        
        panel_layout.addLayout(grid)
        
        return panel, points, bin_labels
    
    def update_io_states(self, input_mask: int, output_mask: int):
        """Actualizar los estados de todos los puntos según las máscaras de bits"""
        # Actualizar puntos de entrada
        for i in range(5):
            bit_state = bool((input_mask >> i) & 1)
            self.input_points[i].set_state(bit_state)
            self.input_bin_labels[i].setText("1" if bit_state else "0")
        
        # Actualizar puntos de salida
        for i in range(5):
            bit_state = bool((output_mask >> i) & 1)
            self.output_points[i].set_state(bit_state)
            self.output_bin_labels[i].setText("1" if bit_state else "0")