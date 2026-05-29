import pandas as pd
from pathlib import Path


# ============================================================
# CONFIGURACIÓN DE ARCHIVOS
# ============================================================

archivo_entrada = Path("../Datos/articulos_siemens_con_ventas_2024_2026.csv")
archivo_parametrizacion = Path("../Datos/parametrizacion_ciclo_vida.xlsx")
archivo_salida = Path("../Datos/articulos_siemens_con_ciclo_vida.csv")


# ============================================================
# CARGAR DATAFRAME PRINCIPAL
# ============================================================

df = pd.read_csv(
    archivo_entrada,
    sep=";",
    encoding="utf-8-sig"
)


# ============================================================
# COLUMNAS BASE DE CLASIFICACIÓN
# ============================================================

columnas_clasificacion = [
    "Categoría",
    "Subcategoría",
    "Tipo"
]


# ============================================================
# VALIDAR QUE EXISTAN LAS COLUMNAS NECESARIAS
# ============================================================

columnas_faltantes = [
    col for col in columnas_clasificacion
    if col not in df.columns
]

if columnas_faltantes:
    raise ValueError(
        f"Faltan columnas de clasificación en el archivo base: {columnas_faltantes}"
    )


# ============================================================
# CREAR ARCHIVO DE PARAMETRIZACIÓN SI NO EXISTE
# ============================================================
# Este archivo se llena manualmente con el ciclo de vida promedio
# por combinación de Categoría CI + Subcategoría CI + Tipo CI.

if not archivo_parametrizacion.exists():

    df_param = (
        df[columnas_clasificacion]
        .drop_duplicates()
        .sort_values(columnas_clasificacion)
        .reset_index(drop=True)
    )

    df_param["U_Ciclo_Vida"] = pd.NA

    df_param.to_excel(
        archivo_parametrizacion,
        index=False
    )

    print("Archivo de parametrización generado:")
    print(archivo_parametrizacion)
    print("Completa la columna U_Ciclo_Vida en meses y vuelve a ejecutar el script.")

else:

    # ========================================================
    # CARGAR PARAMETRIZACIÓN YA COMPLETADA
    # ========================================================

    df_param = pd.read_excel(archivo_parametrizacion)

    columnas_param_requeridas = columnas_clasificacion + ["U_Ciclo_Vida"]

    columnas_faltantes_param = [
        col for col in columnas_param_requeridas
        if col not in df_param.columns
    ]

    if columnas_faltantes_param:
        raise ValueError(
            f"Faltan columnas en el archivo de parametrización: {columnas_faltantes_param}"
        )


    # ========================================================
    # CRUZAR CICLO DE VIDA CONTRA DATAFRAME PRINCIPAL
    # ========================================================

    # Si ya existe U_Ciclo_Vida en el dataframe principal,
    # la eliminamos para evitar duplicidad antes del merge.
    if "U_Ciclo_Vida" in df.columns:
        df = df.drop(columns=["U_Ciclo_Vida"])

    df = df.merge(
        df_param[columnas_param_requeridas],
        on=columnas_clasificacion,
        how="left"
    )


    # ========================================================
    # EXPORTAR DATAFRAME FINAL
    # ========================================================

    df.to_csv(
        archivo_salida,
        index=False,
        encoding="utf-8-sig",
        sep=";"
    )

    print("Archivo final generado:")
    print(archivo_salida)