from PyQt5.QtWidgets import QWidget, QLabel,QTableWidgetItem, QLineEdit, QPushButton, QVBoxLayout

class VistaPacientes(QWidget):
    def __init__(self, controlador):
        super().__init__()
        from estilos import APP_STYLESHEET  
        self.setStyleSheet(APP_STYLESHEET)
        self.controlador = controlador
        self.setWindowTitle("Gestión de Pacientes")
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Gestión de pacientes (próximamente)"))
        self.setLayout(layout)


    def actualizar_tabla(self):
        pacientes = self.controlador.obtener_pacientes()
        self.tabla.setRowCount(len(pacientes))
        self.tabla.setColumnCount(6)  # id, nombre, edad, sexo, fecha, diagnóstico
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre", "Edad", "Sexo", "Fecha", "Diagnóstico"])
        
        for fila, (id, nombre, edad, sexo, fecha, diagnostico) in enumerate(pacientes):
            self.tabla.setItem(fila, 0, QTableWidgetItem(str(id)))
            self.tabla.setItem(fila, 1, QTableWidgetItem(nombre))
            self.tabla.setItem(fila, 2, QTableWidgetItem(edad))
            self.tabla.setItem(fila, 3, QTableWidgetItem(sexo))
            self.tabla.setItem(fila, 4, QTableWidgetItem(fecha))
            self.tabla.setItem(fila, 5, QTableWidgetItem(diagnostico))
       