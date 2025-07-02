# Proyecto Final - Informática II (2025)

Este sistema permite el manejo de pacientes y análisis de imágenes médicas (DICOM, JPG/PNG) y señales (CSV, MAT), usando una interfaz gráfica desarrollada con PyQt5 bajo el patrón MVC.

## Estructura del Proyecto

- `controlador/`: Lógica principal de navegación y operaciones.
- `modelo/`: Clases de base de datos y procesamiento.
- `vista/`: Vistas PyQt5 separadas por tipo de análisis (DICOM, señales, imágenes,etc).
- `main.py`: Punto de entrada. Lanza la interfaz gráfica.
- `app.db`: Base de datos SQLite con usuarios y pacientes.
- `datos/`: Archivos `.mat` y `.csv` para pruebas.
- `DICOM/`: Archivos `.dcm`  para pruebas.
- `imagenes/`: Archivos `.png` y `.jpg` para pruebas.
- `estilos/`: Estilos de las vistas

## Requisitos

- Python 3.11+
- PyQt5
- pydicom
- numpy
- pandas
- matplotlib
- opencv-python

## Ejecución

```bash
python main.py
```

## Funcionalidades

- Login con roles (`imagenes`, `senales`)
- Carga de volúmenes DICOM y reconstrucción 3D
- Visualización de cortes axiales, sagitales y coronales
- Procesamiento de imágenes simples (filtros, binarización, morfología)
- Visualización y análisis de señales MAT y CSV
- Gestión de pacientes (registro, listado, volúmenes)

 ##                                                    MANUAL DEL USUARIO


1. Registro :
      Registrate con un  nombre de ususario y contraseña
      selecciona un rol(`imagenes`, `senales`)
      selecciona el boton registrar

2. Ingreso :        
      Ingresa tu nombre de ususario y contraseña 
      selecciona el boton ingresar

3. seleccion menu:
      selecciona el menu que deseas ejecutar .

4. Para cargar los archivos  ten encuenta :
      - `datos/`: Archivos `.mat` y `.csv` para pruebas.
      - `DICOM/`: Archivos `.dcm`  para pruebas.
      - `imagenes/`: Archivos `.png` y `.jpg` para pruebas.       

