import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "app.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    crear_tablas(conn)
    return conn

def crear_tablas(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT NOT NULL
        );
    """)
    conn.execute("""
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
    conn.commit()
