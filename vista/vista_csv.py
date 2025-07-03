# ====================== V I S T A   C S V ==============================
from PyQt5.QtWidgets import (QWidget, QLabel, QPushButton, QFileDialog, QVBoxLayout, QHBoxLayout,
                             QMessageBox, QTableWidget, QTableWidgetItem, QComboBox)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas
from matplotlib.figure import Figure
import pandas as pd
from modelo.clases_señales import ArchivoCSV

class VistaCSV(QWidget):
    """Carga CSV, muestra tabla y permite scatter entre columnas."""
    def __init__(self, controlador):
        super().__init__()
        from estilos import APP_STYLESHEET  
        self.setStyleSheet(APP_STYLESHEET)
        self.controlador = controlador
        self.setWindowTitle("Exploración CSV")
        self.archivo_csv = ArchivoCSV()
        self._build_ui()

    def _build_ui(self):
        v = QVBoxLayout(self)

        btn_cargar = QPushButton("Cargar CSV"); 
        btn_cargar.clicked.connect(self.cargar_csv)
        v.addWidget(btn_cargar)

        # Combos para columnas X e Y
        h_cols = QHBoxLayout()
        self.cmb_x = QComboBox(); self.cmb_y = QComboBox()
        h_cols.addWidget(QLabel("Eje X:")); h_cols.addWidget(self.cmb_x)
        h_cols.addWidget(QLabel("Eje Y:")); h_cols.addWidget(self.cmb_y)
        v.addLayout(h_cols)

        # Botón scatter
        btn_scatter = QPushButton("Graficar Scatter"); btn_scatter.clicked.connect(self.graficar_scatter)
        v.addWidget(btn_scatter)

        # Tabla de datos
        self.tabla = QTableWidget(); v.addWidget(self.tabla)

        # Canvas matplotlib
        self.fig = Figure(figsize=(6,4)); 
        self.canvas = Canvas(self.fig)
        v.addWidget(self.canvas)

    # ------------------------------------------------------------------
    def cargar_csv(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Selecciona CSV", "", "CSV (*.csv)")
        if not ruta: return
        try:
            self.df = pd.read_csv(ruta)
            self.cmb_x.clear(); self.cmb_y.clear();
            self.cmb_x.addItems(self.df.columns); 
            self.cmb_y.addItems(self.df.columns)
            self._poblar_tabla()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _poblar_tabla(self):
        self.tabla.setRowCount(len(self.df)); 
        self.tabla.setColumnCount(len(self.df.columns))
        self.tabla.setHorizontalHeaderLabels(self.df.columns)
        for r in range(len(self.df)):
            for c, col in enumerate(self.df.columns):
                self.tabla.setItem(r, c, QTableWidgetItem(str(self.df.iloc[r, c])))

    def graficar_scatter(self):
        if self.df is None:
            QMessageBox.warning(self, "Archivo", "Carga un CSV primero")
            return
        col_x, col_y = self.cmb_x.currentText(), self.cmb_y.currentText()
        if col_x == col_y:
            QMessageBox.warning(self, "Columnas", "Elige columnas distintas para scatter")
            return
        self.fig.clf(); ax = self.fig.add_subplot(111)
        ax.scatter(self.df[col_x], self.df[col_y])
        ax.set_xlabel(col_x); ax.set_ylabel(col_y)
        ax.set_title(f"Scatter: {col_x} vs {col_y}")
        self.canvas.draw()
