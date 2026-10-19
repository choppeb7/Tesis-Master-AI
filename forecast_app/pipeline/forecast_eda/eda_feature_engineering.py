import numpy as np
import pandas as pd

from pipeline.forecast_eda.eda_config import (
    VARIABLES_CALCULADAS_EDA
)


# ============================================================
# VALIDACIONES
# ============================================================

def validar_matriz_ventas_eda(
    ventas_24m,
    columna_id="codigo_articulo"
):
    """
    Valida que la matriz de ventas esté correctamente preparada.

    Requisitos:
    - No debe estar vacía.
    - Debe tener codigo_articulo como índice.
    - El índice debe ser único.
    - El índice no debe tener nulos.
    - Todas las columnas deben ser numéricas.
    """

    if ventas_24m.empty:
        raise ValueError("La matriz ventas_24m está vacía.")

    if ventas_24m.index.name != columna_id:
        raise ValueError(
            f"La matriz ventas_24m debe tener '{columna_id}' como índice. "
            f"Actualmente el índice se llama: {ventas_24m.index.name}"
        )

    if not ventas_24m.index.is_unique:
        raise ValueError(
            f"La matriz ventas_24m contiene códigos duplicados en el índice '{columna_id}'."
        )

    if ventas_24m.index.isna().any():
        raise ValueError(
            f"La matriz ventas_24m contiene valores nulos en el índice '{columna_id}'."
        )

    columnas_no_numericas = [
        columna
        for columna in ventas_24m.columns
        if not pd.api.types.is_numeric_dtype(ventas_24m[columna])
    ]

    if columnas_no_numericas:
        raise ValueError(
            "La matriz ventas_24m contiene columnas no numéricas: "
            + ", ".join(columnas_no_numericas)
        )

    return True


def validar_df_eda_para_merge(
    df_eda,
    columna_id="codigo_articulo"
):
    """
    Valida que df_eda pueda recibir variables EDA mediante merge.

    Requisitos:
    - Debe contener codigo_articulo.
    - codigo_articulo no debe tener nulos.
    - codigo_articulo debe ser único.
    """

    if df_eda.empty:
        raise ValueError("df_eda está vacío.")

    if columna_id not in df_eda.columns:
        raise ValueError(
            f"df_eda no contiene la columna llave '{columna_id}'."
        )

    if df_eda[columna_id].isna().any():
        raise ValueError(
            f"df_eda contiene valores nulos en '{columna_id}'."
        )

    if not df_eda[columna_id].is_unique:
        duplicados = (
            df_eda.loc[df_eda[columna_id].duplicated(keep=False), columna_id]
            .drop_duplicates()
            .head(20)
            .tolist()
        )

        raise ValueError(
            f"df_eda contiene códigos duplicados en '{columna_id}'. "
            f"Ejemplos: {duplicados}"
        )

    return True


def validar_alineacion_df_eda_vs_matriz(
    df_eda,
    ventas_24m,
    columna_id="codigo_articulo"
):
    """
    Valida que df_eda y ventas_24m tengan los mismos artículos.
    """

    validar_df_eda_para_merge(
        df_eda=df_eda,
        columna_id=columna_id
    )

    validar_matriz_ventas_eda(
        ventas_24m=ventas_24m,
        columna_id=columna_id
    )

    codigos_df_eda = set(df_eda[columna_id].astype(str))
    codigos_matriz = set(ventas_24m.index.astype(str))

    codigos_solo_df_eda = codigos_df_eda - codigos_matriz
    codigos_solo_matriz = codigos_matriz - codigos_df_eda

    if codigos_solo_df_eda:
        raise ValueError(
            "Hay códigos en df_eda que no existen en ventas_24m. "
            f"Ejemplos: {list(codigos_solo_df_eda)[:20]}"
        )

    if codigos_solo_matriz:
        raise ValueError(
            "Hay códigos en ventas_24m que no existen en df_eda. "
            f"Ejemplos: {list(codigos_solo_matriz)[:20]}"
        )

    return True


# ============================================================
# FUNCIONES AUXILIARES DE COMPORTAMIENTO HISTÓRICO
# ============================================================

def calcular_max_meses_consecutivos_sin_venta(fila):
    """
    Calcula la máxima racha de meses consecutivos sin venta.

    Ejemplo:
    [2, 0, 0, 3, 0, 0, 0, 1] -> 3
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

    Si el último mes tuvo venta:
    retorna 0.

    Si no hubo venta en toda la ventana:
    retorna la cantidad total de meses.
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
    Calcula la pendiente de tendencia de la serie mensual.

    Valor positivo:
    - tendencia creciente.

    Valor negativo:
    - tendencia decreciente.

    Valor cercano a cero:
    - tendencia estable.
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

    if np.isnan(pendiente) or np.isinf(pendiente):
        return 0

    return pendiente


def calcular_indice_concentracion_picos_24m(fila):
    """
    Calcula el índice de concentración de ventas en los meses más altos.

    Fórmula:
    promedio de los 3 meses más altos / promedio mensual general.

    Interpretación:
    - cercano a 1: ventas distribuidas de forma más estable.
    - entre 1.5 y 3: concentración moderada.
    - mayor a 3: alta concentración en pocos meses.
    """

    valores = np.array(fila, dtype=float)

    promedio = np.nanmean(valores)

    if promedio <= 0:
        return 0

    cantidad_top = min(3, len(valores))

    top_promedio = np.sort(valores)[-cantidad_top:].mean()

    resultado = top_promedio / promedio

    if np.isnan(resultado) or np.isinf(resultado):
        return 0

    return resultado


def calcular_correlacion_estacional_12m(fila):
    """
    Calcula una señal preliminar de estacionalidad.

    Compara:
    - primeros 12 meses
    - siguientes 12 meses

    Una correlación positiva alta indica que el patrón mensual
    del segundo año se parece al patrón mensual del primer año.
    """

    valores = np.array(fila, dtype=float)

    if len(valores) < 24:
        return 0

    primer_anio = valores[:12]
    segundo_anio = valores[12:24]

    if np.std(primer_anio) == 0 or np.std(segundo_anio) == 0:
        return 0

    correlacion = np.corrcoef(primer_anio, segundo_anio)[0, 1]

    if np.isnan(correlacion) or np.isinf(correlacion):
        return 0

    return correlacion


def calcular_cv_meses_con_venta(fila):
    """
    Calcula el coeficiente de variación solo en los meses con venta.

    Esto mide la variabilidad del tamaño de la demanda
    cuando sí existe venta.
    """

    valores = np.array(fila, dtype=float)

    valores_con_venta = valores[valores > 0]

    if len(valores_con_venta) == 0:
        return 0

    promedio = valores_con_venta.mean()

    if promedio <= 0:
        return 0

    resultado = valores_con_venta.std() / promedio

    if np.isnan(resultado) or np.isinf(resultado):
        return 0

    return resultado

def calcular_meses_con_venta_24m(fila):
    """
    Calcula la cantidad de meses con ventas positivas
    durante los últimos 24 meses.

    Criterio:
    - Venta > 0: mes con venta.
    - Venta <= 0: mes sin venta.

    Ejemplo:
    [10, 0, 5, 0, 20, 0] -> 3
    """

    valores = np.array(fila, dtype=float)

    meses_con_venta = np.sum(valores > 0)

    return int(meses_con_venta)

# ============================================================
# CÁLCULO DE VARIABLES MATEMÁTICAS EDA
# ============================================================

def calcular_variables_comportamiento_demanda(
    ventas_24m,
    columna_id="codigo_articulo"
):
    """
    Calcula variables matemáticas de comportamiento de demanda
    a partir de la matriz mensual ventas_24m.

    Entrada:
    - ventas_24m:
      DataFrame numérico con codigo_articulo como índice.

    Salida:
    - df_variables:
      DataFrame con codigo_articulo como índice y variables EDA calculadas.
    """

    validar_matriz_ventas_eda(
        ventas_24m=ventas_24m,
        columna_id=columna_id
    )

    cantidad_meses = ventas_24m.shape[1]

    # ============================================================
    # Variables de distribución mensual
    # ============================================================

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

    # ============================================================
    # Variables de picos y concentración
    # ============================================================

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

    # ============================================================
    # Variables de intermitencia
    # ============================================================

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

    # ============================================================
    # Variables de recencia
    # ============================================================

    meses_desde_ultima_venta = ventas_24m.apply(
        calcular_meses_desde_ultima_venta,
        axis=1
    )

    # ============================================================
    # Variables de tendencia
    # ============================================================

    pendiente_tendencia_24m = ventas_24m.apply(
        calcular_pendiente_tendencia,
        axis=1
    )

    # ============================================================
    # meses con venta

    # ============================================================
    meses_con_venta_24m = ventas_24m.apply(
        calcular_meses_con_venta_24m,
        axis=1
    )
    # ============================================================
    # Variables de estacionalidad
    # ============================================================

    correlacion_estacional_12m = ventas_24m.apply(
        calcular_correlacion_estacional_12m,
        axis=1
    )


    # ============================================================
    # Variabilidad en meses activos
    # ============================================================

    cv_meses_con_venta_24m = ventas_24m.apply(
        calcular_cv_meses_con_venta,
        axis=1
    )

    # ============================================================
    # Construcción del DataFrame de variables
    # ============================================================

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
            "cv_meses_con_venta_24m": cv_meses_con_venta_24m,
            "meses_con_venta_24m": meses_con_venta_24m
        },
        index=ventas_24m.index
    )

    df_variables.index.name = columna_id

    df_variables = (
        df_variables
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0)
    )

    return df_variables



# ============================================================
# UNIÓN DE VARIABLES EDA AL DATAFRAME BASE
# ============================================================

def agregar_feature_engineering_a_dataframe(
    df_eda,
    ventas_24m,
    columna_id="codigo_articulo"
):
    """
    Agrega las variables matemáticas EDA a df_eda usando codigo_articulo
    como llave primaria.

    No usa concat por posición.
    Usa merge one_to_one para evitar desalineaciones.
    """

    validar_alineacion_df_eda_vs_matriz(
        df_eda=df_eda,
        ventas_24m=ventas_24m,
        columna_id=columna_id
    )

    df_eda = df_eda.copy()

    df_variables = calcular_variables_comportamiento_demanda(
        ventas_24m=ventas_24m,
        columna_id=columna_id
    )

    df_variables = df_variables.reset_index()

    # ------------------------------------------------------------
    # Eliminar variables existentes para evitar duplicados
    # ------------------------------------------------------------

    columnas_existentes = [
        columna
        for columna in VARIABLES_CALCULADAS_EDA
        if columna in df_eda.columns
    ]

    if columnas_existentes:
        df_eda = df_eda.drop(columns=columnas_existentes)

    # ------------------------------------------------------------
    # Validar que todos los códigos tengan variables calculadas
    # ------------------------------------------------------------

    codigos_df_eda = set(df_eda[columna_id].astype(str))
    codigos_variables = set(df_variables[columna_id].astype(str))

    codigos_sin_variables = codigos_df_eda - codigos_variables

    if codigos_sin_variables:
        raise ValueError(
            "Hay artículos en df_eda sin variables calculadas. "
            f"Ejemplos: {list(codigos_sin_variables)[:20]}"
        )

    # ------------------------------------------------------------
    # Merge seguro por llave primaria
    # ------------------------------------------------------------

    df_eda_enriquecido = df_eda.merge(
        df_variables,
        on=columna_id,
        how="left",
        validate="one_to_one"
    )

    # ------------------------------------------------------------
    # Validar resultado final
    # ------------------------------------------------------------

    if df_eda_enriquecido.shape[0] != df_eda.shape[0]:
        raise ValueError(
            "El merge modificó la cantidad de filas del dataframe EDA."
        )

    variables_faltantes = [
        variable
        for variable in VARIABLES_CALCULADAS_EDA
        if variable not in df_eda_enriquecido.columns
    ]

    if variables_faltantes:
        raise ValueError(
            "No se agregaron correctamente las siguientes variables EDA: "
            + ", ".join(variables_faltantes)
        )

    return df_eda_enriquecido


# ============================================================
# RESÚMENES DE VALIDACIÓN
# ============================================================

def generar_resumen_variables_eda(
    df_eda,
    columna_id="codigo_articulo"
):
    """
    Genera un resumen rápido de las variables EDA calculadas.
    """

    variables_presentes = [
        variable
        for variable in VARIABLES_CALCULADAS_EDA
        if variable in df_eda.columns
    ]

    variables_faltantes = [
        variable
        for variable in VARIABLES_CALCULADAS_EDA
        if variable not in df_eda.columns
    ]

    resumen = {
        "cantidad_articulos": df_eda.shape[0],
        "cantidad_columnas": df_eda.shape[1],
        "columna_id": columna_id,
        "columna_id_presente": columna_id in df_eda.columns,
        "columna_id_unica": df_eda[columna_id].is_unique if columna_id in df_eda.columns else False,
        "cantidad_variables_calculadas": len(variables_presentes),
        "variables_calculadas_presentes": variables_presentes,
        "variables_calculadas_faltantes": variables_faltantes
    }

    return resumen


def generar_descriptivos_variables_eda(df_eda):
    """
    Genera una tabla descriptiva de las variables EDA calculadas.
    """

    variables_presentes = [
        variable
        for variable in VARIABLES_CALCULADAS_EDA
        if variable in df_eda.columns
    ]

    if not variables_presentes:
        raise ValueError(
            "No hay variables EDA calculadas presentes para generar descriptivos."
        )

    descriptivos = (
        df_eda[variables_presentes]
        .describe()
        .T
        .reset_index()
        .rename(columns={"index": "variable"})
    )

    return descriptivos