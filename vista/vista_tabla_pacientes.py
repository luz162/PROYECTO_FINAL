# ---------------- vista/vista_tabla_pacientes.py ----------------
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem

class VistaTablaPacientes(QWidget):
    def __init__(self, controlador):
        super().__init__()
        from estilos import APP_STYLESHEET  
        self.setStyleSheet(APP_STYLESHEET)
        self.controlador = controlador
        self.setWindowTitle("Lista de Pacientes")
        self._construir_ui()

    def _construir_ui(self):
        self.layout = QVBoxLayout()
        self.tabla = QTableWidget()
        self.layout.addWidget(self.tabla)
        self.setLayout(self.layout)
        self.actualizar_tabla()

    def actualizar_tabla(self):
        pacientes = self.controlador.obtener_pacientes()
        self.tabla.setRowCount(len(pacientes))
        self.tabla.setColumnCount(8)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "Patient ID", "Nombre", "Edad", "Sexo",
            "Fecha", "Ruta DICOM", "Ruta NIfTI"
        ])
        for i, fila in enumerate(pacientes):
            for j, valor in enumerate(fila):
                self.tabla.setItem(i, j, QTableWidgetItem(str(valor)))
