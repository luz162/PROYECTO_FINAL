from PyQt5.QtWidgets import (QWidget, QLabel, QPushButton, QFileDialog,
                             QVBoxLayout, QHBoxLayout, QMessageBox, QInputDialog,
                             QSpinBox, )
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from modelo.clases_imagenes import ImagenSimple
import cv2

class VistaImagenSimple(QWidget):
    """Ventana de procesamiento para imágenes JPG/PNG."""

    def __init__(self, controlador):
        super().__init__()
        from estilos import APP_STYLESHEET
        self.setStyleSheet(APP_STYLESHEET)
        self.controlador = controlador
        self.setWindowTitle("Procesamiento de Imagen Simple")
        self.setMinimumSize(900, 650)

        self.img_obj = None          # modelo
        self.img_proc = None         # ndarray que se muestra
        self.img_bin = None          # último binarizado (para morfología)

        self._build_ui()

    def _build_ui(self):
        self.lbl = QLabel("Imagen no cargada")
        self.lbl.setAlignment(Qt.AlignCenter)

        # ---- SpinBox de kernel (compartido) ----
        self.spin_kernel = QSpinBox()
        self.spin_kernel.setRange(1, 21)
        self.spin_kernel.setSingleStep(2)
        self.spin_kernel.setValue(5)
        self.spin_kernel.setPrefix("Kernel: ")

        # ---- Botones ----
        self.btn_cargar    = QPushButton("Cargar")
        self.btn_color     = QPushButton("Espacio color…")
        self.btn_eq        = QPushButton("Ecualizar")
        self.btn_clahe     = QPushButton("CLAHE (nuevo)")
        self.btn_bin       = QPushButton("Binarizar")
        self.btn_apertura  = QPushButton("Apertura")
        self.btn_cierre    = QPushButton("Cierre")
        self.btn_contar    = QPushButton("Contar células")

        # ---- Conexiones ----
        self.btn_cargar.clicked.connect(self.cargar)
        self.btn_color.clicked.connect(self.aplicar_color)
        self.btn_eq.clicked.connect(self.aplicar_eq)
        self.btn_clahe.clicked.connect(self.aplicar_clahe)
        self.btn_bin.clicked.connect(self.aplicar_bin)
        self.btn_apertura.clicked.connect(self.aplicar_apertura)
        self.btn_cierre.clicked.connect(self.aplicar_cierre)
        self.btn_contar.clicked.connect(self.aplicar_conteo)

        # ---- Layout botones ----
        fila1 = QHBoxLayout()
        fila1.addWidget(self.btn_cargar)
        fila1.addWidget(self.btn_color)
        fila1.addWidget(self.btn_eq)
        fila1.addWidget(self.btn_clahe)
        fila1.addStretch()

        fila2 = QHBoxLayout()
        fila2.addWidget(self.btn_bin)
        fila2.addWidget(self.btn_apertura)
        fila2.addWidget(self.btn_cierre)
        fila2.addWidget(self.btn_contar)
        fila2.addWidget(self.spin_kernel)
        fila2.addStretch()

        # ---- Contenedor principal ----
        layout = QVBoxLayout(self)
        layout.addWidget(self.lbl)
        layout.addLayout(fila1)
        layout.addLayout(fila2)

  
    def _mostrar(self, img):
        if img is None:
            return
        img = img.copy()
        if len(img.shape) == 2:                     # gris
            h, w = img.shape
            qimg = QImage(img.data, w, h, img.strides[0],
                          QImage.Format_Grayscale8)
        else:
            h, w, ch = img.shape
            qimg = QImage(img.data, w, h, ch * w,
                          QImage.Format_RGB888).rgbSwapped()
        self.lbl.setPixmap(QPixmap.fromImage(qimg).scaled(
            640, 640, Qt.KeepAspectRatio))
        self.img_proc = img

    def _check(self):
        if not self.img_obj:
            QMessageBox.warning(self, "Sin imagen", "Debes cargar una imagen.")
            return False
        return True

    def cargar(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar imagen", "", "Imágenes (*.png *.jpg *.jpeg)"
        )
        if ruta:
            try:
                self.img_obj = ImagenSimple(ruta)
                self.img_proc = self.img_obj.imagen_color.copy()
                self.img_bin = None
                self._mostrar(self.img_proc)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    # ---------- Procesos ----------
    def aplicar_color(self):
        if not self._check():
            return
        espacios = ["RGB", "HSV", "LAB", "YCrCb"]
        espacio, ok = QInputDialog.getItem(self, "Espacio de color",
                                           "Selecciona:", espacios, 0, False)
        if ok and espacio:
            self._mostrar(self.img_obj.cambiar_espacio_color(espacio))

    def aplicar_eq(self):
        if self._check():
            self._mostrar(self.img_obj.ecualizar_histograma())

    def aplicar_clahe(self):
        if self._check():
            self._mostrar(self.img_obj.aplicar_clahe())

    def aplicar_bin(self):
        if not self._check():
            return
        umbral, ok = QInputDialog.getInt(
            self, "Umbral fijo",
            "Introduce un valor de 0‑255 (‑1 para Otsu):", value=127, min=-1, max=255
        )
        if ok:
            metodo = "otsu" if umbral == -1 else "fijo"
            self.img_bin = self.img_obj.binarizar(umbral=umbral, metodo=metodo)
            self._mostrar(self.img_bin)

    def aplicar_apertura(self):
        if not self._check() or self.img_bin is None:
            QMessageBox.warning(self, "Falta binarizar",
                                "Primero realiza la binarización.")
            return
        k = self.spin_kernel.value()
        self._mostrar(self.img_obj.morfologia(self.img_bin, k, "apertura"))

    def aplicar_cierre(self):
        if not self._check() or self.img_bin is None:
            QMessageBox.warning(self, "Falta binarizar",
                                "Primero realiza la binarización.")
            return
        k = self.spin_kernel.value()
        self._mostrar(self.img_obj.morfologia(self.img_bin, k, "cierre"))

    def aplicar_conteo(self):
        if not self._check():
            return
        k = self.spin_kernel.value()
        out, n = self.img_obj.contar_celulas(k)
        self._mostrar(out)
        QMessageBox.information(self, "Conteo de células",
                                f"Células detectadas: {n}")
