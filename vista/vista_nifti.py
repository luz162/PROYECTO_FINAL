from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QFileDialog, QVBoxLayout, QHBoxLayout, QMessageBox, QSlider
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt
from modelo.clase_ImagenNifti import ImagenNifti

class VistaNifti(QWidget):
    def __init__(self, controlador):
        super().__init__()
        from estilos import APP_STYLESHEET  
        self.setStyleSheet(APP_STYLESHEET)
        self.controlador = controlador
        self.setWindowTitle("Visualización de Imagen NIfTI")
        self.imagen_nifti = None
        self._construir_ui()

    def _construir_ui(self):
        layout = QVBoxLayout()

        self.btn_cargar = QPushButton("Cargar archivo NIfTI")
        self.btn_cargar.clicked.connect(self.cargar_nifti)
        layout.addWidget(self.btn_cargar)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setEnabled(False)
        self.slider.valueChanged.connect(self.mostrar_corte)
        layout.addWidget(self.slider)

        self.setLayout(layout)

    def cargar_nifti(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo NIfTI", "", "NIfTI files (*.nii *.nii.gz)")
        if ruta:
            try:
                self.imagen_nifti = ImagenNifti(ruta)
                self.slider.setMaximum(self.imagen_nifti.datos.shape[2] - 1)
                self.slider.setValue(self.imagen_nifti.datos.shape[2] // 2)
                self.slider.setEnabled(True)
                self.mostrar_corte()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo cargar el archivo NIfTI.\n{str(e)}")

    def mostrar_corte(self):
        if self.imagen_nifti:
            indice = self.slider.value()
            corte = self.imagen_nifti.obtener_corte_axial(indice)
            plt.figure(figsize=(5,5))
            plt.imshow(corte.T, cmap='gray', origin='lower')
            plt.title(f"Corte axial {indice}")
            plt.axis('off')
            plt.show()
