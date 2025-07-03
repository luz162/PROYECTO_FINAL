import os
import nibabel as nib
import numpy as np
import dicom2nifti
import dicom2nifti.convert_dicom

class ImagenNifti:
    def __init__(self, ruta_archivo):
        self.ruta = ruta_archivo
        self.objeto_nifti = nib.load(ruta_archivo)
        self.datos = self.objeto_nifti.get_fdata()
        self.metadatos = self.objeto_nifti.header

    def obtener_corte_axial(self, indice=None):
        if indice is None:
            indice = self.datos.shape[2] // 2
        return self.datos[:, :, indice]

    def obtener_corte_coronal(self, indice=None):
        if indice is None:
            indice = self.datos.shape[1] // 2
        return self.datos[:, indice, :]

    def obtener_corte_sagital(self, indice=None):
        if indice is None:
            indice = self.datos.shape[0] // 2
        return self.datos[indice, :, :]

    def obtener_info(self):
        return {
            "dimensiones": self.datos.shape,
            "espaciado_voxel": self.metadatos.get_zooms(),
            "tipo_dato": self.metadatos.get_data_dtype().name
        }

def convertir_dicom_a_nifti(carpeta_dicom: str, carpeta_salida: str) -> str:
    """
    Convierte una carpeta con archivos DICOM a un archivo .nii.gz usando dicom2nifti.
    Devuelve la ruta del archivo NIfTI generado.
    """
    if not os.path.isdir(carpeta_dicom):
        raise FileNotFoundError(f"No existe la carpeta DICOM: {carpeta_dicom}")

    if not os.path.exists(carpeta_salida):
        os.makedirs(carpeta_salida)

    nombre = os.path.basename(os.path.normpath(carpeta_dicom))
    ruta_salida = os.path.join(carpeta_salida, f"{nombre}.nii.gz")

    try:
        dicom2nifti.convert_dicom.dicom_series_to_nifti(carpeta_dicom, ruta_salida)
        return ruta_salida
    except Exception as e:
        raise Exception(f"Error al convertir DICOM a NIfTI: {e}")
