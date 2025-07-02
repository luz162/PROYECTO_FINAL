import nibabel as nib
import numpy as np

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
