# ---------------- main.py ----------------
import sys
from PyQt5.QtWidgets import QApplication

from controlador.controlador import ControladorPrincipal

if __name__ == "__main__":
  
    # 1. Lanzamos la GUI
    app = QApplication(sys.argv)
    controlador = ControladorPrincipal()
    controlador.vista_login.show()           
    sys.exit(app.exec())                  
