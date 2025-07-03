import os
import cv2
import pydicom
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D      # ← necesario para la vista 3D

# ----------------------------------------------------------------------------------
# CLASE PACIENTE (volúmenes DICOM 3D)
# ----------------------------------------------------------------------------------
class Paciente:
    def __init__(self, nombre, edad, id_paciente, imagen_3d):
        self.nombre = nombre
        self.edad = edad
        self.id = id_paciente
        self.imagen_3d = imagen_3d

    # ----------------------------- VISTA 3D ---------------------------------------
    def mostrar_3d(self):
        """Reconstrucción 3D de un volumen binario o de intensidades."""
        plt.close('all')  # cierra ventanas previas si estaban abiertas
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        vol = self.imagen_3d
        z, y, x = np.nonzero(vol)                       # coordenadas de voxels ≠ 0

        # Normalizamos intensidades a [0,1] para la paleta de colores
        intensidades = vol[z, y, x].astype(np.float32)
        intensidades = (intensidades - intensidades.min()) / (np.ptp(intensidades) + 1e-5)

        # Scatter 3D
        ax.scatter(x, y, z, c=intensidades, cmap='gray',
                   marker='.', alpha=0.3, s=0.5)

        ax.set_title("Reconstrucción 3D del Volumen")
        ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
        plt.show()

# ----------------------------------------------------------------------------------
# CLASE IMAGEN SIMPLE (JPG/PNG)
# ----------------------------------------------------------------------------------
class ImagenSimple:
    def __init__(self, ruta):
        self.ruta = ruta
        self.imagen_color = cv2.imread(ruta)  
        if self.imagen_color is None:
            raise ValueError("No se pudo cargar la imagen.")
        self.imagen_gris = cv2.cvtColor(self.imagen_color, cv2.COLOR_BGR2GRAY)
# ------------------------------------------------------------------
    # 1. Cambio de espacios de color
    # ------------------------------------------------------------------
    def cambiar_espacio_color(self, espacio: str = "HSV"):
        espacios = {
            "RGB":   cv2.COLOR_BGR2RGB,
            "HSV":   cv2.COLOR_BGR2HSV,
            "LAB":   cv2.COLOR_BGR2LAB,
            "YCrCb": cv2.COLOR_BGR2YCrCb,
        }
        if espacio not in espacios:
            raise ValueError(f"Espacio de color no válido: {espacio}")
        return cv2.cvtColor(self.imagen_color, espacios[espacio])

    # ------------------------------------------------------------------
    # 2. Ecualización global
    # ------------------------------------------------------------------
    def ecualizar_histograma(self):
        eq = cv2.equalizeHist(self.imagen_gray)
        return cv2.cvtColor(eq, cv2.COLOR_GRAY2BGR)  # devolver BGR para mostrar

    # ------------------------------------------------------------------
    # 3. CLAHE (método nuevo OpenCV, no visto en clase)
    # ------------------------------------------------------------------
    def aplicar_clahe(self, clip=2.0, grid=(8, 8)):
        clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=grid)
        clahe_img = clahe.apply(self.imagen_gray)
        return cv2.cvtColor(clahe_img, cv2.COLOR_GRAY2BGR)

    # ------------------------------------------------------------------
    # 4. Binarización (umbral fijo u Otsu/adaptativa)
    # ------------------------------------------------------------------
    def binarizar(self, umbral: int = 127, metodo: str = "fijo"):
        if metodo == "otsu":
            _, bin_img = cv2.threshold(self.imagen_gray, 0, 255,
                                       cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        elif metodo == "adapt":
            bin_img = cv2.adaptiveThreshold(self.imagen_gray, 255,
                                            cv2.ADAPTIVE_THRESH_MEAN_C,
                                            cv2.THRESH_BINARY, 11, 2)
        else:  # fijo
            _, bin_img = cv2.threshold(self.imagen_gray, umbral, 255,
                                       cv2.THRESH_BINARY)
        return bin_img

    # ------------------------------------------------------------------
    # 5. Morfología (apertura / cierre) con kernel ajustable
    # ------------------------------------------------------------------
    def morfologia(self, img_bin: np.ndarray, ksize: int = 5,
                   oper: str = "cierre"):
        kernel = np.ones((ksize, ksize), np.uint8)
        if oper == "apertura":
            op = cv2.MORPH_OPEN
        elif oper == "cierre":
            op = cv2.MORPH_CLOSE
        else:
            raise ValueError("oper debe ser 'apertura' o 'cierre'")
        return cv2.morphologyEx(img_bin, op, kernel)

    # ------------------------------------------------------------------
    # 6. Conteo de células
    # ------------------------------------------------------------------
    def contar_celulas(self, ksize: int = 3):
        # 1) Binarizar (Otsu) -> 2) Morfología apertura -> 3) Contornos
        bin_img = self.binarizar(metodo="otsu")
        limpiada = self.morfologia(bin_img, ksize, "apertura")
        cnts, _ = cv2.findContours(limpiada, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)

        # Dibujar contornos en copia a color
        out = cv2.cvtColor(self.imagen_gray, cv2.COLOR_GRAY2BGR)
        cv2.drawContours(out, cnts, -1, (0, 255, 0), 1)
        return out, len(cnts)