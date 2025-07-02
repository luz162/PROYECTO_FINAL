from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout

class VistaMenu(QWidget):
    def __init__(self, controlador, rol):
        super().__init__()
        from estilos import APP_STYLESHEET  
        self.setStyleSheet(APP_STYLESHEET)
        self.controlador = controlador
        self.setWindowTitle("Menú Principal")
        layout = QVBoxLayout()

        if rol == "imagen":
            botones = {
                "Ver Imágenes DICOM": self.controlador.mostrar_dicom,
                "Ver Imágenes Simples": self.controlador.mostrar_simple,
                "Cargar imagen NIfTI": self.controlador.mostrar_nifti,  
                "Pacientes": self.controlador.mostrar_tabla_pacientes,
            }
        elif rol == "senal":
            botones = {
        "Cargar archivos CSV": self.controlador.mostrar_csv,
        "Cargar archivo .MAT": self.controlador.mostrar_mat,
            }
        else:
            botones = {}

        # Botón de cerrar sesión disponible para ambos roles
        botones["Cerrar sesión"] = self.controlador.logout

        for texto, accion in botones.items():
            btn = QPushButton(texto)
            btn.clicked.connect(accion)
            layout.addWidget(btn)

        self.setLayout(layout)
