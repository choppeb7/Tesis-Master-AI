import numpy as np
import pandas as pd


from pipeline.forecast_eda.eda_config import (
    # Columnas oficiales de clasificación
    COLUMNAS_CLASIFICACION_EDA,

    # Estacionalidad
    UMBRAL_ESTACIONALIDAD_FUERTE,
    UMBRAL_ESTACIONALIDAD_MODERADA,
    UMBRAL_ESTACIONALIDAD_DEBIL,
    ETIQUETA_ESTACIONALIDAD_FUERTE,
    ETIQUETA_ESTACIONALIDAD_MODERADA,
    ETIQUETA_ESTACIONALIDAD_DEBIL,
    ETIQUETA_ESTACIONALIDAD_SIN_CLARA,

    # Frecuencia
    UMBRAL_ALTA_FRECUENCIA_MESES,
    UMBRAL_FRECUENCIA_MEDIA_MESES,
    UMBRAL_BAJA_FRECUENCIA_MESES,
    UMBRAL_FRECUENCIA_ESPORADICA_MESES,
    ETIQUETA_ALTA_FRECUENCIA,
    ETIQUETA_FRECUENCIA_MEDIA,
    ETIQUETA_BAJA_FRECUENCIA,
    ETIQUETA_FRECUENCIA_ESPORADICA,
    ETIQUETA_MUY_BAJA_FRECUENCIA,

    # Intermitencia
    UMBRAL_BAJA_INTERMITENCIA_PCT,
    UMBRAL_INTERMITENCIA_MODERADA_PCT,
    UMBRAL_ALTA_INTERMITENCIA_PCT,
    ETIQUETA_BAJA_INTERMITENCIA,
    ETIQUETA_INTERMITENCIA_MODERADA,
    ETIQUETA_ALTA_INTERMITENCIA,
    ETIQUETA_INTERMITENCIA_CRITICA,

    # Recencia
    UMBRAL_VENTA_MUY_RECIENTE_MESES,
    UMBRAL_VENTA_RECIENTE_MESES,
    UMBRAL_VENTA_MODERADAMENTE_RECIENTE_MESES,
    UMBRAL_VENTA_ANTIGUA_MESES,
    ETIQUETA_VENTA_MUY_RECIENTE,
    ETIQUETA_VENTA_RECIENTE,
    ETIQUETA_VENTA_MODERADAMENTE_RECIENTE,
    ETIQUETA_VENTA_ANTIGUA,
    ETIQUETA_VENTA_MUY_ANTIGUA,

    # Variabilidad
    UMBRAL_BAJA_VARIABILIDAD_CV,
    UMBRAL_VARIABILIDAD_MODERADA_CV,
    UMBRAL_ALTA_VARIABILIDAD_CV,
    ETIQUETA_BAJA_VARIABILIDAD,
    ETIQUETA_VARIABILIDAD_MODERADA,
    ETIQUETA_ALTA_VARIABILIDAD,
    ETIQUETA_VARIABILIDAD_EXTREMA,

    # Tendencia
    UMBRAL_TENDENCIA,
    ETIQUETA_TENDENCIA_CRECIENTE,
    ETIQUETA_TENDENCIA_DECRECIENTE,
    ETIQUETA_TENDENCIA_ESTABLE,

    # Concentración de picos
    UMBRAL_BAJA_CONCENTRACION_PICOS,
    UMBRAL_CONCENTRACION_MODERADA_PICOS,
    ETIQUETA_BAJA_CONCENTRACION,
    ETIQUETA_CONCENTRACION_MODERADA,
    ETIQUETA_ALTA_CONCENTRACION
)


# ============================================================
# VARIABLES REQUERIDAS PARA CLASIFICACIÓN
# ============================================================
# Esta lista podría vivir en eda_config.py.
# La dejo aquí para que el script funcione aunque aún no la hayas agregado.

VARIABLES_REQUERIDAS_CLASIFICACION_EDA = [
    "meses_con_venta_24m",
    "porcentaje_meses_sin_venta_24m",
    "meses_desde_ultima_venta",
    "coeficiente_variacion_venta_24m",
    "pendiente_tendencia_24m",
    "correlacion_estacional_12m",
    "indice_concentracion_picos_24m"
]


# ============================================================
# VALIDACIONES
# ============================================================

def validar_columnas_para_clasificacion(df_eda):
    """
    Valida que el dataframe tenga las variables numéricas necesarias
    para generar las clasificaciones EDA.
    """

    columnas_faltantes = [
        columna
        for columna in VARIABLES_REQUERIDAS_CLASIFICACION_EDA
        if columna not in df_eda.columns
    ]

    if columnas_faltantes:
        raise ValueError(
            "Faltan columnas necesarias para aplicar clasificaciones EDA: "
            + ", ".join(columnas_faltantes)
        )

    return True


def asegurar_columnas_numericas_clasificacion(df_eda):
    """
    Convierte las variables requeridas a formato numérico.

    Esto evita errores si alguna columna viene como texto desde Excel.
    """

    df_eda = df_eda.copy()

    for columna in VARIABLES_REQUERIDAS_CLASIFICACION_EDA:
        df_eda[columna] = (
            pd.to_numeric(df_eda[columna], errors="coerce")
            .replace([np.inf, -np.inf], np.nan)
            .fillna(0)
        )

    return df_eda


# ============================================================
# FUNCIONES DE CLASIFICACIÓN
# ============================================================

def clasificar_estacionalidad(df_eda):
    """
    Clasifica la posible estacionalidad con base en la correlación
    entre el primer y segundo año.
    """

    condiciones = [
        df_eda["correlacion_estacional_12m"] >= UMBRAL_ESTACIONALIDAD_FUERTE,
        df_eda["correlacion_estacional_12m"] >= UMBRAL_ESTACIONALIDAD_MODERADA,
        df_eda["correlacion_estacional_12m"] >= UMBRAL_ESTACIONALIDAD_DEBIL
    ]

    resultados = [
        ETIQUETA_ESTACIONALIDAD_FUERTE,
        ETIQUETA_ESTACIONALIDAD_MODERADA,
        ETIQUETA_ESTACIONALIDAD_DEBIL
    ]

    return np.select(
        condiciones,
        resultados,
        default=ETIQUETA_ESTACIONALIDAD_SIN_CLARA
    )


def clasificar_frecuencia_venta(df_eda):
    """
    Clasifica la frecuencia de venta según meses con venta en 24 meses.
    """

    condiciones = [
        df_eda["meses_con_venta_24m"] >= UMBRAL_ALTA_FRECUENCIA_MESES,
        df_eda["meses_con_venta_24m"] >= UMBRAL_FRECUENCIA_MEDIA_MESES,
        df_eda["meses_con_venta_24m"] >= UMBRAL_BAJA_FRECUENCIA_MESES,
        df_eda["meses_con_venta_24m"] >= UMBRAL_FRECUENCIA_ESPORADICA_MESES
    ]

    resultados = [
        ETIQUETA_ALTA_FRECUENCIA,
        ETIQUETA_FRECUENCIA_MEDIA,
        ETIQUETA_BAJA_FRECUENCIA,
        ETIQUETA_FRECUENCIA_ESPORADICA
    ]

    return np.select(
        condiciones,
        resultados,
        default=ETIQUETA_MUY_BAJA_FRECUENCIA
    )


def clasificar_intermitencia(df_eda):
    """
    Clasifica la intermitencia según el porcentaje de meses sin venta.
    """

    condiciones = [
        df_eda["porcentaje_meses_sin_venta_24m"] <= UMBRAL_BAJA_INTERMITENCIA_PCT,
        df_eda["porcentaje_meses_sin_venta_24m"] <= UMBRAL_INTERMITENCIA_MODERADA_PCT,
        df_eda["porcentaje_meses_sin_venta_24m"] <= UMBRAL_ALTA_INTERMITENCIA_PCT
    ]

    resultados = [
        ETIQUETA_BAJA_INTERMITENCIA,
        ETIQUETA_INTERMITENCIA_MODERADA,
        ETIQUETA_ALTA_INTERMITENCIA
    ]

    return np.select(
        condiciones,
        resultados,
        default=ETIQUETA_INTERMITENCIA_CRITICA
    )


def clasificar_recencia_venta(df_eda):
    """
    Clasifica qué tan reciente fue la última venta.
    """

    condiciones = [
        df_eda["meses_desde_ultima_venta"] <= UMBRAL_VENTA_MUY_RECIENTE_MESES,
        df_eda["meses_desde_ultima_venta"] <= UMBRAL_VENTA_RECIENTE_MESES,
        df_eda["meses_desde_ultima_venta"] <= UMBRAL_VENTA_MODERADAMENTE_RECIENTE_MESES,
        df_eda["meses_desde_ultima_venta"] <= UMBRAL_VENTA_ANTIGUA_MESES
    ]

    resultados = [
        ETIQUETA_VENTA_MUY_RECIENTE,
        ETIQUETA_VENTA_RECIENTE,
        ETIQUETA_VENTA_MODERADAMENTE_RECIENTE,
        ETIQUETA_VENTA_ANTIGUA
    ]

    return np.select(
        condiciones,
        resultados,
        default=ETIQUETA_VENTA_MUY_ANTIGUA
    )


def clasificar_variabilidad(df_eda):
    """
    Clasifica la variabilidad usando el coeficiente de variación mensual.
    """

    condiciones = [
        df_eda["coeficiente_variacion_venta_24m"] <= UMBRAL_BAJA_VARIABILIDAD_CV,
        df_eda["coeficiente_variacion_venta_24m"] <= UMBRAL_VARIABILIDAD_MODERADA_CV,
        df_eda["coeficiente_variacion_venta_24m"] <= UMBRAL_ALTA_VARIABILIDAD_CV
    ]

    resultados = [
        ETIQUETA_BAJA_VARIABILIDAD,
        ETIQUETA_VARIABILIDAD_MODERADA,
        ETIQUETA_ALTA_VARIABILIDAD
    ]

    return np.select(
        condiciones,
        resultados,
        default=ETIQUETA_VARIABILIDAD_EXTREMA
    )


def clasificar_tendencia(df_eda):
    """
    Clasifica la tendencia según la pendiente de la serie mensual.
    """

    condiciones = [
        df_eda["pendiente_tendencia_24m"] > UMBRAL_TENDENCIA,
        df_eda["pendiente_tendencia_24m"] < -UMBRAL_TENDENCIA
    ]

    resultados = [
        ETIQUETA_TENDENCIA_CRECIENTE,
        ETIQUETA_TENDENCIA_DECRECIENTE
    ]

    return np.select(
        condiciones,
        resultados,
        default=ETIQUETA_TENDENCIA_ESTABLE
    )


def clasificar_concentracion_picos(df_eda):
    """
    Clasifica qué tan concentrada está la demanda en pocos meses.
    """

    condiciones = [
        df_eda["indice_concentracion_picos_24m"] <= UMBRAL_BAJA_CONCENTRACION_PICOS,
        df_eda["indice_concentracion_picos_24m"] <= UMBRAL_CONCENTRACION_MODERADA_PICOS
    ]

    resultados = [
        ETIQUETA_BAJA_CONCENTRACION,
        ETIQUETA_CONCENTRACION_MODERADA
    ]

    return np.select(
        condiciones,
        resultados,
        default=ETIQUETA_ALTA_CONCENTRACION
    )


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def aplicar_clasificaciones_eda(df_eda):
    """
    Aplica todas las clasificaciones EDA al dataframe enriquecido
    con variables matemáticas.

    Entrada:
    - df_eda con variables calculadas en eda_feature_engineering.py

    Salida:
    - df_eda con columnas de clasificación EDA
    """

    df_eda = df_eda.copy()

    validar_columnas_para_clasificacion(df_eda)

    df_eda = asegurar_columnas_numericas_clasificacion(df_eda)

    # Eliminar clasificaciones existentes para evitar duplicados
    columnas_existentes = [
        columna
        for columna in COLUMNAS_CLASIFICACION_EDA
        if columna in df_eda.columns
    ]

    if columnas_existentes:
        df_eda = df_eda.drop(columns=columnas_existentes)

    df_eda["clasificacion_estacionalidad_24m"] = clasificar_estacionalidad(df_eda)

    df_eda["clasificacion_frecuencia_venta_24m"] = clasificar_frecuencia_venta(df_eda)

    df_eda["clasificacion_intermitencia_24m"] = clasificar_intermitencia(df_eda)

    df_eda["clasificacion_recencia_venta_24m"] = clasificar_recencia_venta(df_eda)

    df_eda["clasificacion_variabilidad_24m"] = clasificar_variabilidad(df_eda)

    df_eda["clasificacion_tendencia_24m"] = clasificar_tendencia(df_eda)

    df_eda["clasificacion_concentracion_picos_24m"] = clasificar_concentracion_picos(df_eda)

    validar_columnas_clasificacion_generadas(df_eda)

    return df_eda


def validar_columnas_clasificacion_generadas(df_eda):
    """
    Valida que todas las columnas oficiales de clasificación hayan sido generadas.
    """

    columnas_faltantes = [
        columna
        for columna in COLUMNAS_CLASIFICACION_EDA
        if columna not in df_eda.columns
    ]

    if columnas_faltantes:
        raise ValueError(
            "No se generaron correctamente las siguientes columnas de clasificación: "
            + ", ".join(columnas_faltantes)
        )

    return True


# ============================================================
# RESÚMENES
# ============================================================

def generar_resumen_clasificaciones_eda(df_eda):
    """
    Genera una tabla larga con conteo y porcentaje por cada clasificación.
    """

    validar_columnas_clasificacion_generadas(df_eda)

    total_articulos = len(df_eda)

    resumenes = []

    for columna in COLUMNAS_CLASIFICACION_EDA:
        conteo = (
            df_eda[columna]
            .value_counts(dropna=False)
            .rename_axis("clasificacion")
            .reset_index(name="cantidad_articulos")
        )

        conteo["variable_clasificacion"] = columna

        conteo["porcentaje_articulos"] = (
            conteo["cantidad_articulos"]
            / total_articulos
            * 100
        ).round(2)

        conteo = conteo[
            [
                "variable_clasificacion",
                "clasificacion",
                "cantidad_articulos",
                "porcentaje_articulos"
            ]
        ]

        resumenes.append(conteo)

    df_resumen = pd.concat(
        resumenes,
        ignore_index=True
    )

    return df_resumen


def generar_resumen_cruzado_clasificaciones(
    df_eda,
    columna_fila,
    columna_columna,
    incluir_totales=True
):
    """
    Genera una tabla cruzada entre dos clasificaciones.

    Ejemplo:
    - variabilidad vs intermitencia
    - tendencia vs estacionalidad
    """

    if columna_fila not in df_eda.columns:
        raise ValueError(
            f"No existe la columna '{columna_fila}' en df_eda."
        )

    if columna_columna not in df_eda.columns:
        raise ValueError(
            f"No existe la columna '{columna_columna}' en df_eda."
        )

    tabla = pd.crosstab(
        df_eda[columna_fila],
        df_eda[columna_columna],
        margins=incluir_totales
    )

    return tabla


def generar_resumen_clasificaciones_por_columna(
    df_eda,
    columna_clasificacion
):
    """
    Genera un resumen de conteo y porcentaje para una sola columna
    de clasificación.
    """

    if columna_clasificacion not in df_eda.columns:
        raise ValueError(
            f"No existe la columna '{columna_clasificacion}' en df_eda."
        )

    total_articulos = len(df_eda)

    resumen = (
        df_eda[columna_clasificacion]
        .value_counts(dropna=False)
        .rename_axis("clasificacion")
        .reset_index(name="cantidad_articulos")
    )

    resumen["porcentaje_articulos"] = (
        resumen["cantidad_articulos"]
        / total_articulos
        * 100
    ).round(2)

    return resumen