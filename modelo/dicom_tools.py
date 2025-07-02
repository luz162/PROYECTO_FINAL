# modelo/dicom_tools.py
import os, shutil, dicom2nifti

def convertir_dicom_a_nifti(carpeta_dicom: str, salida_dir: str) -> str:
    """
    Convierte una carpeta con slices DICOM a un único .nii.gz
    Devuelve la ruta al archivo NIfTI.
    """
    if not os.path.isdir(salida_dir):
        os.makedirs(salida_dir, exist_ok=True)

    nombre = os.path.basename(os.path.normpath(carpeta_dicom))
    ruta_sal = os.path.join(salida_dir, f"{nombre}.nii.gz")
    dicom2nifti.convert_directory(carpeta_dicom, salida_dir, compression=True, reorient=True)
    # la lib guarda con mismo nombre
    return ruta_sal
