import sqlite3
from modelo.base_datos import get_conn
from sqlite3 import Connection

class ModeloUsuarios:
    def __init__(self, conn: Connection | None = None):
        self.conn = conn or get_conn()
        self._crear_tabla()

    # -- crea la tabla si no existe --------------------------------------
    def _crear_tabla(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                rol TEXT NOT NULL
            );
        """)
        self.conn.commit()

    # -- inserta usuario nuevo -------------------------------------------
    def insertar_usuario(self, username: str, password: str, rol: str) -> bool:
        try:
            self.conn.execute(
                "INSERT INTO usuarios (username, password, rol) VALUES (?,?,?)",
                (username, password, rol))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            # username duplicado (violación UNIQUE)
            return False
        except Exception as e:
            print(f"[ModeloUsuarios] Error insertando usuario: {e}")
            return False

    # -- verifica login ---------------------------------------------------
    def verificar_usuario(self, username: str, password: str):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT username, rol FROM usuarios WHERE username=? AND password=?",
            (username, password))
        fila = cur.fetchone()
        if fila:
            return {"usuario": fila[0], "rol": fila[1]}
        return None



