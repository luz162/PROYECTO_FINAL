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

    # ----------------------------- VISTAS 2D --------------------------------------
    def mostrar_cortes(self):
        vol = self.imagen_3d
        z, y, x = vol.shape

        fig, ax = plt.subplots(1, 3, figsize=(15, 5))

        # Axial
        ax[0].imshow(vol[z // 2, :, :], cmap='gray', aspect=x / y)
        ax[0].set_title('Axial')

        # Coronal
        ax[1].imshow(vol[:, y // 2, :], cmap='gray', aspect=x / z)
        ax[1].set_title('Coronal')

        # Sagital
        ax[2].imshow(vol[:, :, x // 2], cmap='gray', aspect=y / z)
        ax[2].set_title('Sagital')

        for a in ax:
            a.axis('off')
        plt.tight_layout()
        plt.show()

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
# CLASE IMAGEN MÉDICA (DICOM individual)
# ----------------------------------------------------------------------------------
class ImagenMedica:
    def __init__(self, ruta):
        self.ruta = ruta
        if not os.path.exists(ruta):
            raise FileNotFoundError(f"Archivo no encontrado: {ruta}")
        self.dicom = pydicom.dcmread(ruta)
        self.imagen = self.dicom.pixel_array

    def obtener_info_paciente(self):
        return {
            "nombre": getattr(self.dicom, 'PatientName', 'Anonimo'),
            "edad":   getattr(self.dicom, 'PatientAge',  '000Y'),
            "id":     getattr(self.dicom, 'PatientID',   'SinID')
        }

    def trasladar_imagen(self, dx=10, dy=10):
        """Traslación (shift) simple en píxeles."""
        h, w = self.imagen.shape
        M = np.float32([[1, 0, dx], [0, 1, dy]])
        return cv2.warpAffine(self.imagen, M, (w, h))

# ----------------------------------------------------------------------------------
# CLASE IMAGEN SIMPLE (JPG/PNG)
# ----------------------------------------------------------------------------------
class ImagenSimple:
    def __init__(self, ruta):
        self.ruta = ruta
        self.imagen = cv2.imread(ruta, cv2.IMREAD_GRAYSCALE)
        if self.imagen is None:
            raise FileNotFoundError(f"No se pudo cargar la imagen en {ruta}")

    # ---------- FILTRO GAUSSIANO ----------
    def filtro_gauss(self, ksize=5, sigma=1):
        return cv2.GaussianBlur(self.imagen, (ksize, ksize), sigma)

    # ---------- BINARIZACIÓN ----------
    def binarizar(self, metodo="binario", umbral=127):
        tipos = {
            "binario":            cv2.THRESH_BINARY,
            "binario_invertido":  cv2.THRESH_BINARY_INV,
            "truncado":           cv2.THRESH_TRUNC,
            "tozero":             cv2.THRESH_TOZERO,
            "tozero_invertido":   cv2.THRESH_TOZERO_INV
        }
        if metodo not in tipos:
            raise ValueError(f"Método inválido: {metodo}")
        _, binarizada = cv2.threshold(self.imagen, umbral, 255, tipos[metodo])
        return binarizada

    # ---------- MORFOLOGÍA ----------
    def morfologia(self, img_bin, ksize=5, oper="close"):
        kernel = np.ones((ksize, ksize), np.uint8)
        op = cv2.MORPH_CLOSE if oper == "close" else cv2.MORPH_OPEN
        return cv2.morphologyEx(img_bin, op, kernel)

    # ---------- DETECCIÓN DE BORDES ----------
    def bordes_canny(self, low=50, high=150):
        return cv2.Canny(self.imagen, low, high)

    # ---------- ANOTAR ----------
    def anotar_imagen(self, img, texto="Demo", forma="cuadrado"):
        color = (255, 255, 255)
        annotated = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        if forma == "cuadrado":
            cv2.rectangle(annotated, (50, 50), (300, 120), color, -1)
            cv2.putText(annotated, texto, (60, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        elif forma == "circulo":
            cv2.circle(annotated, (175, 85), 70, color, -1)
            cv2.putText(annotated, texto, (110, 95),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        return annotated

    # ---------- WATERSHED SEGMENTACIÓN ----------
    def watershed_segmentacion(self, umbral_rel=0.7, kernel_size=3):
        import cv2, numpy as np
        gray = self.imagen                               # ya es gris
        _, thresh = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, 2)
        sure_bg = cv2.dilate(opening, kernel, 3)

        dist = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
        _, sure_fg = cv2.threshold(dist, umbral_rel * dist.max(), 255, 0)
        sure_fg = np.uint8(sure_fg)
        unknown = cv2.subtract(sure_bg, sure_fg)

        _, markers = cv2.connectedComponents(sure_fg)
        markers = markers + 1
        markers[unknown == 255] = 0

        img_color = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        markers = cv2.watershed(img_color, markers)
        img_color[markers == -1] = [0, 0, 255]           # bordes en rojo
        return img_color