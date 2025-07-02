# ====================== V I S T A   M A T ==============================
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QFileDialog, QVBoxLayout, QHBoxLayout,
    QSpinBox, QDoubleSpinBox, QMessageBox, QComboBox
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas
from matplotlib.figure import Figure
import numpy as np
from modelo.clases_señales import ArchivoMAT
import os

class VistaMAT(QWidget):
    """Carga .mat, muestra llaves, plotea canales/intervalos y calcula promedios."""
    def __init__(self, controlador):
        super().__init__()
        from estilos import APP_STYLESHEET  
        self.setStyleSheet(APP_STYLESHEET)
        self.controlador = controlador
        self.setWindowTitle("Exploración de Señales MAT")
        self.mat_obj = None
        self._build_ui()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        v = QVBoxLayout(self)

        # ----- Cargar archivo & llaves
        btn_cargar = QPushButton("Cargar .mat")
        btn_cargar.clicked.connect(self.cargar_archivo)
        self.cmb_keys = QComboBox()

        h_top = QHBoxLayout(); h_top.addWidget(btn_cargar); h_top.addWidget(QLabel("Llave:")); h_top.addWidget(self.cmb_keys)
        v.addLayout(h_top)

        # ----- Parámetros de intervalo
        h_int = QHBoxLayout()
        self.sb_ch_ini = QSpinBox(); self.sb_ch_ini.setPrefix("Canal ini: "); self.sb_ch_ini.setRange(0, 500)
        self.sb_ch_fin = QSpinBox(); self.sb_ch_fin.setPrefix("Canal fin: "); self.sb_ch_fin.setRange(0, 500)
        self.sb_t_ini = QDoubleSpinBox(); self.sb_t_ini.setPrefix("t_ini: "); self.sb_t_ini.setDecimals(2); self.sb_t_ini.setRange(0, 1000)
        self.sb_t_fin = QDoubleSpinBox(); self.sb_t_fin.setPrefix("t_fin: "); self.sb_t_fin.setDecimals(2); self.sb_t_fin.setRange(0, 1000)
        for w in (self.sb_ch_ini, self.sb_ch_fin, self.sb_t_ini, self.sb_t_fin):
            h_int.addWidget(w)
        v.addLayout(h_int)

        # ----- Botones acción
        h_btn = QHBoxLayout()
        btn_plot = QPushButton("Graficar intervalo")
        btn_prom = QPushButton("Calcular promedio (eje 1) y mostrar stem")
        btn_plot.clicked.connect(self.graficar_intervalo)
        btn_prom.clicked.connect(self.promedio_eje1)
        h_btn.addWidget(btn_plot); h_btn.addWidget(btn_prom)
        v.addLayout(h_btn)
        # ----- Canvas matplotlib
        self.fig = Figure(figsize=(8, 6)); self.canvas = Canvas(self.fig)
        v.addWidget(self.canvas)

    # ------------------------------------------------------------------ Slots
    def cargar_archivo(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Selecciona .mat", "", "Archivos MAT (*.mat)")
        if not ruta:
            return
        try:
            nombre = os.path.splitext(os.path.basename(ruta))[0]
            self.mat_obj = ArchivoMAT(nombre, ruta)
            self.cmb_keys.clear(); self.cmb_keys.addItems(list(self.mat_obj.data.keys()))
            QMessageBox.information(self, "Cargado", "Archivo cargado; selecciona la llave con array")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _get_array(self):
        key = self.cmb_keys.currentText()
        if not key:
            QMessageBox.warning(self, "Llave", "Selecciona una llave")
            return None
        arr = self.mat_obj.data.get(key)
        if not isinstance(arr, np.ndarray):
            QMessageBox.warning(self, "No es arreglo", "La llave seleccionada no contiene un array. Intenta otra.")
            return None
        return arr

    def graficar_intervalo(self):
        if not self.mat_obj:
            QMessageBox.warning(self, "Archivo", "Carga un .mat primero")
            return
        arr = self._get_array();
        if arr is None: return
        ch_ini, ch_fin = self.sb_ch_ini.value(), self.sb_ch_fin.value()
        t_ini, t_fin = self.sb_t_ini.value(), self.sb_t_fin.value()

        # Validaciones
        if ch_ini > ch_fin or ch_fin >= arr.shape[0]:
            QMessageBox.warning(self, "Canales", "Rango de canales inválido")
            return
        fs = self.mat_obj.fs
        idx_ini, idx_fin = int(t_ini*fs), int(t_fin*fs)
        if idx_ini >= idx_fin or idx_fin > arr.shape[1]:
            QMessageBox.warning(self, "Tiempo", "Intervalo de tiempo inválido")
            return

        # Graficar
        self.fig.clf(); ax = self.fig.add_subplot(111)
        t = np.arange(idx_ini, idx_fin)/fs
        for ch in range(ch_ini, ch_fin+1):
            ax.plot(t, arr[ch, idx_ini:idx_fin], label=f"Canal {ch}")
        ax.set_xlabel("Tiempo (s)"); ax.set_ylabel("Amplitud")
        ax.set_title(f"Señales {ch_ini}-{ch_fin} | {t_ini}-{t_fin}s | llave '{self.cmb_keys.currentText()}'")
        ax.legend(); self.canvas.draw()
        
        try:
            t, datos = self.mat_obj.extraer_intervalo(ch_ini, ch_fin, t_ini, t_fin)
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
            return

        self.fig.clf()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor('white')
        ax.grid(True, linestyle='--', alpha=0.3)

        colores = ['blue', 'green', 'orange', 'purple', 'red', 'cyan', 'magenta', 'black']

        for i in range(datos.shape[0]):
            color = colores[i % len(colores)]
            ax.plot(t, datos[i], label=f"Canal {ch_ini + i}", linewidth=1.8, color=color)

        ax.set_xlabel("Tiempo (s)", fontsize=10)
        ax.set_ylabel("Amplitud", fontsize=10)
        ax.set_title(f"Canales {ch_ini}-{ch_fin} | {t_ini}–{t_fin}s", fontsize=11)
        ax.legend(loc="upper right", fontsize=8)
        self.fig.tight_layout()
        self.canvas.draw()
    def promedio_eje1(self):
        """Calcula promedio a lo largo del eje 1 y lo muestra como gráfico tipo stem."""
        if not self.mat_obj:
            QMessageBox.warning(self, "Archivo", "Carga un .mat primero")
            return

        arr = self._get_array()
        if arr is None:
            return

        # Convertir a 2D si es 3D tomando una época
        if arr.ndim == 3:
            arr = arr[:, :, 0]

        if arr.ndim != 2:
            QMessageBox.warning(self, "Dimensión", "La matriz debe ser 2D para este promedio")
            return

        if arr.shape[0] <= arr.shape[1]:
            prom = np.mean(arr, axis=1)
            x = np.arange(arr.shape[0])
        else:
            prom = np.mean(arr, axis=0)
            x = np.arange(arr.shape[1])

        self.fig.clf()
        ax = self.fig.add_subplot(111)
        ax.stem(x, prom, basefmt=" ")
        ax.set_xlabel("Índice de canal", fontsize=10)
        ax.set_ylabel("Promedio", fontsize=10)
        ax.set_title(f"Promedio por canal • llave '{self.cmb_keys.currentText()}'", fontsize=11)
        ax.grid(True, linestyle='--', alpha=0.3)
        self.fig.subplots_adjust(top=0.88, bottom=0.12, left=0.12, right=0.95, hspace=0.4)
        self.canvas.draw()

        QMessageBox.information(self, "Promedio", "Promedio eje 1 calculado y graficado.")

        print("Forma de la matriz seleccionada:", arr.shape)