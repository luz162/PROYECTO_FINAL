from __future__ import annotations

"""
Visor DICOM 3D + Cortes 2D (MVC)
================================
• Carga recursivamente una carpeta con archivos *.dcm
• Genera un volumen 3D y lo normaliza a 0‑255
• Ofrece:
    – Reconstrucción 3D (scatter) incrustada (no plt.show())
    – Exploración interactiva por sliders (axial, coronal, sagital)
    – Botón para mostrar cortes 2D clásicos vía método `mostrar_cortes()` de `Paciente`
"""

import glob
import os
from typing import List

import numpy as np
import pydicom
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QFileDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas
from matplotlib.figure import Figure

from modelo.clases_imagenes import Paciente
from estilos import APP_STYLESHEET

# -----------------------------------------------------------------------------
# HELPERS
# -----------------------------------------------------------------------------

def _dicom_files(folder: str) -> List[str]:
    """Recupera todas las rutas .dcm en la carpeta (recursivo)."""
    return glob.glob(os.path.join(folder, "**", "*.dcm"), recursive=True)


def cargar_volumen_desde_dicom(dicom_folder: str) -> np.ndarray:
    """Devuelve volumen 3D (uint8) normalizado.

    • Acepta estudios con ImagePositionPatient *o* InstanceNumber.
    • Lanza ValueError si < 2 cortes válidos.
    """
    paths = _dicom_files(dicom_folder)
    print("Archivos encontrados:", len(paths))

    slices = []
    for p in paths:
        try:
            ds = pydicom.dcmread(p)
            if hasattr(ds, "ImagePositionPatient") or hasattr(ds, "InstanceNumber"):
                slices.append(ds)
        except Exception as exc:
            print(f"Error leyendo {p}: {exc}")

    if len(slices) < 2:
        raise ValueError("No se encontraron suficientes imágenes DICOM válidas.")

    # Orden inteligente
    try:
        slices.sort(key=lambda s: float(s.ImagePositionPatient[2]))
    except AttributeError:
        slices.sort(key=lambda s: int(s.InstanceNumber))

    volume = np.stack([s.pixel_array for s in slices], axis=0).astype(np.float32)
    volume = (volume - volume.min()) / (np.ptp(volume) + 1e-5) * 255
    return volume.astype(np.uint8)

# -----------------------------------------------------------------------------
# VISTA
# -----------------------------------------------------------------------------

class VistaDICOM3D(QWidget):
    """Widget principal que integra exploración de cortes 2D y reconstrucción 3D."""

    def __init__(self, controlador):
        super().__init__()
        self.setStyleSheet(APP_STYLESHEET)
        self.controlador = controlador
        self.setWindowTitle("Visor DICOM 3D")
        self.setMinimumSize(900, 650)
        self.volumen: np.ndarray | None = None

        # Canvas principal para cortes 2D
        self.canvas2d: Canvas | None = None
        self.ax: "Figure.axes" | None = None

        # Canvas para 3D (se crea on‑demand)
        self.canvas3d: Canvas | None = None
        self.ax3d: "Figure.axes" | None = None

        self._init_ui()

    # --------------------------------------------- UI Construction -----------
    def _init_ui(self):
        self.layout = QVBoxLayout(self)

        # --- Botones de acción ------------------------------------------------
        btn_cargar = QPushButton("Cargar carpeta DICOM", self)
        btn_cargar.clicked.connect(self.cargar_dicom)

        btn_3d = QPushButton("Mostrar reconstrucción 3D", self)
        btn_3d.clicked.connect(self.mostrar_3d)

        btn_cortes = QPushButton("Mostrar cortes 2D clásicos", self)
        btn_cortes.clicked.connect(self.mostrar_cortes_modelo)

        for btn in (btn_cargar, btn_3d, btn_cortes):
            self.layout.addWidget(btn)

        # --- Canvas Matplotlib para cortes interactivos ----------------------
        self.canvas2d = Canvas(Figure(figsize=(5, 4)))
        self.ax = self.canvas2d.figure.add_subplot(111)
        self.layout.addWidget(self.canvas2d)

        # --- Sliders por plano ----------------------------------------------
        self.slider_ax, _ = self._crear_slider("Axial", self.actualizar_corte_axial)
        self.slider_cor, _ = self._crear_slider("Coronal", self.actualizar_corte_coronal)
        self.slider_sag, _ = self._crear_slider("Sagital", self.actualizar_corte_sagital)

    def _crear_slider(self, name: str, slot):
        lbl = QLabel(name)
        sld = QSlider(Qt.Horizontal)
        sld.setEnabled(False)
        sld.valueChanged.connect(slot)
        self.layout.addWidget(lbl)
        self.layout.addWidget(sld)
        return sld, lbl

    # ---------------------------------------------------- Carga DICOM ---------
    def cargar_dicom(self):
        folder = QFileDialog.getExistingDirectory(self, "Selecciona carpeta DICOM")
        if not folder:
            return
        try:
            self.volumen = cargar_volumen_desde_dicom(folder)
            QMessageBox.information(self, "Carga exitosa", "Volumen cargado.")

            z, y, x = self.volumen.shape
            for sld, dim in zip(
                (self.slider_ax, self.slider_cor, self.slider_sag), (z, y, x)
            ):
                sld.setMaximum(dim - 1)
                sld.setEnabled(True)
                sld.setValue(dim // 2)

            # Muestra el corte axial por defecto
            self.actualizar_corte_axial(z // 2)
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    # ---------------------------------------------------- Reconstrucción 3D ---
    def mostrar_3d(self):
        if self.volumen is None:
            QMessageBox.warning(self, "Sin volumen", "Carga primero un estudio DICOM.")
            return

        # Crear canvas 3D la primera vez
        if self.canvas3d is None:
            self.canvas3d = Canvas(Figure(figsize=(5, 4)))
            self.ax3d = self.canvas3d.figure.add_subplot(111, projection="3d")
            self.layout.addWidget(self.canvas3d)
        else:
            self.ax3d.clear()

        QTimer.singleShot(10, self._pintar_3d)

    def _pintar_3d(self):
        if self.volumen is None:
            return

        # 1) Limpiar figura
        self.canvas3d.figure.clf()
        self.ax3d = self.canvas3d.figure.add_subplot(111, projection="3d")

        # 2) Obtener y sub‑muestrear coordenadas
        coords = np.column_stack(np.nonzero(self.volumen))      # (N, 3)  ->  [z, y, x]
        max_pts = 120_000
        if coords.shape[0] > max_pts:
            idx = np.random.choice(coords.shape[0], max_pts, replace=False)
            coords = coords[idx]

        z, y, x = coords.T     # des‑empaquetar ya tras el muestreo

        # 3) Colores en escala de grises normalizada
        intens = (self.volumen[z, y, x] - self.volumen.min()) / (
            np.ptp(self.volumen) + 1e-5
        )

        # 4) Scatter muy ligero
        self.ax3d.scatter(
            x, y, z,
            c=intens,
            cmap="gray",
            marker=".",
            alpha=0.35,
            s=1,
        )
        self.ax3d.set_title("Reconstrucción 3D")
        self.ax3d.set_xlabel("X")
        self.ax3d.set_ylabel("Y")
        self.ax3d.set_zlabel("Z")
        self.canvas3d.draw_idle()


    # --------------------------------------------------- Sliders callbacks ----
    def _draw_slice(self, img: np.ndarray, title: str):
        self.ax.clear()
        self.ax.imshow(img, cmap="gray")
        self.ax.set_title(title)
        self.ax.axis("off")
        self.canvas2d.draw_idle()

    def actualizar_corte_axial(self, idx: int):
        if self.volumen is None:
            return
        self._draw_slice(self.volumen[idx, :, :], f"Axial {idx}")

    def actualizar_corte_coronal(self, idx: int):
        if self.volumen is None:
            return
        self._draw_slice(self.volumen[:, idx, :], f"Coronal {idx}")

    def actualizar_corte_sagital(self, idx: int):
        if self.volumen is None:
            return
        self._draw_slice(self.volumen[:, :, idx], f"Sagital {idx}")

    # ------------------------------------------------ Cortes 2D clásicos ------
    def mostrar_cortes_modelo(self):
        if self.volumen is None:
            QMessageBox.warning(self, "Sin volumen", "Carga primero un estudio DICOM.")
            return
        tmp = Paciente("Volumen DICOM", 0, "TMP", self.volumen)
        tmp.mostrar_cortes()
