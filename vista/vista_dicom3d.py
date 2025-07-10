from __future__ import annotations
import glob, os
from typing import List

import numpy as np
import pydicom
import nibabel as nib
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QFileDialog, QMessageBox, QPushButton, QVBoxLayout, QWidget, 
    QHBoxLayout, QLabel, QSlider
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas
from matplotlib.figure import Figure

from estilos import APP_STYLESHEET
import cv2
# ───────────────────────────── Helpers ─────────────────────────────────────────
def _dicom_files(folder: str) -> List[str]:
    return glob.glob(os.path.join(folder, "**", "*.dcm"), recursive=True)

def cargar_volumen_desde_dicom(folder: str) -> np.ndarray:
    paths = _dicom_files(folder)
    print("Archivos encontrados:", len(paths))
    slices = [
        pydicom.dcmread(p) for p in paths
        if (_ := pydicom.dcmread(p)) and
           (hasattr(_, "ImagePositionPatient") or hasattr(_, "InstanceNumber"))
    ]
    if len(slices) < 2:
        raise ValueError("No se encontraron suficientes imágenes DICOM válidas.")
    try:
        slices.sort(key=lambda s: float(s.ImagePositionPatient[2]))
    except AttributeError:
        slices.sort(key=lambda s: int(s.InstanceNumber))
    vol = np.stack([s.pixel_array for s in slices]).astype(np.float32)
    vol = (vol - vol.min()) / (np.ptp(vol) + 1e-5) * 255
    return vol.astype(np.uint8)

# ──────────────────────────── Vista ────────────────────────────────────────────
class VistaDICOM3D(QWidget):
    def __init__(self, controlador):
        super().__init__()
        self.setStyleSheet(APP_STYLESHEET)
        self.controlador = controlador
        self.setWindowTitle("Visor DICOM 3D")
        self.setMinimumSize(900, 650)

        self.volumen: np.ndarray | None = None
        self.canvas3d: Canvas | None = None
        self.ax3d    : "Figure.axes" | None = None
        
        # Variables para los índices actuales de cada plano
        self.indice_axial = 0
        self.indice_coronal = 0
        self.indice_sagital = 0

        # ---------- UI ----------
        lay = QVBoxLayout(self)

        btn_cargar = QPushButton("Cargar carpeta DICOM")
        btn_cargar.clicked.connect(self.cargar_dicom)
        btn_3d = QPushButton("Mostrar reconstrucción 3D")
        btn_3d.clicked.connect(self.mostrar_3d)
        btn_nifti = QPushButton("Convertir a NIfTI")
        btn_nifti.clicked.connect(self.convertir_a_nifti)
        lay.addWidget(btn_cargar)
        lay.addWidget(btn_3d)
        lay.addWidget(btn_nifti)

        # Canvas con 3 subplots para los cortes
        self.canvas2d = Canvas(Figure(figsize=(12, 4)))
        fig = self.canvas2d.figure
        self.ax_axial   = fig.add_subplot(1, 3, 1)
        self.ax_coronal = fig.add_subplot(1, 3, 2)
        self.ax_sagital = fig.add_subplot(1, 3, 3)
        lay.addWidget(self.canvas2d)
        
        # ---------- SLIDERS PARA NAVEGACIÓN ----------
        sliders_layout = QVBoxLayout()
        
        # Slider Axial (navega en Z)
        axial_layout = QHBoxLayout()
        self.label_axial = QLabel("Axial (Z): 0")
        self.slider_axial = QSlider(Qt.Horizontal)
        self.slider_axial.valueChanged.connect(self.actualizar_axial)
        axial_layout.addWidget(self.label_axial)
        axial_layout.addWidget(self.slider_axial)
        sliders_layout.addLayout(axial_layout)
        
        # Slider Coronal (navega en Y)
        coronal_layout = QHBoxLayout()
        self.label_coronal = QLabel("Coronal (Y): 0")
        self.slider_coronal = QSlider(Qt.Horizontal)
        self.slider_coronal.valueChanged.connect(self.actualizar_coronal)
        coronal_layout.addWidget(self.label_coronal)
        coronal_layout.addWidget(self.slider_coronal)
        sliders_layout.addLayout(coronal_layout)
        
        # Slider Sagital (navega en X)
        sagital_layout = QHBoxLayout()
        self.label_sagital = QLabel("Sagital (X): 0")
        self.slider_sagital = QSlider(Qt.Horizontal)
        self.slider_sagital.valueChanged.connect(self.actualizar_sagital)
        sagital_layout.addWidget(self.label_sagital)
        sagital_layout.addWidget(self.slider_sagital)
        sliders_layout.addLayout(sagital_layout)
        
        lay.addLayout(sliders_layout)

    # --------------------------- Cargar DICOM ---------------------------------
    def cargar_dicom(self):
        carpeta = QFileDialog.getExistingDirectory(self, "Selecciona carpeta DICOM")
        if not carpeta:
            return
        try:
            self.ruta_dicom = carpeta
            self.volumen = cargar_volumen_desde_dicom(carpeta)
            QMessageBox.information(self, "Carga exitosa", "Volumen cargado.")
            self.configurar_sliders()
            self.mostrar_cortes()  
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))
            import traceback; traceback.print_exc()
    
    def configurar_sliders(self):
        """Configura los rangos de los sliders según las dimensiones del volumen"""
        if self.volumen is None:
            return
            
        z, y, x = self.volumen.shape
        
        # Configurar slider axial (dimensión Z)
        self.slider_axial.setRange(0, z - 1)
        self.indice_axial = z // 2
        self.slider_axial.setValue(self.indice_axial)
        
        # Configurar slider coronal (dimensión Y)
        self.slider_coronal.setRange(0, y - 1)
        self.indice_coronal = y // 2
        self.slider_coronal.setValue(self.indice_coronal)
        
        # Configurar slider sagital (dimensión X)
        self.slider_sagital.setRange(0, x - 1)
        self.indice_sagital = x // 2
        self.slider_sagital.setValue(self.indice_sagital)
        
        # Actualizar etiquetas
        self.label_axial.setText(f"Axial (Z): {self.indice_axial}/{z-1}")
        self.label_coronal.setText(f"Coronal (Y): {self.indice_coronal}/{y-1}")
        self.label_sagital.setText(f"Sagital (X): {self.indice_sagital}/{x-1}")
    
    def actualizar_axial(self, valor):
        """Actualiza la vista axial cuando se mueve el slider"""
        self.indice_axial = valor
        if self.volumen is not None:
            z, y, x = self.volumen.shape
            self.label_axial.setText(f"Axial (Z): {valor}/{z-1}")
            self.mostrar_cortes()
    
    def actualizar_coronal(self, valor):
        """Actualiza la vista coronal cuando se mueve el slider"""
        self.indice_coronal = valor
        if self.volumen is not None:
            z, y, x = self.volumen.shape
            self.label_coronal.setText(f"Coronal (Y): {valor}/{y-1}")
            self.mostrar_cortes()
    
    def actualizar_sagital(self, valor):
        """Actualiza la vista sagital cuando se mueve el slider"""
        self.indice_sagital = valor
        if self.volumen is not None:
            z, y, x = self.volumen.shape
            self.label_sagital.setText(f"Sagital (X): {valor}/{x-1}")
            self.mostrar_cortes()
        # ----------------------------- VISTAS 2D --------------------------------------
    def mostrar_cortes(self):
        """Muestra axial, coronal y sagital en el canvas de la interfaz usando los índices de los sliders."""
        if self.volumen is None:
            return

        vol = self.volumen
        z, y, x = vol.shape

        # Usar los índices actuales de los sliders
        img_axial   = vol[self.indice_axial, :, :]
        img_coronal = vol[:, self.indice_coronal, :]
        img_sagital = vol[:, :, self.indice_sagital]
        
        # Redimensionar para visualización uniforme
        target_shape = (x, y)  # mismo orden que img_axial.shape: (y, x)
        img_coronal = cv2.resize(img_coronal, target_shape, interpolation=cv2.INTER_AREA)
        img_sagital = cv2.resize(img_sagital, target_shape, interpolation=cv2.INTER_AREA)

        # mostrar imágenes
        self.ax_axial.clear()
        self.ax_axial.imshow(img_axial, cmap="gray")
        self.ax_axial.set_title(f"Axial - Slice {self.indice_axial}")
        self.ax_axial.axis("off")

        self.ax_coronal.clear()
        self.ax_coronal.imshow(img_coronal, cmap="gray")
        self.ax_coronal.set_title(f"Coronal - Slice {self.indice_coronal}")
        self.ax_coronal.axis("off")

        self.ax_sagital.clear()
        self.ax_sagital.imshow(img_sagital, cmap="gray")
        self.ax_sagital.set_title(f"Sagital - Slice {self.indice_sagital}")
        self.ax_sagital.axis("off")

        self.canvas2d.draw_idle()
    # --------------------------- Reconstrucción 3D ----------------------------       
    def mostrar_3d(self):
        if self.volumen is None:
            QMessageBox.warning(self, "Sin volumen", "Carga primero un estudio DICOM.")
            return
        if self.canvas3d is None:
            self.canvas3d = Canvas(Figure(figsize=(5, 4)))
            self.ax3d = self.canvas3d.figure.add_subplot(111, projection="3d")
            self.layout().addWidget(self.canvas3d)
        QTimer.singleShot(10, self._pintar_3d)

    def _pintar_3d(self):
        if self.volumen is None:
            return

        self.canvas3d.figure.clf()
        ax3d = self.canvas3d.figure.add_subplot(111, projection="3d")

        # Umbral para descartar voxeles de fondo (aire)
        umbral = 50
        coords = np.column_stack(np.nonzero(self.volumen > umbral))

        if coords.shape[0] > 80_000:
            idx = np.random.choice(coords.shape[0], 80_000, replace=False)
            coords = coords[idx]

        z, y, x = coords.T
        intensidades = self.volumen[z, y, x]
        intens_norm = (intensidades - intensidades.min()) / (np.ptp(intensidades) + 1e-5)

        # Visualización 
        ax3d.scatter(
            x, y, z,
            c=intens_norm,
            cmap="plasma", 
            alpha=0.25,
            s=0.7
        )

        ax3d.set_title("Reconstrucción 3D")
        ax3d.set_xlabel("X")
        ax3d.set_ylabel("Y")
        ax3d.set_zlabel("Z")

        #  proporcion de los ejes
        ax3d.set_box_aspect([np.ptp(x), np.ptp(y), np.ptp(z)])

        #  rotación inicial para una vista más clara
        ax3d.view_init(elev=30, azim=120)

        self.canvas3d.draw_idle()
    # --------------------------- Conversión a NIfTI ----------------------------       
    def convertir_a_nifti(self):
        """Convierte el volumen DICOM cargado a formato NIfTI y lo guarda"""
        if self.volumen is None:
            QMessageBox.warning(self, "Sin volumen", "Carga primero un estudio DICOM.")
            return

        try:
            # Seleccionar ubicación para guardar el archivo NIfTI
            archivo_salida, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar como NIfTI",
                "volumen_convertido.nii.gz",
                "Archivos NIfTI (*.nii.gz *.nii)"
            )

            if not archivo_salida:
                return

            # Crear imagen NIfTI (transponer de (z, y, x) → (x, y, z))
            volumen_nifti = np.transpose(self.volumen, (2, 1, 0))
            img_nifti = nib.Nifti1Image(volumen_nifti, affine=np.eye(4))
            nib.save(img_nifti, archivo_salida)

            # Registrar en base de datos si ruta DICOM disponible
            if hasattr(self, "ruta_dicom"):
                self.controlador.registrar_paciente_dicom(self.ruta_dicom, archivo_salida)

            #  ACTUALIZAR TABLA DE PACIENTES SI ESTÁ ABIERTA
            self.controlador.mostrar_tabla_pacientes()

            QMessageBox.information(
                self,
                "Conversión exitosa",
                f"Volumen convertido y guardado en:\n{archivo_salida}"
            )

        except Exception as exc:
            QMessageBox.critical(self, "Error en conversión", f"Error al convertir a NIfTI:\n{str(exc)}")
            import traceback; traceback.print_exc()
