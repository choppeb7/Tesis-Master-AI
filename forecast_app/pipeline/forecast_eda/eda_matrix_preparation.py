import re
import unicodedata
import pandas as pd

from pipeline.forecast_eda.eda_config import (
    COLUMNA_FILTRO_SEGMENTO_FORECAST,
    VALOR_FILTRO_SEGMENTO_FORECAST,
    MESES_HISTORICO_EDA,
    COLUMNAS_REQUERIDAS_INPUT
)


MESES_ES = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12
}


def normalizar_texto(texto):
    """
    Normaliza texto para facilitar detección de columnas.
    """

    texto = str(texto).strip().lower()

    texto = "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", texto)
        if unicodedata.category(caracter) != "Mn"
    )

    return texto


def validar_columnas_requeridas(df, columnas_requeridas=COLUMNAS_REQUERIDAS_INPUT):
    """
    Valida que el dataframe contenga las columnas mínimas necesarias.
    """

    columnas_faltantes = [
        columna
        for columna in columnas_requeridas
        if columna not in df.columns
    ]

    if columnas_faltantes:
        raise ValueError(
            "Faltan columnas requeridas en el dataframe: "
            + ", ".join(columnas_faltantes)
        )

    return True


def convertir_serie_a_bool(serie):
    """
    Convierte una serie a booleano de forma robusta.
    """

    if serie.dtype == bool:
        return serie

    serie_limpia = (
        serie
        .fillna(False)
        .astype(str)
        .str.strip()
        .str.lower()
    )

    mapa_booleano = {
        "true": True,
        "1": True,
        "si": True,
        "sí": True,
        "yes": True,
        "y": True,

        "false": False,
        "0": False,
        "no": False,
        "n": False,
        "nan": False,
        "none": False,
        "": False
    }

    return serie_limpia.map(mapa_booleano).fillna(False)

def validar_primary_key_articulo(
    df,
    columna_id="codigo_articulo"
):
    """
    Valida que la columna identificadora del artículo pueda usarse
    como llave primaria.

    Revisa:
    - que exista la columna
    - que no tenga nulos
    - que no tenga duplicados
    """

    if columna_id not in df.columns:
        raise ValueError(
            f"No existe la columna identificadora '{columna_id}' en el dataframe."
        )

    if df[columna_id].isna().any():
        raise ValueError(
            f"La columna '{columna_id}' contiene valores nulos."
        )

    duplicados = df[columna_id].duplicated().sum()

    if duplicados > 0:
        articulos_duplicados = (
            df.loc[df[columna_id].duplicated(keep=False), columna_id]
            .drop_duplicates()
            .head(20)
            .tolist()
        )

        raise ValueError(
            f"La columna '{columna_id}' no es única. "
            f"Se encontraron {duplicados} filas duplicadas. "
            f"Ejemplos: {articulos_duplicados}"
        )

    return True

def extraer_fecha_desde_columna_venta(columna):
    """
    Extrae una fecha desde nombres de columnas de venta.

    Soporta:
    - venta_2024_01
    - venta_enero_2024
    """

    columna_normalizada = normalizar_texto(columna)

    match_numerico = re.match(
        r"^venta_(\d{4})_(\d{2})$",
        columna_normalizada
    )

    if match_numerico:
        anio = int(match_numerico.group(1))
        mes = int(match_numerico.group(2))

        if 1 <= mes <= 12:
            return pd.Timestamp(year=anio, month=mes, day=1)

    match_texto = re.match(
        r"^venta_([a-zñ]+)_(\d{4})$",
        columna_normalizada
    )

    if match_texto:
        nombre_mes = match_texto.group(1)
        anio = int(match_texto.group(2))

        mes = MESES_ES.get(nombre_mes)

        if mes is not None:
            return pd.Timestamp(year=anio, month=mes, day=1)

    return None


def detectar_columnas_venta_mensual(df):
    """
    Detecta columnas mensuales de venta y las ordena cronológicamente.
    """

    columnas_detectadas = []

    for columna in df.columns:
        fecha_columna = extraer_fecha_desde_columna_venta(columna)

        if fecha_columna is not None:
            columnas_detectadas.append(
                {
                    "columna": columna,
                    "fecha": fecha_columna
                }
            )

    if not columnas_detectadas:
        raise ValueError(
            "No se detectaron columnas mensuales de venta. "
            "Se esperaba un formato como 'venta_2024_01' "
            "o 'venta_enero_2024'."
        )

    df_columnas = pd.DataFrame(columnas_detectadas)

    df_columnas = (
        df_columnas
        .sort_values("fecha")
        .drop_duplicates(subset=["columna"])
        .reset_index(drop=True)
    )

    return df_columnas["columna"].tolist()


def obtener_columnas_ultimos_meses(
    df,
    meses=MESES_HISTORICO_EDA
):
    """
    Retorna las últimas N columnas mensuales de venta.
    """

    columnas_venta = detectar_columnas_venta_mensual(df)

    if len(columnas_venta) < meses:
        return columnas_venta

    return columnas_venta[-meses:]


def filtrar_articulos_forecast_automatico(
    df,
    columna_filtro=COLUMNA_FILTRO_SEGMENTO_FORECAST,
    valor_filtro=VALOR_FILTRO_SEGMENTO_FORECAST
):
    """
    Filtra artículos aplicables a forecast automático.
    """

    if columna_filtro not in df.columns:
        raise ValueError(
            f"No existe la columna de filtro '{columna_filtro}' en el dataframe."
        )

    df = df.copy()

    serie_bool = convertir_serie_a_bool(df[columna_filtro])

    df_filtrado = df[serie_bool == valor_filtro].copy()

    if df_filtrado.empty:
        raise ValueError(
            "Después de filtrar artículos aplicables a forecast automático, "
            "el dataframe quedó vacío."
        )

    return df_filtrado


def preparar_matriz_ventas_mensuales(
    df,
    columnas_venta,
    columna_id="codigo_articulo",
    convertir_negativos_a_cero=True
):
    """
    Prepara una matriz numérica de ventas mensuales.

    La matriz resultante usa codigo_articulo como índice para evitar
    errores de alineación por posición.

    Filas:
    - artículos identificados por codigo_articulo

    Columnas:
    - meses de venta
    """

    validar_primary_key_articulo(
        df=df,
        columna_id=columna_id
    )

    columnas_faltantes = [
        columna
        for columna in columnas_venta
        if columna not in df.columns
    ]

    if columnas_faltantes:
        raise ValueError(
            "Faltan columnas de venta mensual en el dataframe: "
            + ", ".join(columnas_faltantes)
        )

    ventas = df[[columna_id] + list(columnas_venta)].copy()

    ventas[columnas_venta] = (
        ventas[columnas_venta]
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0)
    )

    if convertir_negativos_a_cero:
        ventas[columnas_venta] = ventas[columnas_venta].clip(lower=0)

    ventas = ventas.set_index(columna_id)

    ventas.index.name = columna_id

    return ventas

def seleccionar_columnas_base_eda(
    df,
    columnas_venta_24m,
    columnas_contexto=None,
    columna_id="codigo_articulo",
    incluir_columnas_venta_en_df_eda=True,
    ignorar_columnas_faltantes=True
):
    """
    Selecciona las columnas que acompañarán al dataframe base del EDA.

    Esta función permite controlar qué información adicional conservar
    junto al artículo antes de calcular variables matemáticas.

    Parámetros:
    - df: DataFrame filtrado.
    - columnas_venta_24m: columnas mensuales usadas para construir la matriz.
    - columnas_contexto: columnas adicionales que se desean conservar.
    - incluir_columnas_venta_en_df_eda: si True, mantiene las columnas mensuales en df_eda.
    - ignorar_columnas_faltantes: si True, ignora columnas solicitadas que no existan.

    Retorna:
    - df_base: DataFrame con identificadores, contexto y opcionalmente ventas mensuales.
    """
    validar_primary_key_articulo(
        df=df,
        columna_id=columna_id
    )
    columnas_identificadoras_minimas = [
        "codigo_articulo",
        "descripcion_completa"
    ]

    if columnas_contexto is None:
        columnas_contexto = []

    columnas_solicitadas = (
        columnas_identificadoras_minimas
        + list(columnas_contexto)
    )

    if incluir_columnas_venta_en_df_eda:
        columnas_solicitadas = (
            columnas_solicitadas
            + list(columnas_venta_24m)
        )

    # Eliminar duplicados conservando el orden
    columnas_solicitadas = list(dict.fromkeys(columnas_solicitadas))

    columnas_faltantes = [
        columna
        for columna in columnas_solicitadas
        if columna not in df.columns
    ]

    if columnas_faltantes and not ignorar_columnas_faltantes:
        raise ValueError(
            "Las siguientes columnas solicitadas no existen en el dataframe: "
            + ", ".join(columnas_faltantes)
        )

    columnas_existentes = [
        columna
        for columna in columnas_solicitadas
        if columna in df.columns
    ]

    df_base = df[columnas_existentes].copy()

    return df_base

def preparar_base_y_matriz_eda(
    df,
    columna_filtro,
    valor_filtro,
    meses_historico,
    convertir_negativos_a_cero=True,
    columnas_contexto=None,
    columna_id="codigo_articulo",
    incluir_columnas_venta_en_df_eda=True,
    ignorar_columnas_faltantes=True
):
    """
    Prepara la base inicial del EDA.

    Flujo:
    1. Valida columnas requeridas.
    2. Filtra artículos aplicables a forecast automático.
    3. Detecta columnas mensuales de venta.
    4. Toma los últimos N meses.
    5. Construye la matriz de ventas mensual.
    6. Selecciona columnas de contexto para df_eda.

    Retorna:
    - df_eda: dataframe base con artículo, columnas de contexto y ventas mensuales.
    - ventas_24m: matriz numérica de ventas mensuales.
    - columnas_venta_24m: nombres de columnas mensuales utilizadas.
    """

    validar_columnas_requeridas(df)

    df_filtrado = filtrar_articulos_forecast_automatico(
        df=df,
        columna_filtro=columna_filtro,
        valor_filtro=valor_filtro
    )

    validar_primary_key_articulo(
        df=df_filtrado,
        columna_id=columna_id
    )

    columnas_venta_24m = obtener_columnas_ultimos_meses(
        df=df_filtrado,
        meses=meses_historico
    )

    ventas_24m = preparar_matriz_ventas_mensuales(
        df=df_filtrado,
        columnas_venta=columnas_venta_24m,
        columna_id=columna_id,
        convertir_negativos_a_cero=convertir_negativos_a_cero
    )

    df_eda = seleccionar_columnas_base_eda(
        df=df_filtrado,
        columnas_venta_24m=columnas_venta_24m,
        columnas_contexto=columnas_contexto,
        columna_id=columna_id,
        incluir_columnas_venta_en_df_eda=incluir_columnas_venta_en_df_eda,
        ignorar_columnas_faltantes=ignorar_columnas_faltantes
    )

    return df_eda, ventas_24m, columnas_venta_24m

# ============================================================
# RESUMEN DE VALIDACIÓN
# ============================================================

def generar_resumen_preparacion_matriz_eda(
    df_eda,
    ventas_24m,
    columnas_venta_24m,
    columna_id="codigo_articulo"
):
    """
    Genera un resumen de validación de la preparación de matriz EDA.
    """

    resumen = {
        "cantidad_articulos_df_eda": df_eda.shape[0],
        "cantidad_columnas_df_eda": df_eda.shape[1],
        "cantidad_articulos_matriz_ventas": ventas_24m.shape[0],
        "cantidad_meses_matriz_ventas": ventas_24m.shape[1],
        "cantidad_columnas_venta_24m": len(columnas_venta_24m),
        "primera_columna_venta": columnas_venta_24m[0] if columnas_venta_24m else None,
        "ultima_columna_venta": columnas_venta_24m[-1] if columnas_venta_24m else None,
        "columna_id": columna_id,
        "matriz_index_name": ventas_24m.index.name,
        "df_eda_contiene_columna_id": columna_id in df_eda.columns,
        "matriz_index_es_unico": ventas_24m.index.is_unique,
        "df_eda_columna_id_es_unica": df_eda[columna_id].is_unique if columna_id in df_eda.columns else False
    }

    return resumen