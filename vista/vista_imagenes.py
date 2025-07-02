from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout

class VistaImagenes(QWidget):
    def __init__(self, controlador):
        super().__init__()
        from estilos import APP_STYLESHEET  
        self.setStyleSheet(APP_STYLESHEET)
        self.controlador = controlador
        self.setWindowTitle("Selector de Imágenes")
        layout = QVBoxLayout()
        btn_dicom = QPushButton("Ver imágenes DICOM")
        btn_simple = QPushButton("Ver imágenes JPG/PNG")
        btn_dicom.clicked.connect(self.controlador.mostrar_dicom)
        btn_simple.clicked.connect(self.controlador.mostrar_simple)
        layout.addWidget(btn_dicom)
        layout.addWidget(btn_simple)
        self.setLayout(layout)