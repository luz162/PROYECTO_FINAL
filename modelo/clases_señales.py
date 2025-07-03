import os
import numpy as np
import pandas as pd
import scipy.io as sio
import matplotlib.pyplot as plt
from matplotlib import gridspec

# Diccionarios principales
objetos_csv = {}
rutas_graficos = {}

class ArchivoCSV:
    def __init__(self):
        self.df = None

    """Carga el archivo CSV desde la ruta."""
    def cargar_csv(self, ruta):  
        self.df = pd.read_csv(ruta)

    """Devuelve las columnas si el DataFrame fue cargado."""
    def obtener_columnas(self):
        return self.df.columns if self.df is not None else []
    
    """Devuelve el DataFrame completo."""
    def obtener_datos(self):
        return self.df
    
    """Grafica un scatter plot en la figura proporcionada."""
    def graficar_scatter(self, col_x, col_y, figura):
        ax = figura.add_subplot(111)
        ax.scatter(self.df[col_x], self.df[col_y])
        ax.set_xlabel(col_x)
        ax.set_ylabel(col_y)
        ax.set_title(f"Scatter: {col_x} vs {col_y}")

class ArchivoMAT:
    def __init__(self, nombre, ruta):
        self.nombre = nombre
        self.ruta = ruta
        self.data = sio.loadmat(ruta)
        self.senal = self.data['data']  # Asegura que 'data' existe en el .mat

        # Si tiene 3 dimensiones (por ejemplo: canales, muestras, épocas), toma la primera época
        if self.senal.ndim == 3:
            self.senal = self.senal[:, :, 0]

        # Frecuencia de muestreo fija 
        self.fs = 100  # Hz

    def extraer_intervalo(self, ch_ini, ch_fin, t_ini, t_fin):
        if ch_ini > ch_fin or ch_fin >= self.senal.shape[0]:
            raise ValueError("Rango de canales inválido")

        idx_ini = int(t_ini * self.fs)
        idx_fin = int(t_fin * self.fs)
        if idx_ini >= idx_fin or idx_fin > self.senal.shape[1]:
            raise ValueError("Intervalo de tiempo inválido")

        t = np.arange(idx_ini, idx_fin) / self.fs
        datos = self.senal[ch_ini:ch_fin + 1, idx_ini:idx_fin]
        return t, datos

    def graficar(self, xmin, xmax, eje, epoca):
        muestras = self.senal.shape[1]
        tiempo = np.arange(muestras) / self.fs

        fig = plt.figure(figsize=(12, 8))
        gs = gridspec.GridSpec(2, 2)

        ax1 = fig.add_subplot(gs[0, :])
        idx_ini = int(xmin * self.fs)
        idx_fin = int(xmax * self.fs)

        if self.senal.ndim == 3:
            senal_epoca = self.senal[:4, :, epoca]
        else:
            senal_epoca = self.senal[:4, :]

        for i in range(senal_epoca.shape[0]):
            ax1.plot(tiempo[idx_ini:idx_fin], senal_epoca[i, idx_ini:idx_fin], label=f'Canal {i+1}')
        ax1.set_title("Señales continuas")
        ax1.set_xlabel("Tiempo (s)")
        ax1.set_ylabel("Amplitud")
        ax1.legend()

        ax2 = fig.add_subplot(gs[1, 0])
        if eje == 0:
            promedio = np.mean(senal_epoca, axis=0)
        elif eje == 1:
            promedio = np.mean(senal_epoca, axis=1)
        else:
            raise ValueError("Eje inválido, debe ser 0 o 1")
        ax2.stem(np.arange(len(promedio)), promedio)
        ax2.set_title("Promedio tipo Stem")
        ax2.set_xlabel("Índice")
        ax2.set_ylabel("Valor")

        ax3 = fig.add_subplot(gs[1, 1])
        promedio_epoca = np.mean(senal_epoca, axis=0)
        ax3.hist(promedio_epoca, bins=20)
        ax3.set_title("Histograma de época promedio")
        ax3.set_xlabel("Valor")
        ax3.set_ylabel("Frecuencia")

        plt.tight_layout()
        ruta_img = os.path.join("recursos", f"grafico_mat_{self.nombre}.png")
        plt.savefig(ruta_img)
        plt.close()

       