from PyQt5.QtWidgets import QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import os
class VistaLogin(QWidget):
    def __init__(self, controlador):
        super().__init__()
        from estilos import APP_STYLESHEET  
        self.setStyleSheet(APP_STYLESHEET)
        self.controlador = controlador
        self.setWindowTitle("Ingreso al Sistema")
        self._construir_ui()

    def _construir_ui(self):
        layout = QVBoxLayout()

        # Ruta del logo
        ruta_logo = os.path.join(os.path.dirname(__file__), "..", "logo.jpg")
        logo = QLabel()
        pixmap = QPixmap(ruta_logo).scaled(300,300, Qt.KeepAspectRatio)
        logo.setPixmap(pixmap)
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)

         # Campos de login
        self.lbl_user = QLabel("Usuario:")
        self.txt_user = QLineEdit()
        self.lbl_pass = QLabel("Contraseña:")
        self.txt_pass = QLineEdit()
        self.txt_pass.setEchoMode(QLineEdit.Password)
        self.btn_login = QPushButton("Ingresar")
        self.btn_login.clicked.connect(self._login)
        self.btn_registro = QPushButton("Registrarse")
        self.btn_registro.clicked.connect(self.controlador.mostrar_registro)
        layout.addWidget(self.lbl_user)
        layout.addWidget(self.txt_user)
        layout.addWidget(self.lbl_pass)
        layout.addWidget(self.txt_pass)
        layout.addWidget(self.btn_login)
        layout.addWidget(self.btn_registro)
        self.setLayout(layout)

    def _login(self):
        usuario = self.txt_user.text().strip()
        contrasena = self.txt_pass.text().strip()
        if not usuario or not contrasena:
            QMessageBox.warning(self, "Datos faltantes", "Completa usuario y contraseña")
            return
        self.controlador.login(usuario, contrasena)

    def mostrar_error(self, msg):
        QMessageBox.critical(self, "Error", msg)