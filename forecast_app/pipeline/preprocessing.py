import pandas as pd
import re

# =====================================================================================
# 1. Detectar columnas mensuales de venta & convertirlas a formato datetime 
# ======================================================================================

def obtener_columnas_venta_ordenadas(df):
    """
    Detecta columnas tipo venta_YYYY_MM las convierte a datetime (format="%Y_%m_%d") y las ordena cronológicamente.
    """

    patron = r"^venta_\d{4}_\d{2}$"

    columnas_venta = [
        col for col in df.columns
        if re.match(patron, str(col))
    ]

    columnas_venta = sorted(
        columnas_venta,
        key=lambda col: pd.to_datetime(
            col.replace("venta_", "") + "_01",
            format="%Y_%m_%d"
        )
    )

    return columnas_venta


# =====================================================================================
# 2. Convertir un string de fecha de venta a formato datetime fin de mes
# ======================================================================================

def convertir_columna_venta_a_fecha(columna):
    """
    Convierte una columna tipo venta_2024_01 a fecha fin de mes.
    """
    fecha = pd.to_datetime(
        columna.replace("venta_", "") + "_01",
        format="%Y_%m_%d"
    ) + pd.offsets.MonthEnd(0)

    return fecha



# ============================================================
# 3. Convertir matriz mensual a formato largo
# ============================================================

def convertir_matriz_a_formato_largo(df_ventas, columnas_venta):
    """
    Convierte la matriz mensual por artículo a formato largo:
    codigo_articulo | columna_venta | fecha_mes | venta_mensual
    """

    df_temp = df_ventas.copy()


    if "codigo_articulo" not in df_temp.columns:
        df_temp = df_temp.reset_index()

    columnas_id = [
        col for col in df_temp.columns
        if col not in columnas_venta
    ]
    #Si best_model columna esta presente incluirla


    df_long = df_temp.melt(
        id_vars=columnas_id,
        value_vars=columnas_venta,
        var_name="columna_venta",
        value_name="venta_mensual"
    )

    df_long["fecha_mes"] = df_long["columna_venta"].apply(
        convertir_columna_venta_a_fecha
    )

    df_long["venta_mensual"] = pd.to_numeric(
        df_long["venta_mensual"],
        errors="coerce"
    ).fillna(0)

   

    df_long = df_long.sort_values(
        by=["codigo_articulo", "fecha_mes"]
    ).reset_index(drop=True)

    return df_long

# =================================================================================
# 4. Preparar dataframe de inferencia y metadata por artículo
# =================================================================================

def preparar_formato_forecast_y_metadata(
    df_ventas,
    columna_codigo="codigo_articulo"
):
    """
    A partir de una matriz consolidada de artículos y ventas mensuales,
    genera:

    1. df_inferencia:
       DataFrame en formato StatsForecast:
       unique_id | ds | y

    2. df_metadata_articulos:
       DataFrame con una fila por artículo y toda la información
       no mensual.

    3. metadata_por_articulo:
       Diccionario clave-valor:
       unique_id -> información completa del artículo.

    4. mapa_fechas:
       DataFrame con equivalencia entre columnas de venta y fechas.

    Parámetros:
    - df_consolidado: dataframe matriz consolidada.
    - columna_codigo: nombre de la columna con el código del artículo.

    Retorna:
    - df_inferencia
    - df_metadata_articulos
    - metadata_por_articulo
    - mapa_fechas
    - columnas_venta
    """

    df_temp = df_ventas.copy()

    # ------------------------------------------------------------
    # Si codigo_articulo está como índice, lo regresamos a columna
    # ------------------------------------------------------------

    if columna_codigo not in df_temp.columns:
        if df_temp.index.name == columna_codigo:
            df_temp = df_temp.reset_index()
        else:
            raise ValueError(
                f"No se encontró la columna {columna_codigo} en el dataframe."
            )

    # ------------------------------------------------------------
    # Detectar columnas mensuales tipo venta_YYYY_MM
    # ------------------------------------------------------------

    patron_venta = r"^venta_\d{4}_\d{2}$"

    columnas_venta = [
        col for col in df_temp.columns
        if re.match(patron_venta, str(col))
    ]

    if len(columnas_venta) == 0:
        raise ValueError(
            "No se encontraron columnas mensuales con formato venta_YYYY_MM."
        )

    # Ordenar columnas de venta cronológicamente
    columnas_venta = sorted(
        columnas_venta,
        key=lambda col: convertir_columna_venta_a_fecha(col)
    )

    # ------------------------------------------------------------
    # Crear mapa de fechas
    # ------------------------------------------------------------

    mapa_fechas = pd.DataFrame({
        "columna_venta": columnas_venta,
        "ds": [
            convertir_columna_venta_a_fecha(col)
            for col in columnas_venta
        ]
    })

    # ------------------------------------------------------------
    # Separar metadata: todo lo que no sea columna mensual
    # ------------------------------------------------------------

    columnas_metadata = [
        col for col in df_temp.columns
        if col not in columnas_venta
    ]

    df_metadata_articulos = (
        df_temp[columnas_metadata]
        .drop_duplicates(subset=[columna_codigo])
        .copy()
    )

    # Renombrar código a unique_id para mantener estándar
    df_metadata_articulos = df_metadata_articulos.rename(columns={columna_codigo: "unique_id"})
    #)

    # Validar que haya una sola fila por artículo
    duplicados = df_metadata_articulos["unique_id"].duplicated().sum()

    if duplicados > 0:
        raise ValueError(
            f"Hay {duplicados} códigos duplicados en metadata. "
            "Revisar antes de continuar."
        )

    # ------------------------------------------------------------
    # Crear diccionario clave-valor por artículo
    # ------------------------------------------------------------

    metadata_por_articulo = (
        df_metadata_articulos
        .set_index("unique_id")
        .to_dict(orient="index")
    )

    # ------------------------------------------------------------
    # Crear formato largo para inferencia
    # ------------------------------------------------------------

    df_inferencia = df_temp[
        [columna_codigo] + columnas_venta
    ].melt(
        id_vars=[columna_codigo],
        value_vars=columnas_venta,
        var_name="columna_venta",
        value_name="y"
    )

    df_inferencia["ds"] = df_inferencia["columna_venta"].map(
        dict(zip(mapa_fechas["columna_venta"], mapa_fechas["ds"]))
    )

    df_inferencia = df_inferencia.rename(columns={columna_codigo: "unique_id"})

    df_inferencia["y"] = pd.to_numeric(
        df_inferencia["y"],
        errors="coerce"
    ).fillna(0)

    df_inferencia = (
        df_inferencia[["unique_id", "ds", "y"]]
        .sort_values(["unique_id", "ds"])
        .reset_index(drop=True)
    )

    return (
        df_inferencia,
        df_metadata_articulos,
        metadata_por_articulo,
        mapa_fechas,
        columnas_venta
    )