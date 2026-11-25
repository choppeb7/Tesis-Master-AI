import pandas as pd

def cargar_matriz_ventas(ruta_excel):
    df = pd.read_excel(ruta_excel)
    return df