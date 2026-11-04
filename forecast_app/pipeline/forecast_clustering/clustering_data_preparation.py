"""
PIPELINE 04 - PREPARACIÓN DE DATOS PARA CLUSTERING
================================================
Lee el único Excel consolidado que entrega el Pipeline 03.

Entradas:
    - cluster_input: codigo_articulo + variables seleccionadas por correlación.
    - eda_completo: catálogo, estadísticas y clasificaciones para interpretar clusters.

Responsabilidad de este módulo:
    - Detectar dinámicamente las variables de clustering.
    - Validar identificadores, valores numéricos y coherencia entre hojas.
    - Entregar datos alineados al siguiente módulo de preprocesamiento.

NO realiza imputación, winsorización, transformación, escalado ni clustering.
"""

from pathlib import Path

import numpy as np 
import pandas as pd

from . import clustering_config as cfg

#====================================
# 1. VALIDACIONES AUXILIARES
#====================================

def validar_identificadores(df,nombre_hoja, columna_id ):
    if df.empty: 
        raise ValueError(f"la hoja {nombre_hoja} está vacía")

    if columna_id not in df.columns: 
        raise ValueError(
            f"No se encontró {columna_id} en la hoja {nombre_hoja}"
        )

    df[columna_id]=df[columna_id].astype("string").str.strip()

    if df[columna_id].isna().any() or df[columna_id].eq("").any():
        raise ValueError(
            f"existen códigos de artículos nulos o vacios en {nombre_hoja}"
        )

    if df[columna_id].duplicated().any():
        ejemplos = df.loc[
            df[columna_id].duplicated(keep=False), columna_id
        ].head(5).tolist()
        raise ValueError(
            f"Existen códigos duplicados en '{nombre_hoja}': {ejemplos}"
        )
    
# ============================================================
# 2. PREPARAR MATRIZ NUMÉRICA
# ============================================================

def preparar_matriz_numerica(df_input, variables, columna_id):
    """Valida variables seleccionadas y devuelve X sin imputar ni transformar."""

    # Convertir valores numéricos representados como texto, pero sin
    # sustituir silenciosamente valores faltantes o textos inválidos.

    X=df_input[variables].apply(pd.to_numeric, errors="coerce")

    valores_invalidos= X.isna()

    if valores_invalidos.any().any():

        filas, columnas=np.where(
            valores_invalidos.to_numpy()
            )

        ejemplos = [
        (
            f"{df_input.iloc[i][columna_id]} / "
            f"{X.columns[j]} = "
            f"{df_input.iloc[i][X.columns[j]]!r}"
        )
        for i, j in zip(filas[:8], columnas[:8])
        ]
        cantidad_invalidos=int(valores_invalidos.to_numpy(),sum())

        raise ValueError( 
            "Se encontraron valores nulos o no numéricos "
            "en las variables seleccionadas para clustering. "
            "No se reemplazarán automáticamente por cero. "
            f"Cantidad de valores inválidos: {len(cantidad_invalidos)}. "
            f"Ejemplos: {ejemplos}"
        )
    
    # --------------------------------------------------------
    # 3. Validar valores infinitos
    # --------------------------------------------------------

    valores_no_finitos=~np.isinfinite(
        X.to_numpy(dtype=float)
    )

    if valores_no_finitos.any():

        posiciones=np.argwhere(
            valores_no_finitos
        )

        ejemplos= [
            (
                f"{df_input.iloc[i][columna_id]}/"
                f"{X.columns[j]}"
            )
            for i, j in posiciones [:8]
        ]

        raise ValueError("Se encontraron valores infinitos en las "
                         f"variables de clustering. Ejemplos {ejemplos}")

    # --------------------------------------------------------
    # 4. Comprobar variables constantes
    # --------------------------------------------------------

    variables_constantes=[
        variable
        for variable in variables
        if X[variable].nunique() <=1
    ]

    if variables_constantes:
        raise ValueError(
            "Existen variables sin variacion, que deberían "
            "haberse descartado durante el pipeline 03:"
            f"{variables_constantes}"
        )
    return X.astype(float)

# ============================================================
# 3. FUNCIÓN PRINCIPAL - CARGA DE DATOS
# ============================================================

def cargar_dataset_cluster(
        ruta_input=cfg.RUTA_INPUT_CLUSTER_READY,
        columna_id=cfg.COLUMNA_ID
):
    """
    Carga y valida el dataset oficial del Pipeline 04.

    Devuelve:
        df_input: artículos y variables seleccionadas.
        df_eda: información completa de los artículos.
        X: matriz numérica original.
        variables: nombres de las variables seleccionadas.
    """
    ruta_input=Path(ruta_input)

    # --------------------------------------------------------
    # 1. Comprobar archivo de entrada
    # --------------------------------------------------------

    if not ruta_input.is_file():
        raise FileNotFoundError(
            "No se encontró el archivo de entrada:" 
            f"{ruta_input}"
        )

    # --------------------------------------------------------
    # 2. Leer las hojas del Excel consolidado
    # --------------------------------------------------------

    with pd.ExcelFile(ruta_input) as libro: 

        hojas_requeridas=[
            cfg.HOJA_INPUT_CLUSTER,
            cfg.HOJA_EDA_COMPLETO
        ]

        hojas_faltantes=[
            hoja
            for hoja in hojas_requeridas
            if hoja not in libro.sheet_names
        ]

        if hojas_faltantes:
            raise ValueError(
                f"Faltan hojas en el Excel: {hojas_faltantes}"
            )
        
        df_input= pd.read_excel(
            libro, 
            sheet_name=cfg.HOJA_INPUT_CLUSTER,
            dtype={columna_id: str}
        )
        df_eda= pd.read_excel(
            libro,
            sheet_name=cfg.HOJA_EDA_COMPLETO,
            dtype={columna_id:str}
        )
    # --------------------------------------------------------
    # 3. Validar identificadores
    # --------------------------------------------------------

    validar_identificadores(
        df=df_input,
        nombre_hoja=cfg.HOJA_INPUT_CLUSTER,
        columna_id=columna_id
    )

    validar_identificadores(
        df=df_eda,
        nombre_hoja=cfg.HOJA_EDA_COMPLETO,
        columna_id=columna_id
    )
    # --------------------------------------------------------
    # 4. Obtener variables dinámicamente
    # --------------------------------------------------------

    variables = [
        columna
        for columna in df_input.columns
        if columna != columna_id
    ]

    if len(variables) < 2:
        raise ValueError(
            "Se necesitan al menos dos variables "
            "seleccionadas para realizar clustering."
        )

    # --------------------------------------------------------
    # 5. Preparar matriz numérica X
    # --------------------------------------------------------
    
    X = preparar_matriz_numerica(
            df_input=df_input,
            variables=variables,
            columna_id=columna_id
        )
    
    df_input[variables] = X

    # --------------------------------------------------------
    # 6. Validar artículos entre ambas hojas
    # --------------------------------------------------------

    codigos_input = set(df_input[columna_id])
    codigos_eda = set(df_eda[columna_id])

    if codigos_input != codigos_eda:

        faltantes = codigos_input - codigos_eda
        sobrantes = codigos_eda - codigos_input

        raise ValueError(
            "Los artículos no coinciden entre "
            "'cluster_input' y 'eda_completo'. "
            f"Faltantes en EDA: {list(faltantes)[:5]}. "
            f"Sobrantes en EDA: {list(sobrantes)[:5]}"
        )

    # --------------------------------------------------------
    # 7. Alinear información de EDA por artículo
    # --------------------------------------------------------

    df_eda = df_input[[columna_id]].merge(
        df_eda,
        on=columna_id,
        how="left",
        validate="one_to_one"
    )

    #

    # --------------------------------------------------------
    # 9. Resumen de preparación
    # --------------------------------------------------------

    print(
        "\nPreparación de datos del Pipeline 04 "
        "finalizada correctamente."
    )

    print(f"Archivo: {ruta_input.name}")
    print(f"Cantidad de artículos: {len(df_input)}")
    print(f"Variables seleccionadas: {len(variables)}")

    print("\nVariables utilizadas en clustering:")
    for variable in variables:
        print(f" - {variable}")

    return df_input, df_eda, X, variables

