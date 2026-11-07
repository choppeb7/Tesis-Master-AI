"""
PIPELINE 04 - PERFIL MATEMATICO DE LOS CLUSTERS
==============================================

Objetivo:
    Asociar cada articulo con el cluster asignado por K-Means y describir
    las caracteristicas matematicas de los grupos en sus unidades originales.

Entradas:
    df_input: DataFrame de la hoja 'cluster_input'. Contiene codigo_articulo
              y las variables matematicas ORIGINALES seleccionadas en P03.
    etiquetas: array de enteros devuelto por entrenar_modelo_final().

Flujo:
    1. crear_dataframe_clusterizado(df_input, etiquetas)
    2. generar_perfiles_clusters(df_clusterizado)

Importante:
    - NO se realiza ningun escalado ni transformacion inversa.
    - NO se vuelve a entrenar K-Means.
    - Las etiquetas se asignan por posicion: las filas deben conservar
      el mismo orden usado para entrenar el modelo.
    - NO se lee ni modifica 'eda_completo'.
    - NO se guardan archivos; main_forecast_clustering.py los exportara.
"""

import numpy as np
import pandas as pd

from . import clustering_config as cfg

# ============================================================
# 1. CONSOLIDAR ARTICULOS, VARIABLES Y ETIQUETAS
# ============================================================

def crear_dataframe_clusterizado(df_input, etiquetas):
    """Agrega a df_input el cluster de cada articulo, sin alterar los datos originales.

    Devuelve un DataFrame con:
        codigo_articulo + variables originales + cluster_kmeans_final
    """

    # A. Validaciones esenciales de la entrada.
    if not isinstance(df_input, pd.DataFrame) or df_input.empty:
        raise ValueError("df_input debe ser un DataFrame no vacio.")

    if df_input.columns.duplicated().any():
        raise ValueError("df_input tiene columnas duplicadas.")

    if cfg.COLUMNA_ID not in df_input.columns:
        raise ValueError(f"Falta la columna '{cfg.COLUMNA_ID}'.")

    if cfg.COLUMNA_CLUSTER in df_input.columns:
        raise ValueError("df_input ya contiene una columna de cluster.")

    # K-Means devuelve un array con una etiqueta por fila de entrenamiento.
    etiquetas = np.asarray(etiquetas)

    if etiquetas.ndim != 1 or len(etiquetas) != len(df_input):
        raise ValueError("Debe existir exactamente una etiqueta por articulo.")

    if not np.issubdtype(etiquetas.dtype, np.integer):
        raise ValueError("Las etiquetas deben ser numeros enteros.")

    if np.any(etiquetas < 0):
        raise ValueError("Las etiquetas no pueden ser negativas.")

    # B. Preparar una copia con indices consecutivos.
    # Nunca modificamos el DataFrame original.
    df_clusterizado = df_input.reset_index(drop=True).copy()

    # C. Agregar la etiqueta a la misma posicion del articulo.
    # Esto exige conservar el orden utilizado al entrenar K-Means.
    df_clusterizado[cfg.COLUMNA_CLUSTER] = etiquetas

    return df_clusterizado


# ============================================================
# 2. INTERPRETAR LOS CLUSTERS CON DATOS ORIGINALES
# ============================================================

def generar_perfiles_clusters(df_clusterizado, n_variables_destacadas=3):
    """Calcula cinco tablas para interpretar matematicamente los clusters.

    Devuelve:
        df_cluster_tamanos
        df_cluster_estadisticas
        df_cluster_comparativo
        df_cluster_perfiles
        df_articulos_clusterizados (con variables originales y cluster)
    """

     # A. Validar solo la estructura que necesitamos para el profiling.
    if not isinstance(df_clusterizado, pd.DataFrame) or df_clusterizado.empty:
        raise ValueError("df_clusterizado debe ser un DataFrame no vacio.")

    if not isinstance(n_variables_destacadas, int) or n_variables_destacadas < 1:
        raise ValueError("n_variables_destacadas debe ser un entero positivo.")

    if df_clusterizado.columns.duplicated().any():
        raise ValueError("df_clusterizado tiene columnas duplicadas.")

    nombre_cluster = cfg.COLUMNA_CLUSTER
    columna_id = cfg.COLUMNA_ID

    if columna_id not in df_clusterizado.columns or nombre_cluster not in df_clusterizado.columns:
        raise ValueError("Falta el codigo del articulo o la columna del cluster.")

    # Identificador unico: necesario para exportar y cruzar luego con df_eda.
    codigos = df_clusterizado[columna_id].astype("string").str.strip()
    if codigos.isna().any() or codigos.eq("").any() or codigos.duplicated().any():
        raise ValueError("Hay codigos de articulo vacios o duplicados.")

        # Separar los nombres de las variables; ninguna cantidad esta fijada.
    variables = [
        columna for columna in df_clusterizado.columns
        if columna not in [columna_id, nombre_cluster]
    ]
    if not variables:
        raise ValueError("No se encontraron variables matematicas para analizar.")

    # Los valores deben seguir siendo los originales y ser numericos.
    try:
        X_original = df_clusterizado[variables].astype(float)
    except (TypeError, ValueError) as error:
        raise ValueError("Las variables matematicas deben ser numericas.") from error

    if not np.isfinite(X_original.to_numpy()).all():
        raise ValueError("Hay valores nulos o infinitos en las variables matematicas.")

    etiquetas = df_clusterizado[nombre_cluster]
    if etiquetas.isna().any() or len(etiquetas.unique()) < 2:
        raise ValueError("Se requieren al menos dos clusters validos.")

    n_articulos = len(df_clusterizado)

    # Copia de trabajo: variables originales + identificador del cluster.
    datos = X_original.copy()
    datos[nombre_cluster] = etiquetas.to_numpy()

    # B. Cantidad y porcentaje de articulos por cluster.
    df_cluster_tamanos = (
        datos.groupby(nombre_cluster)
        .size()
        .reset_index(name="n_articulos")
    )
    df_cluster_tamanos["porcentaje_articulos"] = (
        100 * df_cluster_tamanos["n_articulos"] / n_articulos
    )
     # C. Estadisticas descriptivas por cluster y variable original.
    registros = []

    for cluster, grupo in datos.groupby(nombre_cluster):
        for variable in variables:
            valores = grupo[variable]

            registros.append({
                nombre_cluster: int(cluster),
                "variable": variable,
                "n_articulos": len(valores),
                "media": float(valores.mean()),
                "mediana": float(valores.median()),
                "desviacion_std": float(valores.std(ddof=0)),
                "minimo": float(valores.min()),
                "q1": float(valores.quantile(0.25)),
                "q3": float(valores.quantile(0.75)),
                "maximo": float(valores.max()),
                "porcentaje_ceros": float(100 * valores.eq(0).mean()),
            })

    df_cluster_estadisticas = pd.DataFrame(registros)

    # D. Comparar la media de cada cluster con la media general.
    # Dividir entre la desviacion estandar GENERAL permite comparar
    # diferencias de variables que tienen unidades muy distintas.

    