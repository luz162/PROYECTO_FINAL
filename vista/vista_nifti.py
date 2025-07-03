from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QFileDialog, QMessageBox
from modelo.clase_ImagenNifti import convertir_dicom_a_nifti

class VistaNifti(QWidget):
    def __init__(self, controlador):
        super().__init__()
        from estilos import APP_STYLESHEET  
        self.setStyleSheet(APP_STYLESHEET)
        self.controlador = controlador
        self.setWindowTitle("Conversión DICOM a NIfTI")
        self._construir_ui()

    def _construir_ui(self):
        layout = QVBoxLayout()

        self.btn_convertir = QPushButton("Convertir carpeta DICOM a NIfTI")
        self.btn_convertir.clicked.connect(self.convertir_dicom)
        layout.addWidget(self.btn_convertir)

        self.setLayout(layout)

    def convertir_dicom(self):
        carpeta_dicom = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta DICOM")
        if not carpeta_dicom:
            return

        carpeta_salida = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta para guardar NIfTI")
        if not carpeta_salida:
            return

        try:
            ruta_nifti = convertir_dicom_a_nifti(carpeta_dicom, carpeta_salida)

            # Registrar en base de datos
            self.controlador.registrar_paciente_dicom(carpeta_dicom, ruta_nifti)

            QMessageBox.information(self, "Conversión exitosa", f"NIfTI guardado en:\n{ruta_nifti}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al convertir DICOM:\n{str(e)}")
