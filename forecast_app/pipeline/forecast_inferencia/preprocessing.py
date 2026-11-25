
# =====================================================================================
# IMPORTACIONES
# =====================================================================================

import re
import pandas as pd


# =====================================================================================
# 1. CONFIGURACIÓN Y DICCIONARIOS DE REFERENCIA
# =====================================================================================

# Equivalencia entre nombres de meses en español y su representación numérica.
# Se utiliza para interpretar las columnas con formato venta_mes_YYYY.

MESES = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


# =====================================================================================
# 2. CONVERSIÓN DE COLUMNAS MENSUALES A FECHAS
# =====================================================================================

def convertir_columna_venta_a_fecha(columna):
    """
    Convierte el nombre de una columna de ventas mensuales en una fecha
    correspondiente al último día del mes.

    Formato de entrada:
        venta_febrero_2025

    Resultado:
        Timestamp('2025-02-28')
    """

    # -------------------------------------------------------------------------
    # 2.1. Validar formato y extraer mes y año
    # -------------------------------------------------------------------------

    match = re.fullmatch(
        r"venta_([a-z]+)_(\d{4})",
        str(columna)
    )

    if not match:
        raise ValueError(
            f"Formato de columna no válido: {columna}"
        )

    nombre_mes, anio = match.groups()

    # -------------------------------------------------------------------------
    # 2.2. Validar que el mes esté definido en el diccionario MESES
    # -------------------------------------------------------------------------

    if nombre_mes not in MESES:
        raise ValueError(
            f"Mes no reconocido: {nombre_mes}"
        )

    # -------------------------------------------------------------------------
    # 2.3. Construir fecha y ajustarla al último día del mes
    # -------------------------------------------------------------------------

    fecha = pd.Timestamp(
        year=int(anio),
        month=MESES[nombre_mes],
        day=1
    ) + pd.offsets.MonthEnd(0)

    return fecha


# =====================================================================================
# 3. IDENTIFICACIÓN Y ORDENAMIENTO DE COLUMNAS MENSUALES
# =====================================================================================

def obtener_columnas_venta_ordenadas(df):
    """
    Identifica las columnas mensuales de ventas de un DataFrame y las
    ordena cronológicamente.

    Formato esperado:
        venta_febrero_2025

    El ordenamiento utiliza las fechas reales calculadas mediante
    convertir_columna_venta_a_fecha().

    Retorna:
        Lista de nombres de columnas ordenados cronológicamente.
    """

    # -------------------------------------------------------------------------
    # 3.1. Definir patrón de identificación de columnas de ventas
    # -------------------------------------------------------------------------

    patron = r"^venta_([a-z]+)_(\d{4})$"

    # -------------------------------------------------------------------------
    # 3.2. Filtrar columnas que cumplen el patrón y contienen meses válidos
    # -------------------------------------------------------------------------

    columnas_venta = [
        col for col in df.columns
        if re.fullmatch(patron, str(col))
        and re.fullmatch(patron, str(col)).group(1) in MESES
    ]

    # -------------------------------------------------------------------------
    # 3.3. Ordenar las columnas cronológicamente utilizando fechas reales
    # -------------------------------------------------------------------------

    columnas_venta = sorted(
        columnas_venta,
        key=convertir_columna_venta_a_fecha
    )

    return columnas_venta


# =====================================================================================
# 4. CONVERSIÓN DE MATRIZ DE VENTAS A FORMATO LARGO
# =====================================================================================

def convertir_matriz_a_formato_largo(df_ventas, columnas_venta):
    """
    Convierte una matriz de ventas mensuales por artículo desde formato
    ancho (wide format) a formato largo (long format).

    Estructura de salida:
        codigo_articulo | columna_venta | fecha_mes | venta_mensual

    Se conservan las columnas adicionales del DataFrame como
    identificadores o metadatos de cada artículo.
    """

    # -------------------------------------------------------------------------
    # 4.1. Generar copia del DataFrame original
    # -------------------------------------------------------------------------

    df_temp = df_ventas.copy()

    # -------------------------------------------------------------------------
    # 4.2. Recuperar codigo_articulo si no existe como columna
    # -------------------------------------------------------------------------

    if "codigo_articulo" not in df_temp.columns:
        df_temp = df_temp.reset_index()

    # -------------------------------------------------------------------------
    # 4.3. Identificar columnas que deben conservarse como identificadores
    # -------------------------------------------------------------------------

    columnas_id = [
        col for col in df_temp.columns
        if col not in columnas_venta
    ]

    # -------------------------------------------------------------------------
    # 4.4. Transformar las ventas mensuales de columnas a filas
    # -------------------------------------------------------------------------

    df_long = df_temp.melt(
        id_vars=columnas_id,
        value_vars=columnas_venta,
        var_name="columna_venta",
        value_name="venta_mensual"
    )

    # -------------------------------------------------------------------------
    # 4.5. Convertir los nombres de meses a fechas de fin de mes
    # -------------------------------------------------------------------------

    df_long["fecha_mes"] = df_long["columna_venta"].apply(
        convertir_columna_venta_a_fecha
    )

    # -------------------------------------------------------------------------
    # 4.6. Convertir las ventas mensuales a valores numéricos
    # -------------------------------------------------------------------------

    df_long["venta_mensual"] = pd.to_numeric(
        df_long["venta_mensual"],
        errors="coerce"
    ).fillna(0)

    # -------------------------------------------------------------------------
    # 4.7. Ordenar observaciones por artículo y fecha
    # -------------------------------------------------------------------------

    df_long = df_long.sort_values(
        by=["codigo_articulo", "fecha_mes"]
    ).reset_index(drop=True)

    return df_long


# =====================================================================================
# 5. PREPARACIÓN DE DATASETS PARA FORECASTING Y METADATOS
# =====================================================================================

def preparar_formato_forecast_y_metadata(
    df_ventas,
    columna_codigo="codigo_articulo"
):
    """
    A partir de una matriz consolidada de artículos y ventas mensuales,
    genera las estructuras necesarias para el forecasting.

    Parámetros:
        df_ventas:
            DataFrame consolidado con información de artículos
            y columnas de ventas mensuales.

        columna_codigo:
            Nombre de la columna que identifica cada artículo.

    Retorna:
        1. df_inferencia:
            DataFrame en formato StatsForecast:
            unique_id | ds | y

        2. df_metadata_articulos:
            DataFrame con una fila por artículo y la información
            no correspondiente a ventas mensuales.

        3. metadata_por_articulo:
            Diccionario con la información de cada artículo:
            unique_id -> información completa del artículo.

        4. mapa_fechas:
            DataFrame con equivalencias:
            columna_venta | ds

        5. columnas_venta:
            Lista de columnas mensuales ordenadas cronológicamente.
    """

    # -------------------------------------------------------------------------
    # 5.1. Generar copia del DataFrame original
    # -------------------------------------------------------------------------

    df_temp = df_ventas.copy()

    # -------------------------------------------------------------------------
    # 5.2. Validar identificador del artículo y recuperarlo desde el índice
    # -------------------------------------------------------------------------

    if columna_codigo not in df_temp.columns:
        if df_temp.index.name == columna_codigo:
            df_temp = df_temp.reset_index()
        else:
            raise ValueError(
                f"No se encontró la columna {columna_codigo} en el dataframe."
            )

    # -------------------------------------------------------------------------
    # 5.3. Identificar y ordenar las columnas mensuales de ventas
    # -------------------------------------------------------------------------

    columnas_venta = obtener_columnas_venta_ordenadas(df_temp)

    # -------------------------------------------------------------------------
    # 5.4. Convertir los nombres de columnas a fechas de fin de mes
    # -------------------------------------------------------------------------

    fechas_venta = [
        convertir_columna_venta_a_fecha(col)
        for col in columnas_venta
    ]

    # -------------------------------------------------------------------------
    # 5.5. Construir mapa de equivalencias entre columnas y fechas
    # -------------------------------------------------------------------------

    mapa_fechas = pd.DataFrame({
        "columna_venta": columnas_venta,
        "ds": fechas_venta
    })

    # -------------------------------------------------------------------------
    # 5.6. Identificar columnas de metadatos no correspondientes a ventas
    # -------------------------------------------------------------------------

    columnas_metadata = [
        col for col in df_temp.columns
        if col not in columnas_venta
    ]

    # -------------------------------------------------------------------------
    # 5.7. Construir DataFrame de metadatos por artículo
    # -------------------------------------------------------------------------

    df_metadata_articulos = (
        df_temp[columnas_metadata]
        .drop_duplicates(subset=[columna_codigo])
        .copy()
    )

    # Renombrar el identificador al estándar utilizado en forecasting.
    df_metadata_articulos = df_metadata_articulos.rename(
        columns={columna_codigo: "unique_id"}
    )

    # -------------------------------------------------------------------------
    # 5.8. Verificar unicidad de artículos en el DataFrame de metadatos
    # -------------------------------------------------------------------------

    duplicados = df_metadata_articulos["unique_id"].duplicated().sum()

    if duplicados > 0:
        raise ValueError(
            f"Hay {duplicados} códigos duplicados en metadata. "
            "Revisar antes de continuar."
        )

    # -------------------------------------------------------------------------
    # 5.9. Generar diccionario de metadatos por artículo
    # -------------------------------------------------------------------------

    metadata_por_articulo = (
        df_metadata_articulos
        .set_index("unique_id")
        .to_dict(orient="index")
    )

    # -------------------------------------------------------------------------
    # 5.10. Transformar matriz de ventas de formato ancho a formato largo
    # -------------------------------------------------------------------------

    df_inferencia = df_temp[
        [columna_codigo] + columnas_venta
    ].melt(
        id_vars=[columna_codigo],
        value_vars=columnas_venta,
        var_name="columna_venta",
        value_name="y"
    )

    # -------------------------------------------------------------------------
    # 5.11. Asignar fechas reales mediante el mapa de equivalencias
    # -------------------------------------------------------------------------

    df_inferencia["ds"] = df_inferencia["columna_venta"].map(
        dict(zip(mapa_fechas["columna_venta"], mapa_fechas["ds"]))
    )

    # -------------------------------------------------------------------------
    # 5.12. Estandarizar identificador de artículo a unique_id
    # -------------------------------------------------------------------------

    df_inferencia = df_inferencia.rename(
        columns={columna_codigo: "unique_id"}
    )

    # -------------------------------------------------------------------------
    # 5.13. Convertir ventas a valores numéricos
    # -------------------------------------------------------------------------

    df_inferencia["y"] = pd.to_numeric(
        df_inferencia["y"],
        errors="coerce"
    ).fillna(0)

    # -------------------------------------------------------------------------
    # 5.14. Seleccionar columnas finales y ordenar las series temporales
    # -------------------------------------------------------------------------

    df_inferencia = (
        df_inferencia[["unique_id", "ds", "y"]]
        .sort_values(["unique_id", "ds"])
        .reset_index(drop=True)
    )

    # -------------------------------------------------------------------------
    # 5.15. Retornar los datasets y estructuras de metadatos
    # -------------------------------------------------------------------------

    return (
        df_inferencia,
        df_metadata_articulos,
        metadata_por_articulo,
        mapa_fechas,
        columnas_venta
    )
