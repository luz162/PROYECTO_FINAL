# ---------------- vista/vista_registro.py ----------------
from PyQt5.QtWidgets import QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox, QComboBox

class VistaRegistro(QWidget):
    def __init__(self, controlador):
        super().__init__()
        from estilos import APP_STYLESHEET  
        self.setStyleSheet(APP_STYLESHEET)
        self.controlador = controlador
        self.setWindowTitle("Registro de Usuario")
        self._construir_ui()

    def _construir_ui(self):
        layout = QVBoxLayout()
        self.lbl_user = QLabel("Usuario:")
        self.txt_user = QLineEdit()
        self.lbl_pass = QLabel("Contraseña:")
        self.txt_pass = QLineEdit()
        self.lbl_rol = QLabel("Rol:")
        self.cmb_rol = QComboBox()
        self.cmb_rol.addItems(["Imagenes", "Señales"])
        self.btn_registrar = QPushButton("Registrar")
        self.btn_registrar.clicked.connect(self._registrar)
        layout.addWidget(self.lbl_user)
        layout.addWidget(self.txt_user)
        layout.addWidget(self.lbl_pass)
        layout.addWidget(self.txt_pass)
        layout.addWidget(self.lbl_rol)
        layout.addWidget(self.cmb_rol)
        layout.addWidget(self.btn_registrar)
        self.setLayout(layout)

    def _registrar(self):
        user = self.txt_user.text().strip()
        passwd = self.txt_pass.text().strip()
        rol = self.cmb_rol.currentText()

        if not user or not passwd:
            QMessageBox.warning(self, "Campos vacíos", "Usuario y contraseña requeridos")
            return

        exito = self.controlador.registrar_usuario(user, passwd, rol)
        if exito:
            QMessageBox.information(self, "Éxito", "Usuario creado correctamente.")
            self.close()
        else:
            QMessageBox.warning(self, "Nombre en uso",
                                "Ese nombre de usuario ya existe. Elige otro.")