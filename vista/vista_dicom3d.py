from __future__ import annotations
import glob, os
from typing import List

import numpy as np
import pydicom
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QFileDialog, QMessageBox, QPushButton, QVBoxLayout, QWidget
)
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

        # ---------- UI ----------
        lay = QVBoxLayout(self)

        btn_cargar = QPushButton("Cargar carpeta DICOM")
        btn_cargar.clicked.connect(self.cargar_dicom)
        btn_3d = QPushButton("Mostrar reconstrucción 3D")
        btn_3d.clicked.connect(self.mostrar_3d)
        lay.addWidget(btn_cargar)
        lay.addWidget(btn_3d)

        # Canvas con 3 subplots para los cortes
        self.canvas2d = Canvas(Figure(figsize=(9, 4)))
        fig = self.canvas2d.figure
        self.ax_axial   = fig.add_subplot(1, 3, 1)
        self.ax_coronal = fig.add_subplot(1, 3, 2)
        self.ax_sagital = fig.add_subplot(1, 3, 3)
        lay.addWidget(self.canvas2d)

    # --------------------------- Cargar DICOM ---------------------------------
    def cargar_dicom(self):
        carpeta = QFileDialog.getExistingDirectory(self, "Selecciona carpeta DICOM")
        if not carpeta:
            return
        try:
            self.volumen = cargar_volumen_desde_dicom(carpeta)
            QMessageBox.information(self, "Carga exitosa", "Volumen cargado.")
            self.mostrar_cortes()  
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))
            import traceback; traceback.print_exc()
        # ----------------------------- VISTAS 2D --------------------------------------
    def mostrar_cortes(self):
        """Muestra axial, coronal y sagital en el canvas de la interfaz."""
        if self.volumen is None:
            return

        vol = self.volumen
        z, y, x = vol.shape

        img_axial   = vol[z // 2, :, :]
        img_coronal = vol[:, y // 2, :]
        img_sagital = vol[:, :, x // 2]
        
        target_shape = (x, y)  # mismo orden que img_axial.shape: (y, x)

        img_coronal = cv2.resize(img_coronal, target_shape, interpolation=cv2.INTER_AREA)
        img_sagital = cv2.resize(img_sagital, target_shape, interpolation=cv2.INTER_AREA)

        # mostrar imágenes
        self.ax_axial.clear()
        self.ax_axial.imshow(img_axial, cmap="gray")
        self.ax_axial.set_title("Axial")
        self.ax_axial.axis("off")

        self.ax_coronal.clear()
        self.ax_coronal.imshow(img_coronal, cmap="gray")
        self.ax_coronal.set_title("Coronal")
        self.ax_coronal.axis("off")

        self.ax_sagital.clear()
        self.ax_sagital.imshow(img_sagital, cmap="gray")
        self.ax_sagital.set_title("Sagital")
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