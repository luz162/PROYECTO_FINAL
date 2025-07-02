from PyQt5.QtWidgets import (QWidget, QLabel, QPushButton, QFileDialog,
                             QVBoxLayout, QHBoxLayout, QMessageBox)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
import cv2
import numpy as np
from modelo.clases_imagenes import ImagenSimple

class VistaImagenSimple(QWidget):
    def __init__(self, controlador):
        super().__init__()
        from estilos import APP_STYLESHEET  
        self.setStyleSheet(APP_STYLESHEET)
        self.controlador = controlador
        self.setWindowTitle("Procesamiento de Imagen Simple")
        self.img_obj = None       # instancia de ImagenSimple
        self.img_mostrada = None  # np.ndarray

        # ---------- Widgets ----------
        self.lbl = QLabel("Imagen no cargada")
        self.lbl.setAlignment(Qt.AlignCenter)

        btn_cargar = QPushButton("Cargar")
        btn_gauss = QPushButton("Filtro Gauss")
        btn_bin = QPushButton("Binarizar")
        btn_morf = QPushButton("Morfología")
        btn_bordes = QPushButton("Bordes Canny")
        btn_anota = QPushButton("Anotar")
        btn_watershed = QPushButton("Segmentar (Watershed)")

        # Conexiones
        btn_cargar.clicked.connect(self.cargar)
        btn_gauss.clicked.connect(self.aplicar_gauss)
        btn_bin.clicked.connect(self.aplicar_bin)
        btn_morf.clicked.connect(self.aplicar_morf)
        btn_bordes.clicked.connect(self.aplicar_bordes)
        btn_anota.clicked.connect(self.aplicar_anota)
        btn_watershed.clicked.connect(self.aplicar_watershed)

        # Layout
        botones = QHBoxLayout()
        for b in (btn_cargar, btn_gauss, btn_bin, btn_morf, btn_bordes, btn_anota, btn_watershed):
            botones.addWidget(b)

        layout = QVBoxLayout(self)
        layout.addWidget(self.lbl)
        layout.addLayout(botones)

    def _mostrar(self, img):
        if len(img.shape) == 2:
            h, w = img.shape
            qimg = QImage(img.data, w, h, img.strides[0], QImage.Format_Grayscale8)
        else:
            h, w, ch = img.shape
            bytes_per_line = ch * w
            qimg = QImage(img.data, w, h, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        self.lbl.setPixmap(QPixmap.fromImage(qimg).scaled(512, 512, Qt.KeepAspectRatio))
        self.img_mostrada = img

    def _check(self):
        if not self.img_obj:
            QMessageBox.warning(self, "Sin imagen", "Carga una imagen primero.")
            return False
        return True

    def cargar(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Seleccionar imagen", "", "Imágenes (*.png *.jpg *.jpeg)")
        if ruta:
            try:
                self.img_obj = ImagenSimple(ruta)
                self._mostrar(self.img_obj.imagen)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def aplicar_gauss(self):
        if self._check():
            self._mostrar(self.img_obj.filtro_gauss())

    def aplicar_bin(self):
        if self._check():
            img = self.img_obj.binarizar("binario", 127)
            self._mostrar(img)
            self.img_bin = img

    def aplicar_morf(self):
        if self._check():
            if not hasattr(self, "img_bin"):
                QMessageBox.warning(self, "Primero binariza", "Realiza primero la binarización.")
                return
            self._mostrar(self.img_obj.morfologia(self.img_bin, 5, "close"))

    def aplicar_bordes(self):
        if self._check():
            self._mostrar(self.img_obj.bordes_canny())

    def aplicar_anota(self):
        if self._check():
            img = self.img_obj.anotar_imagen(self.img_obj.imagen, "Paciente 001", "cuadrado")
            img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            self._mostrar(img_gray)

    def aplicar_watershed(self):
        if self._check():
            img_seg = self.img_obj.watershed_segmentacion()
            self._mostrar(img_seg)
