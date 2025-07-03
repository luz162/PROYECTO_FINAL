"""Controlador principal del sistema: maneja autenticación, vistas y operaciones de alto nivel
Incluye función para cargar carpetas DICOM completas y generar el volumen 3D que se guarda
en el paciente activo.
"""

from modelo.base_datos import get_conn
import os
import numpy as np
import pydicom
from PyQt5.QtWidgets import QFileDialog, QMessageBox

# Modelos
from modelo.modelo_usuarios import ModeloUsuarios
from modelo.modelo_pacientes import ModeloPacientes
from modelo.clases_imagenes import Paciente

# Vistas
from vista.vista_login import VistaLogin
from vista.vista_menu import VistaMenu
from vista.vista_imagen_simple import VistaImagenSimple
from vista.vista_nifti import VistaNifti
from vista.vista_csv import VistaCSV
from vista.vista_mat import VistaMAT
from vista.vista_tabla_pacientes import VistaTablaPacientes
from vista.vista_registro import VistaRegistro 

# Vista DICOM la importamos dentro del método


class ControladorPrincipal:
    """Coordinador maestro del flujo de la aplicación  MVC."""

    def __init__(self):
        # Conexión y modelos
        self.conn = get_conn()
        self.modelo_usuarios = ModeloUsuarios(self.conn)
        self.modelo_pacientes = ModeloPacientes(self.conn)

        # Estado
        self.usuario_actual = None
        self.paciente_actual = None  #  atributo para el volumen 

        # Lanzar la primera vista (login)
        self.vista_login = VistaLogin(self)
        self.vista_login.show()

    # -------------------------------------------------------------------------
    # AUTENTICACIÓN
    # -------------------------------------------------------------------------
    def login(self, username: str, password: str) -> bool:
        usuario = self.modelo_usuarios.verificar_usuario(username, password)
        if usuario:
            self.usuario_actual = usuario
            self.vista_login.close()
            self.mostrar_menu_principal(usuario["rol"])
            return True
        return False

    def registrar_usuario(self, username: str, password: str, rol: str) -> bool:
        rol = rol.lower()
        if rol == "imagenes":
            rol_db = "imagen"
        elif rol == "señales":
            rol_db = "senal"
        else:
            rol_db = rol
        return self.modelo_usuarios.insertar_usuario(username, password, rol_db)

    def mostrar_registro(self):
        self.vista_registro = VistaRegistro(self)
        self.vista_registro.show()

    def logout(self):
        self.usuario_actual = None
        self.paciente_actual = None
        self.vista_menu.close()
        self.vista_login = VistaLogin(self)
        self.vista_login.show()

    # -------------------------------------------------------------------------
    # MENÚ PRINCIPAL
    # -------------------------------------------------------------------------
    def mostrar_menu_principal(self, rol: str):
        self.vista_menu = VistaMenu(self, rol)
        self.vista_menu.show()

    # -------------------------------------------------------------------------
    # VISTAS – IMÁGENES
    # -------------------------------------------------------------------------
    def mostrar_dicom(self):
        from vista.vista_dicom3d import VistaDICOM3D  
        self.vista_dicom = VistaDICOM3D(self)
        self.vista_dicom.show()

    def mostrar_simple(self):
        self.vista_simple = VistaImagenSimple(self)
        self.vista_simple.show()

    def mostrar_nifti(self):
        self.vista_nifti = VistaNifti(self)
        self.vista_nifti.show()

    # -------------------------------------------------------------------------
    # VISTAS – SEÑALES
    # -------------------------------------------------------------------------
    def mostrar_csv(self):
        self.vista_csv = VistaCSV(self)
        self.vista_csv.show()

    def mostrar_mat(self):
        self.vista_mat = VistaMAT(self)
        self.vista_mat.show()

    # -------------------------------------------------------------------------
    # PACIENTES
    # -------------------------------------------------------------------------
    def mostrar_tabla_pacientes(self):
        self.vista_tabla = VistaTablaPacientes(self)
        self.vista_tabla.show()

    def obtener_pacientes(self):
        return self.modelo_pacientes.obtener_todos()
    

    def registrar_paciente_dicom(self, carpeta_dicom, ruta_nifti, diagnostico=""):
        self.modelo_pacientes.insertar_dicom(carpeta_dicom, ruta_nifti, diagnostico)
        if hasattr(self, "vista_tabla") and self.vista_tabla.isVisible():
            self.vista_tabla.actualizar_tabla()
    # =====================================================================
    #  CARGA COMPLETA DE UNA CARPETA DICOM
    # =====================================================================
    def cargar_carpeta_dicom(self):
        """Abre un diálogo para que el usuario elija la carpeta DICOM y genera
        el volumen 3D que queda disponible en `self.paciente_actual`. Si la
        operación es exitosa, muestra una notificación y actualiza la vista
        activa (VistaDICOM3D, si está abierta)."""

        carpeta = QFileDialog.getExistingDirectory(None, "Selecciona carpeta DICOM")
        if not carpeta:
            return  # el usuario canceló

        try:
            volumen = self._cargar_volumen_dicom(carpeta)
            nombre_paciente = os.path.basename(carpeta)

            # Crear y almacenar el paciente activo
            self.paciente_actual = Paciente(nombre_paciente, 0, "N/A", volumen)

            QMessageBox.information(None, "Éxito", f"Volumen DICOM cargado para '{nombre_paciente}'")

            # Si la vista DICOM ya está abierta, refrescamos la información
            if hasattr(self, "vista_dicom") and self.vista_dicom.isVisible():
                self.vista_dicom.refrescar_volumen()

        except Exception as exc:
            QMessageBox.critical(None, "Error al cargar DICOM", str(exc))

    # ---------------------------------------------------------------------
    # construcción del volumen 3D a partir de archivos DICOM
    # ---------------------------------------------------------------------
    def _cargar_volumen_dicom(self, ruta_carpeta):
        import pydicom
        import numpy as np
        import os

        archivos = [f for f in os.listdir(ruta_carpeta) if f.lower().endswith('.dcm')]
        rutas = [os.path.join(ruta_carpeta, f) for f in archivos]

        slices = []
        for path in rutas:
            ds = pydicom.dcmread(path)
            pixel_array = ds.pixel_array
            instancia = getattr(ds, 'InstanceNumber', len(slices))
            slices.append((instancia, pixel_array))

        slices.sort(key=lambda x: x[0])

        volumen = np.stack([s[1] for s in slices], axis=0)
        print("Volumen cargado con shape:", volumen.shape)
        return volumen
