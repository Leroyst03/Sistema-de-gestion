from PyQt5.QtCore import QObject, QTimer
from Model.IOProvider import IOProvider
from View.IOWidget import IOWidget

class IOController(QObject):
    def __init__(self):
        super().__init__()
        self.model = IOProvider()
        self.view = IOWidget()
        
        # Inicialmente no monitoreamos
        self.timer = None
        self.is_monitoring = False
        
        # Inicializar la vista con todos los puntos en 0 (rojos)
        self.view.update_io_states(0, 0)
    
    def start_monitoring(self):
        """Comenzar a monitorear los cambios en la base de datos IO"""
        if not self.is_monitoring:
            # Configurar temporizador para actualización automática
            self.timer = QTimer()
            self.timer.timeout.connect(self.update_io_display)
            self.timer.start(500)  # Actualizar cada 500ms
            self.is_monitoring = True
        
        # Actualizar inmediatamente con los valores actuales de la BD
        self.update_io_display()
    
    def stop_monitoring(self):
        """Detener el monitoreo de I/O"""
        if self.timer and self.is_monitoring:
            self.timer.stop()
            self.timer = None
            self.is_monitoring = False
    
    def reset_display(self):
        """Resetear la visualización a todos los puntos en 0 (rojos)"""
        self.view.update_io_states(0, 0)
    
    def update_io_display(self):
        """Actualizar la visualización de entradas/salidas"""
        try:
            input_value, output_value = self.model.get_io_data()
            self.view.update_io_states(input_value, output_value)
        except Exception as e:
            print(f"Error actualizando I/O: {e}")
            # Si hay error, mostrar todos en 0
            self.view.update_io_states(0, 0)
    
    def get_widget(self):
        """Obtener el widget para insertar en la interfaz principal"""
        return self.view