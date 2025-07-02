import os
import numpy as np
import pandas as pd
import scipy.io as sio
import matplotlib.pyplot as plt
from matplotlib import gridspec
from PyQt5.QtWidgets import QMessageBox

# Diccionarios principales
objetos_csv = {}
objetos_mat = {}
rutas_graficos = {}

class ArchivoCSV:
    def __init__(self, nombre, rutas_archivos):
        self.nombre = nombre
        self.rutas = rutas_archivos
        self.dataframes = [pd.read_csv(ruta) for ruta in rutas_archivos]
        self.df_recortado = None
        self.df_promedio = None

    def extraer_columna(self, columna, cantidad=200):
        columnas_extraidas = []
        for df in self.dataframes:
            if columna in df.columns:
                columnas_extraidas.append(df[columna].iloc[:cantidad].reset_index(drop=True))
            else:
                raise ValueError(f"Columna '{columna}' no encontrada en uno de los archivos.")

        self.df_recortado = pd.concat(columnas_extraidas, axis=1)
        self.df_recortado.columns = [f"Archivo_{i+1}" for i in range(len(columnas_extraidas))]

        nueva_ruta = f"csv_recortado_{self.nombre}.csv"
        self.df_recortado.to_csv(nueva_ruta, index=False)
        print(f"Archivo CSV combinado guardado como: {nueva_ruta}")

    def calcular_promedio_y_graficar(self):
        if self.df_recortado is None:
            raise ValueError("Primero debe extraerse la columna y crear el archivo recortado.")

        self.df_recortado["Promedio"] = self.df_recortado.mean(axis=1)

        plt.figure(figsize=(12, 5))
        plt.subplot(1, 2, 1)
        plt.plot(self.df_recortado["Promedio"])
        plt.title("Promedio de la variable")
        plt.xlabel("Índice")
        plt.ylabel("Promedio")

        plt.subplot(1, 2, 2)
        plt.boxplot(self.df_recortado["Promedio"])
        plt.title("Boxplot del promedio")
        plt.ylabel("Valor")

        ruta_img = f"grafico_promedio_{self.nombre}.png"
        plt.tight_layout()
        plt.savefig(ruta_img)
        plt.close()

        rutas_graficos[f"csv_{self.nombre}"] = ruta_img
        self.ruta_img = ruta_img   


class ArchivoMAT:
    def __init__(self, nombre, ruta):
        self.nombre = nombre
        self.ruta = ruta
        self.data = sio.loadmat(ruta)
        self.senal = self.data['data']  # Asegura que 'data' existe en el .mat

        # Si tiene 3 dimensiones (por ejemplo: canales, muestras, épocas), toma la primera época
        if self.senal.ndim == 3:
            self.senal = self.senal[:, :, 0]

        # Frecuencia de muestreo fija (ajústala si varía según tus datos)
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

        rutas_graficos[f"mat_{self.nombre}"] = ruta_img
        return ruta_img  # ← por si la vista quiere usarla