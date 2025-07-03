# modelo/modelo_pacientes.py
import os, sqlite3, pydicom, dicom2nifti
from typing import List

class ModeloPacientes():
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self._crear_tabla()

    def _crear_tabla(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT,
            nombre TEXT,
            edad TEXT,
            sexo TEXT,
            study_date TEXT,
            diagnostico TEXT,
            ruta_dicom TEXT,
            ruta_nifti TEXT
        );
        """)
        self.conn.commit()

    # ---------- NUEVO ----------

    def insertar_dicom(self, carpeta_dicom: str, ruta_nifti: str, diagnostico=""):
        # Busca el primer archivo .dcm
        archivo = next(
            f for f in os.listdir(carpeta_dicom)
            if f.lower().endswith(".dcm")
        )
        ds = pydicom.dcmread(os.path.join(carpeta_dicom, archivo))

        #  Convierte TODO a str para  SQLite
        campos = {
            "patient_id" : str(getattr(ds, "PatientID",  "")),
            "nombre"     : str(getattr(ds, "PatientName", "")),   # PersonName → str
            "edad"       : str(getattr(ds, "PatientAge",  "")),
            "sexo"       : str(getattr(ds, "PatientSex",  "")),
            "study_date" : str(getattr(ds, "StudyDate",   "")),
            "ruta_dicom" : str(carpeta_dicom),
            "ruta_nifti" : str(ruta_nifti),
        }

        cols = ", ".join(campos.keys())
        vals = tuple(campos.values())          
        qs   = ", ".join("?"*len(campos))
        self.conn.execute(f"INSERT INTO pacientes ({cols}) VALUES ({qs})", vals)
        self.conn.commit()

    def obtener_todos(self) -> List[tuple]:
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id,patient_id, nombre, edad, sexo, study_date,ruta_dicom, ruta_nifti
                FROM pacientes
                ORDER BY id;
            """)
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"[ERROR obtener_todos] {e}")
            return []