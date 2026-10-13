import re
import unicodedata
import numpy as np
import pandas as pd


from pipeline.forecast_eda.eda_config import (
    COLUMNA_FILTRO_FORECAST_AUTOMATICO,
    VALOR_FILTRO_FORECAST_AUTOMATICO,
    MESES_HISTORICO_EDA,
    COLUMNAS_REQUERIDAS_INPUT,
    PATRONES_COLUMNAS_VENTA_MENSUAL,
    VARIABLES_CALCULADAS_EDA
)


# ============================================================
# MAPEO DE MESES EN ESPAÑOL
# ============================================================

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


# ============================================================
# FUNCIONES GENERALES DE LIMPIEZA Y VALIDACIÓN
# ============================================================

def normalizar_texto(texto):
    """
    Normaliza texto:
    - convierte a minúsculas
    - elimina espacios
    - elimina tildes

    Sirve para detectar columnas tipo venta_enero_2024.
    """

    texto = str(texto).strip().lower()

    texto = "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", texto)
        if unicodedata.category(caracter) != "Mn"
    )

    return texto


def validar_columnas_requeridas(df, columnas_requeridas):
    """
    Valida que el dataframe tenga las columnas mínimas necesarias.
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
    Convierte una serie que puede venir como booleano, texto o número
    a valores booleanos.

    Acepta:
    - True / False
    - 'true' / 'false'
    - 'si' / 'no'
    - 'sí' / 'no'
    - 1 / 0
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


# ============================================================
# DETECCIÓN DE COLUMNAS MENSUALES DE VENTA
# ============================================================

def extraer_fecha_desde_columna_venta(columna):
    """
    Extrae una fecha mensual desde nombres de columnas de venta.

    Soporta dos formatos:

    1. venta_2024_01
    2. venta_enero_2024

    Retorna:
    - pd.Timestamp con el primer día del mes
    - None si no reconoce el formato
    """

    columna_original = str(columna).strip()
    columna_normalizada = normalizar_texto(columna_original)

    # ------------------------------------------------------------
    # Formato: venta_2024_01
    # ------------------------------------------------------------
    match_numerico = re.match(
        r"^venta_(\d{4})_(\d{2})$",
        columna_normalizada
    )

    if match_numerico:
        anio = int(match_numerico.group(1))
        mes = int(match_numerico.group(2))

        if 1 <= mes <= 12:
            return pd.Timestamp(year=anio, month=mes, day=1)

    # ------------------------------------------------------------
    # Formato: venta_enero_2024
    # ------------------------------------------------------------
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
    Detecta columnas de venta mensual y retorna las últimas N columnas.
    """

    columnas_venta = detectar_columnas_venta_mensual(df)

    if len(columnas_venta) < meses:
        columnas_ultimos_meses = columnas_venta
    else:
        columnas_ultimos_meses = columnas_venta[-meses:]

    return columnas_ultimos_meses


# ============================================================
# FILTRO PRINCIPAL PARA EDA
# ============================================================

def filtrar_articulos_forecast_automatico(
    df,
    columna_filtro=COLUMNA_FILTRO_FORECAST_AUTOMATICO,
    valor_filtro=VALOR_FILTRO_FORECAST_AUTOMATICO
):
    """
    Filtra únicamente los artículos aplicables a forecast automático.
    """

    if columna_filtro not in df.columns:
        raise ValueError(
            f"No existe la columna de filtro '{columna_filtro}' en el dataframe."
        )

    df = df.copy()

    serie_bool = convertir_serie_a_bool(df[columna_filtro])

    df_filtrado = df[serie_bool == valor_filtro].copy()

    return df_filtrado


# ============================================================
# MATRIZ DE VENTAS MENSUALES
# ============================================================

def preparar_matriz_ventas_mensuales(
    df,
    columnas_venta,
    convertir_negativos_a_cero=True
):
    """
    Prepara una matriz numérica de ventas mensuales.

    Cada fila representa un artículo.
    Cada columna representa un mes de venta.
    """

    ventas = (
        df[columnas_venta]
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0)
    )

    if convertir_negativos_a_cero:
        ventas = ventas.clip(lower=0)

    return ventas


# ============================================================
# FUNCIONES AUXILIARES DE COMPORTAMIENTO HISTÓRICO
# ============================================================

def calcular_max_meses_consecutivos_sin_venta(fila):
    """
    Calcula la máxima racha de meses consecutivos sin venta.
    """

    valores = np.array(fila, dtype=float)

    max_racha = 0
    racha_actual = 0

    for valor in valores:
        if valor <= 0:
            racha_actual += 1
            max_racha = max(max_racha, racha_actual)
        else:
            racha_actual = 0

    return max_racha


def calcular_meses_desde_ultima_venta(fila):
    """
    Calcula cuántos meses han pasado desde la última venta.

    Si el último mes tuvo venta, retorna 0.
    Si no hubo venta en toda la ventana, retorna la longitud de la ventana.
    """

    valores = np.array(fila, dtype=float)

    indices_con_venta = np.where(valores > 0)[0]

    if len(indices_con_venta) == 0:
        return len(valores)

    ultima_posicion_venta = indices_con_venta[-1]

    meses_desde_ultima = len(valores) - 1 - ultima_posicion_venta

    return meses_desde_ultima


def calcular_pendiente_tendencia(fila):
    """
    Calcula la pendiente de tendencia de ventas mensuales.

    Una pendiente positiva sugiere crecimiento.
    Una pendiente negativa sugiere decrecimiento.
    Una pendiente cercana a cero sugiere estabilidad.
    """

    valores = np.array(fila, dtype=float)

    if len(valores) < 2:
        return 0

    if np.nansum(valores) == 0:
        return 0

    x = np.arange(len(valores))

    try:
        pendiente = np.polyfit(x, valores, 1)[0]
    except Exception:
        pendiente = 0

    return pendiente


def calcular_indice_concentracion_picos_24m(fila):
    """
    Calcula el índice de concentración de ventas en los meses de mayor demanda.

    Fórmula:
        promedio de los 3 meses más altos / promedio mensual general

    Interpretación:
    - cercano a 1: ventas relativamente estables
    - 1.5 a 3: concentración moderada
    - mayor a 3: alta concentración
    """

    valores = np.array(fila, dtype=float)

    promedio = np.nanmean(valores)

    if promedio <= 0:
        return 0

    cantidad_top = min(3, len(valores))

    top_promedio = np.sort(valores)[-cantidad_top:].mean()

    return top_promedio / promedio


def calcular_correlacion_estacional_12m(fila):
    """
    Calcula una señal de posible estacionalidad comparando:

    - primeros 12 meses
    - siguientes 12 meses

    Una correlación positiva alta sugiere repetición de patrón mensual.
    """

    valores = np.array(fila, dtype=float)

    if len(valores) < 24:
        return 0

    primer_anio = valores[:12]
    segundo_anio = valores[12:24]

    if np.std(primer_anio) == 0 or np.std(segundo_anio) == 0:
        return 0

    correlacion = np.corrcoef(primer_anio, segundo_anio)[0, 1]

    if np.isnan(correlacion):
        return 0

    return correlacion


def calcular_cv_meses_con_venta(fila):
    """
    Calcula el coeficiente de variación únicamente en meses con venta positiva.
    """

    valores = np.array(fila, dtype=float)

    valores_con_venta = valores[valores > 0]

    if len(valores_con_venta) == 0:
        return 0

    promedio = valores_con_venta.mean()

    if promedio <= 0:
        return 0

    return valores_con_venta.std() / promedio


# ============================================================
# CÁLCULO DE VARIABLES MATEMÁTICAS EDA
# ============================================================

def calcular_variables_comportamiento_demanda(
    ventas_24m
):
    """
    Calcula variables matemáticas de comportamiento de demanda
    a partir de una matriz de ventas mensuales.

    Retorna un dataframe con las variables calculadas.
    """

    cantidad_meses = ventas_24m.shape[1]

    promedio_venta_24m = ventas_24m.mean(axis=1)
    desviacion_std_venta_24m = ventas_24m.std(axis=1)

    venta_maxima_mensual_24m = ventas_24m.max(axis=1)
    venta_mediana_mensual_24m = ventas_24m.median(axis=1)

    iqr_venta_24m = (
        ventas_24m.quantile(0.75, axis=1)
        - ventas_24m.quantile(0.25, axis=1)
    )

    coeficiente_variacion_venta_24m = np.where(
        promedio_venta_24m > 0,
        desviacion_std_venta_24m / promedio_venta_24m,
        0
    )

    # ------------------------------------------------------------
    # Picos de demanda
    # ------------------------------------------------------------

    umbral_pico = promedio_venta_24m + desviacion_std_venta_24m

    cantidad_meses_pico_24m = ventas_24m.gt(
        umbral_pico,
        axis=0
    ).sum(axis=1)

    ratio_max_vs_promedio_24m = np.where(
        promedio_venta_24m > 0,
        venta_maxima_mensual_24m / promedio_venta_24m,
        0
    )

    indice_concentracion_picos_24m = ventas_24m.apply(
        calcular_indice_concentracion_picos_24m,
        axis=1
    )

    # ------------------------------------------------------------
    # Intermitencia
    # ------------------------------------------------------------

    meses_con_venta = (ventas_24m > 0).sum(axis=1)

    porcentaje_meses_sin_venta_24m = (
        (ventas_24m <= 0).sum(axis=1)
        / cantidad_meses
        * 100
    )

    venta_promedio_meses_con_venta_24m = np.where(
        meses_con_venta > 0,
        ventas_24m.sum(axis=1) / meses_con_venta,
        0
    )

    adi_24m = np.where(
        meses_con_venta > 0,
        cantidad_meses / meses_con_venta,
        0
    )

    max_meses_consecutivos_sin_venta = ventas_24m.apply(
        calcular_max_meses_consecutivos_sin_venta,
        axis=1
    )

    # ------------------------------------------------------------
    # Recencia
    # ------------------------------------------------------------

    meses_desde_ultima_venta = ventas_24m.apply(
        calcular_meses_desde_ultima_venta,
        axis=1
    )

    # ------------------------------------------------------------
    # Tendencia
    # ------------------------------------------------------------

    pendiente_tendencia_24m = ventas_24m.apply(
        calcular_pendiente_tendencia,
        axis=1
    )

    # ------------------------------------------------------------
    # Estacionalidad
    # ------------------------------------------------------------

    correlacion_estacional_12m = ventas_24m.apply(
        calcular_correlacion_estacional_12m,
        axis=1
    )

    # ------------------------------------------------------------
    # Variabilidad en meses activos
    # ------------------------------------------------------------

    cv_meses_con_venta_24m = ventas_24m.apply(
        calcular_cv_meses_con_venta,
        axis=1
    )

    # ------------------------------------------------------------
    # Construir dataframe de variables calculadas
    # ------------------------------------------------------------

    df_variables = pd.DataFrame(
        {
            "desviacion_std_venta_24m": desviacion_std_venta_24m,
            "coeficiente_variacion_venta_24m": coeficiente_variacion_venta_24m,
            "venta_maxima_mensual_24m": venta_maxima_mensual_24m,
            "venta_mediana_mensual_24m": venta_mediana_mensual_24m,
            "iqr_venta_24m": iqr_venta_24m,
            "cantidad_meses_pico_24m": cantidad_meses_pico_24m,
            "ratio_max_vs_promedio_24m": ratio_max_vs_promedio_24m,
            "indice_concentracion_picos_24m": indice_concentracion_picos_24m,
            "porcentaje_meses_sin_venta_24m": porcentaje_meses_sin_venta_24m,
            "venta_promedio_meses_con_venta_24m": venta_promedio_meses_con_venta_24m,
            "adi_24m": adi_24m,
            "max_meses_consecutivos_sin_venta": max_meses_consecutivos_sin_venta,
            "meses_desde_ultima_venta": meses_desde_ultima_venta,
            "pendiente_tendencia_24m": pendiente_tendencia_24m,
            "correlacion_estacional_12m": correlacion_estacional_12m,
            "cv_meses_con_venta_24m": cv_meses_con_venta_24m
        },
        index=ventas_24m.index
    )

    df_variables = (
        df_variables
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0)
    )

    return df_variables


def agregar_variables_comportamiento_demanda(
    df,
    columnas_venta_24m=None,
    meses_historico=MESES_HISTORICO_EDA,
    convertir_negativos_a_cero=True
):
    """
    Agrega al dataframe las variables matemáticas de comportamiento de demanda.
    """

    df = df.copy()

    if columnas_venta_24m is None:
        columnas_venta_24m = obtener_columnas_ultimos_meses(
            df=df,
            meses=meses_historico
        )

    ventas_24m = preparar_matriz_ventas_mensuales(
        df=df,
        columnas_venta=columnas_venta_24m,
        convertir_negativos_a_cero=convertir_negativos_a_cero
    )

    df_variables = calcular_variables_comportamiento_demanda(
        ventas_24m=ventas_24m
    )

    # Eliminar variables si ya existían para evitar duplicados
    columnas_a_eliminar = [
        columna
        for columna in VARIABLES_CALCULADAS_EDA
        if columna in df.columns
    ]

    if columnas_a_eliminar:
        df = df.drop(columns=columnas_a_eliminar)

    df = pd.concat(
        [
            df,
            df_variables
        ],
        axis=1
    )

    return df, columnas_venta_24m


# ============================================================
# FUNCIÓN PRINCIPAL DEL FEATURE ENGINEERING EDA
# ============================================================

def preparar_dataframe_eda_base(
    df,
    columna_filtro=COLUMNA_FILTRO_FORECAST_AUTOMATICO,
    valor_filtro=VALOR_FILTRO_FORECAST_AUTOMATICO,
    meses_historico=MESES_HISTORICO_EDA,
    convertir_negativos_a_cero=True
):
    """
    Prepara el dataframe base del pipeline 03 EDA.

    Flujo:
    1. Valida columnas mínimas.
    2. Filtra artículos aplicables a forecast automático.
    3. Detecta columnas mensuales de venta.
    4. Calcula variables matemáticas de demanda.
    """

    validar_columnas_requeridas(
        df=df,
        columnas_requeridas=COLUMNAS_REQUERIDAS_INPUT
    )

    df_eda = filtrar_articulos_forecast_automatico(
        df=df,
        columna_filtro=columna_filtro,
        valor_filtro=valor_filtro
    )

    if df_eda.empty:
        raise ValueError(
            "Después de filtrar artículos aplicables a forecast automático, "
            "el dataframe quedó vacío."
        )

    df_eda, columnas_venta_24m = agregar_variables_comportamiento_demanda(
        df=df_eda,
        columnas_venta_24m=None,
        meses_historico=meses_historico,
        convertir_negativos_a_cero=convertir_negativos_a_cero
    )

    return df_eda, columnas_venta_24m


# ============================================================
# RESUMEN DE VALIDACIÓN
# ============================================================

def generar_resumen_feature_engineering(
    df_eda,
    columnas_venta_24m
):
    """
    Genera un resumen simple para validar la salida del feature engineering.
    """

    resumen = {
        "cantidad_articulos_eda": df_eda.shape[0],
        "cantidad_columnas_eda": df_eda.shape[1],
        "cantidad_columnas_venta_24m": len(columnas_venta_24m),
        "primera_columna_venta": columnas_venta_24m[0] if columnas_venta_24m else None,
        "ultima_columna_venta": columnas_venta_24m[-1] if columnas_venta_24m else None,
        "variables_calculadas_presentes": [
            variable
            for variable in VARIABLES_CALCULADAS_EDA
            if variable in df_eda.columns
        ]
    }

    return resumen