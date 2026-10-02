from pathlib import Path
import sys
import pandas as pd
import numpy as np


MESES_ES = {
    1: "enero",
    2: "febrero",
    3: "marzo",
    4: "abril",
    5: "mayo",
    6: "junio",
    7: "julio",
    8: "agosto",
    9: "septiembre",
    10: "octubre",
    11: "noviembre",
    12: "diciembre",
}


def generar_columnas_venta_ultimos_meses(
    config_fechas,
    meses_historico=24
):
    """
    Genera los nombres esperados de columnas mensuales de venta
    para los últimos N meses del período histórico.

    Ejemplo:
    venta_septiembre_2024
    venta_octubre_2024
    ...
    venta_septiembre_2026
    """

    fecha_inicio = config_fechas.fecha_inicio_historico
    fecha_fin = config_fechas.fecha_fin

    fechas_mensuales = pd.date_range(
        start=pd.Timestamp(fecha_inicio).replace(day=1),
        end=pd.Timestamp(fecha_fin).replace(day=1),
        freq="MS"
    )

    columnas = []

    for fecha in fechas_mensuales:
        nombre_mes = MESES_ES[fecha.month]
        nombre_columna = f"venta_{nombre_mes}_{fecha.year}"
        columnas.append(nombre_columna)

    # Tomar solo los últimos N meses disponibles
    columnas = columnas[-meses_historico:]

    return columnas


def obtener_columnas_venta_disponibles(
    df,
    columnas_esperadas
):
    """
    Retorna únicamente las columnas de venta que existen en el dataframe.
    """

    columnas_disponibles = [
        columna
        for columna in columnas_esperadas
        if columna in df.columns
    ]

    columnas_faltantes = [
        columna
        for columna in columnas_esperadas
        if columna not in df.columns
    ]

    if columnas_faltantes:
        print("Advertencia: algunas columnas mensuales esperadas no existen en el dataframe:")
        for columna in columnas_faltantes:
            print("-", columna)

    if not columnas_disponibles:
        raise ValueError(
            "No se encontraron columnas mensuales de venta disponibles."
        )

    return columnas_disponibles


def preparar_columnas_numericas_comerciales(df):
    """
    Asegura que las columnas necesarias para cálculos comerciales
    sean numéricas.
    """

    df = df.copy()

    columnas_numericas = [
        "ultimo_precio_compra",
        "costo_promedio",
        "total_unidades_vendidas_24m"
    ]

    for columna in columnas_numericas:
        if columna in df.columns:
            df[columna] = pd.to_numeric(
                df[columna],
                errors="coerce"
            ).fillna(0)

    return df

def calcular_precio_referencia(
    df,
    margen_bruto_objetivo=0.30
):
    """
    Calcula un precio de referencia de venta a partir del costo.

    Se usa como costo base:
    1. costo_promedio, si existe y es mayor que cero.
    2. ultimo_precio_compra, si costo_promedio no existe o es cero.

    Luego se calcula:

        precio_referencia = costo_base / (1 - margen_bruto_objetivo)

    Ejemplo:
        costo_base = 100
        margen_bruto_objetivo = 0.30
        precio_referencia = 100 / 0.70 = 142.86
    """

    df = df.copy()

    if margen_bruto_objetivo <= 0 or margen_bruto_objetivo >= 1:
        raise ValueError(
            "margen_bruto_objetivo debe estar entre 0 y 1. "
            "Ejemplo: 0.30 para 30%."
        )

    df["costo_promedio"] = pd.to_numeric(
        df.get("costo_promedio", 0),
        errors="coerce"
    ).fillna(0)

    df["ultimo_precio_compra"] = pd.to_numeric(
        df.get("ultimo_precio_compra", 0),
        errors="coerce"
    ).fillna(0)

    df["costo_base_referencia"] = np.where(
        df["costo_promedio"] > 0,
        df["costo_promedio"],
        df["ultimo_precio_compra"]
    )

    df["precio_referencia"] = np.where(
        df["costo_base_referencia"] > 0,
        df["costo_base_referencia"] / (1 - margen_bruto_objetivo),
        0
    )

    return df

def calcular_criticidad_comercial(
    df,
    columnas_venta_24m
):
    df["cantidad_vendida_24m"] = (
    df[columnas_venta_24m]
    .sum(axis=1)
    )

# Calcular precio de venta estimado a partir del costo,
# usando un margen bruto objetivo del 30%.
    df = calcular_precio_referencia(
    df=df,
    margen_bruto_objetivo=0.30
    )

    df["venta_estimada_24m"] = (
    df["cantidad_vendida_24m"]
    * df["precio_referencia"]
    )


    df["venta_estimada_24m"] = (
        df["cantidad_vendida_24m"]
        * df["precio_referencia"]
    )

    total_venta_estimada = df["venta_estimada_24m"].sum()

    if total_venta_estimada > 0:
        df["participacion_comercial"] = (
            df["venta_estimada_24m"] / total_venta_estimada
        )
    else:
        df["participacion_comercial"] = 0

    df = df.sort_values(
        by="venta_estimada_24m",
        ascending=False
    ).reset_index(drop=True)

    df["participacion_acumulada"] = (
        df["participacion_comercial"]
        .cumsum()
        .round(4)
    )

    df["criticidad_comercial"] = np.select(
    [
        df["venta_estimada_24m"] <= 0,
        df["participacion_acumulada"] <= 0.50,
        df["participacion_acumulada"] <= 0.70,
        df["participacion_acumulada"] <= 0.80,
        df["participacion_acumulada"] <= 0.90
    ],
    [
        "sin_venta",
        "critica",
        "alta",
        "media",
        "baja"
    ],
    default="muy_baja"
    )

    return df


def calcular_frecuencia_venta_24m(
    df,
    columnas_venta_24m
):
    """
    Calcula:
    - meses_con_venta_24m
    - frecuencia_venta_24m_pct
    """

    df = df.copy()

    for columna in columnas_venta_24m:
        df[columna] = pd.to_numeric(
            df[columna],
            errors="coerce"
        ).fillna(0)

    df["meses_con_venta_24m"] = (
        df[columnas_venta_24m] > 0
    ).sum(axis=1)

    df["frecuencia_venta_24m_pct"] = (
        df["meses_con_venta_24m"]
        / len(columnas_venta_24m)
        * 100
    ).round(2)

    return df


def clasificar_tipo_abastecimiento(row):
    """
    Clasifica el artículo según recurrencia de venta e impacto económico.

    Reglas:
    - stock_regular:
        6 o más meses con venta.

    - stock_puntual:
        entre 3 y 5 meses con venta.

    - articulo_proyecto:
        2 meses o menos con venta, pero venta estimada >= 1000.

    - bajo_pedido_especial:
        venta muy esporádica o bajo impacto económico.
    """

    meses_con_venta = row["meses_con_venta_24m"]
    #venta_estimada = row["venta_estimada_24m"]

    if meses_con_venta >= 6:
        return "stock_regular"

    elif 3 <= meses_con_venta <= 5:
        return "stock_puntual"

    elif meses_con_venta <= 2:
        return "articulo_proyecto"

    else:
        return "bajo_pedido_especial"


def calcular_tipo_abastecimiento_y_forecast(df):
    """
    Calcula:
    - tipo_abastecimiento
    - aplica_forecast
    """

    df = df.copy()

    df["tipo_abastecimiento"] = df.apply(
        clasificar_tipo_abastecimiento,
        axis=1
    )

    df["aplica_forecast"] = ~df["tipo_abastecimiento"].isin(
        [
            "articulo_proyecto",
            "bajo_pedido_especial"
        ]
    )

    return df


def aplicar_reglas_comerciales(
    df,
    config_fechas,
    meses_historico=24
):
    """
    Aplica todas las reglas comerciales al dataframe base.

    Retorna:
    - df con columnas comerciales calculadas.
    """

    df = df.copy()

    df = preparar_columnas_numericas_comerciales(df)

    columnas_esperadas = generar_columnas_venta_ultimos_meses(
        config_fechas=config_fechas,
        meses_historico=meses_historico
    )

    columnas_venta_24m = obtener_columnas_venta_disponibles(
        df=df,
        columnas_esperadas=columnas_esperadas
    )

    df = calcular_criticidad_comercial(
        df=df,
        columnas_venta_24m=columnas_venta_24m
    )

    df = calcular_frecuencia_venta_24m(
        df=df,
        columnas_venta_24m=columnas_venta_24m
    )

    df = calcular_tipo_abastecimiento_y_forecast(df)

    return df


def mostrar_resumen_reglas_comerciales(df):
    """
    Muestra resumen de los principales campos comerciales calculados.
    """

    print("=" * 80)
    print("RESUMEN REGLAS COMERCIALES")
    print("=" * 80)

    print(f"Filas: {df.shape[0]:,}")
    print(f"Columnas: {df.shape[1]:,}")

    print("\nCriticidad comercial:")
    print(df["criticidad_comercial"].value_counts(dropna=False))

    print("\nTipo de abastecimiento:")
    print(df["tipo_abastecimiento"].value_counts(dropna=False))

    print("\nAplica forecast:")
    print(df["aplica_forecast"].value_counts(dropna=False))

    print("\nVenta estimada 24M total:")
    print(round(df["venta_estimada_24m"].sum(), 2))


def main():
    """
    Prueba directa de commercial_rules.py usando el archivo generado
    por test_oitm_ventas_extraction.py.
    """

    project_root = Path(__file__).resolve().parents[3]
    forecast_app_dir = project_root / "forecast_app"

    if str(forecast_app_dir) not in sys.path:
        sys.path.insert(0, str(forecast_app_dir))

    from pipeline.data_preparation.date_config import construir_configuracion_fechas

    ruta_input = (
        forecast_app_dir
        / "data"
        / "output"
        / "test_df_OITM_Ventas.xlsx"
    )

    ruta_output = (
        forecast_app_dir
        / "data"
        / "output"
        / "test_df_OITM_Ventas_commercial_rules.xlsx"
    )

    print("=" * 80)
    print("PRUEBA COMMERCIAL_RULES.PY")
    print("=" * 80)

    print("Ruta input:", ruta_input)
    print("Existe input:", ruta_input.exists())

    df = pd.read_excel(ruta_input)

    config_fechas = construir_configuracion_fechas(
        fecha_fin=None,
        fecha_inicio_visual="2024-01-01",
        meses_historico=24
    )

    df_commercial = aplicar_reglas_comerciales(
        df=df,
        config_fechas=config_fechas,
        meses_historico=24
    )

    mostrar_resumen_reglas_comerciales(df_commercial)

    ruta_output.parent.mkdir(parents=True, exist_ok=True)

    df_commercial.to_excel(
        ruta_output,
        index=False
    )

    print("\nArchivo exportado correctamente ✅")
    print("Ruta output:", ruta_output)


if __name__ == "__main__":
    main()