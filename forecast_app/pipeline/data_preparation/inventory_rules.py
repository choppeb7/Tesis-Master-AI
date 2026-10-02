from pathlib import Path
import pandas as pd
import numpy as np


COLUMNAS_NUMERICAS_INVENTARIO = [
    "stock_en_mano",
    "stock_comprometido",
    "stock_en_pedido_transito",
    "total_unidades_vendidas_24m",
    "lead_time_promedio_dias",
    "meses_promedio_entre_compras_24m",
    "precio_referencia"
]


def asegurar_columnas_numericas_inventario(df):
    """
    Asegura que las columnas necesarias para reglas de inventario sean numéricas.

    Si una columna no existe, se crea en cero para evitar que el pipeline falle.
    """

    df = df.copy()

    for columna in COLUMNAS_NUMERICAS_INVENTARIO:
        if columna not in df.columns:
            print(f"Advertencia: no existe columna '{columna}'. Se creará con valor 0.")
            df[columna] = 0

        df[columna] = pd.to_numeric(
            df[columna],
            errors="coerce"
        ).fillna(0)

    return df


def calcular_stock_disponible_proyectado(df):
    """
    Calcula stock disponible proyectado:

    stock_en_mano - stock_comprometido + stock_en_pedido_transito
    """

    df = df.copy()

    df["stock_disponible_proyectado"] = (
        df["stock_en_mano"]
        - df["stock_comprometido"]
        + df["stock_en_pedido_transito"]
    )

    return df


def calcular_venta_promedio_mensual(
    df,
    meses_historico=24
):
    """
    Calcula venta promedio mensual de los últimos N meses.

    venta_promedio_mensual_24m = total_unidades_vendidas_24m / 24
    """

    df = df.copy()

    df["venta_promedio_mensual_24m"] = (
        df["total_unidades_vendidas_24m"] / meses_historico
    )

    return df


def clasificar_rango_meses(serie_meses):
    """
    Clasifica una serie numérica de meses en rangos estándar.
    """

    return np.select(
        [
            serie_meses <= 6,
            (serie_meses > 6) & (serie_meses <= 12),
            (serie_meses > 12) & (serie_meses <= 24),
            (serie_meses > 24) & (serie_meses <= 36),
            serie_meses > 36
        ],
        [
            "0 a 6 meses",
            "6 a 12 meses",
            "12 a 24 meses",
            "24 a 36 meses",
            "Mayor a 36 meses"
        ],
        default="Sin clasificar"
    )


def clasificar_rango_alcance_normal(serie_meses):
    """
    Clasifica el alcance de inventario en rangos de meses
    para artículos que sí tuvieron venta en los últimos 24 meses.
    """

    return np.select(
        [
            serie_meses <= 6,
            (serie_meses > 6) & (serie_meses <= 12),
            (serie_meses > 12) & (serie_meses <= 24),
            (serie_meses > 24) & (serie_meses <= 36),
            serie_meses > 36
        ],
        [
            "0 a 6 meses",
            "6 a 12 meses",
            "12 a 24 meses",
            "24 a 36 meses",
            "Mayor a 36 meses"
        ],
        default="Sin clasificar"
    )


def calcular_alcance_inventario(
    df,
    fecha_fin=None,
    meses_compra_reciente=12,
    usar_stock_disponible_proyectado=False
):
    """
    Calcula el alcance de inventario únicamente para artículos con stock.

    Lógica:

    1. Si el artículo tiene stock y tuvo venta en los últimos 24 meses:
        alcance = stock_base / venta_promedio_mensual_24m

        Clasificación:
        - 0 a 6 meses
        - 6 a 12 meses
        - 12 a 24 meses
        - 24 a 36 meses
        - Mayor a 36 meses

    2. Si el artículo tiene stock, pero NO tuvo venta en los últimos 24 meses:
        alcance = infinito

        Si la última compra fue reciente:
            clasificación = Infinito nuevo

        Si la última compra no fue reciente o no hay fecha:
            clasificación = Infinito
    """

    df = df.copy()

    # ============================================================
    # 1. Fecha de referencia
    # ============================================================

    if fecha_fin is None:
        fecha_fin = pd.Timestamp.today().normalize()
    else:
        fecha_fin = pd.Timestamp(fecha_fin).normalize()

    fecha_corte_compra_reciente = fecha_fin - pd.DateOffset(
        months=meses_compra_reciente
    )

    # ============================================================
    # 2. Asegurar columnas necesarias
    # ============================================================

    columnas_numericas = [
        "total_unidades_vendidas_24m",
        "venta_promedio_mensual_24m",
        "stock_en_mano"
    ]

    for columna in columnas_numericas:
        if columna not in df.columns:
            df[columna] = 0

        df[columna] = pd.to_numeric(
            df[columna],
            errors="coerce"
        ).fillna(0)

    if "stock_disponible_proyectado" not in df.columns:
        df["stock_disponible_proyectado"] = df["stock_en_mano"]

    df["stock_disponible_proyectado"] = pd.to_numeric(
        df["stock_disponible_proyectado"],
        errors="coerce"
    ).fillna(0)

    if "ultima_fecha_compra" not in df.columns:
        df["ultima_fecha_compra"] = pd.NaT

    df["ultima_fecha_compra"] = pd.to_datetime(
        df["ultima_fecha_compra"],
        errors="coerce"
    )

    # ============================================================
    # 3. Filtrar únicamente artículos con stock físico
    # ============================================================

    df = df[df["stock_en_mano"] > 0].copy()

    # ============================================================
    # 4. Definir stock base para cálculo de alcance
    # ============================================================

    if usar_stock_disponible_proyectado:
        columna_stock_base = "stock_disponible_proyectado"
    else:
        columna_stock_base = "stock_en_mano"

    df["stock_base_alcance"] = (
        df[columna_stock_base]
        .clip(lower=0)
    )

    # ============================================================
    # 5. Meses desde última compra
    # ============================================================

    df["meses_desde_ultima_compra"] = np.where(
        df["ultima_fecha_compra"].notna(),
        (fecha_fin - df["ultima_fecha_compra"]).dt.days / 30.4375,
        np.nan
    )

    df["meses_desde_ultima_compra"] = pd.to_numeric(
        df["meses_desde_ultima_compra"],
        errors="coerce"
    ).clip(lower=0)

    # ============================================================
    # 6. Inicializar columnas
    # ============================================================

    df["alcance_inventario_24m"] = np.nan
    df["clasificacion_base_alcance_inventario_24m"] = ""
    df["clasificacion_alcance_inventario_24m"] = ""

    # ============================================================
    # 7. Máscaras principales
    # ============================================================

    mask_con_venta = (
        (df["total_unidades_vendidas_24m"] > 0)
        & (df["venta_promedio_mensual_24m"] > 0)
    )

    mask_sin_venta = (
        df["total_unidades_vendidas_24m"] <= 0
    )

    mask_compra_reciente = (
        df["ultima_fecha_compra"].notna()
        & (df["ultima_fecha_compra"] >= fecha_corte_compra_reciente)
    )

    mask_infinito_nuevo = (
        mask_sin_venta
        & mask_compra_reciente
    )

    mask_infinito = (
        mask_sin_venta
        & ~mask_compra_reciente
    )

    # ============================================================
    # 8. Caso con venta: alcance real
    # ============================================================

    df.loc[mask_con_venta, "alcance_inventario_24m"] = (
        df.loc[mask_con_venta, "stock_base_alcance"]
        / df.loc[mask_con_venta, "venta_promedio_mensual_24m"]
    )

    df.loc[
        mask_con_venta,
        "clasificacion_base_alcance_inventario_24m"
    ] = "Normal"

    df.loc[
        mask_con_venta,
        "clasificacion_alcance_inventario_24m"
    ] = clasificar_rango_alcance_normal(
        df.loc[mask_con_venta, "alcance_inventario_24m"]
    )

    # ============================================================
    # 9. Caso sin venta, con stock y compra reciente
    # ============================================================

    df.loc[
        mask_infinito_nuevo,
        "alcance_inventario_24m"
    ] = np.inf

    df.loc[
        mask_infinito_nuevo,
        "clasificacion_base_alcance_inventario_24m"
    ] = "Infinito nuevo"

    df.loc[
        mask_infinito_nuevo,
        "clasificacion_alcance_inventario_24m"
    ] = "Infinito nuevo"

    # ============================================================
    # 10. Caso sin venta, con stock y sin compra reciente
    # ============================================================

    df.loc[
        mask_infinito,
        "alcance_inventario_24m"
    ] = np.inf

    df.loc[
        mask_infinito,
        "clasificacion_base_alcance_inventario_24m"
    ] = "Infinito"

    df.loc[
        mask_infinito,
        "clasificacion_alcance_inventario_24m"
    ] = "Infinito"

    return df


def agregar_meses_objetivo_cobertura(
    df,
    ruta_fabricantes=None,
    df_fabricantes=None,
    valor_defecto=0
):
    """
    Agrega meses_objetivo_cobertura desde el archivo de fabricantes.

    Cruce:
    marca_fabricante_normalizada -> meses_objetivo_cobertura
    """

    df = df.copy()

    if "meses_objetivo_cobertura" in df.columns:
        df = df.drop(columns=["meses_objetivo_cobertura"])

    if ruta_fabricantes is None:
        project_root = Path(__file__).resolve().parents[3]

        ruta_fabricantes = (
            project_root
            / "forecast_app"
            / "data"
            / "input"
            / "fabricantes_repuestos_cerosa.xlsx"
        )

    ruta_fabricantes = Path(ruta_fabricantes)

    if not ruta_fabricantes.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo de fabricantes en la ruta: {ruta_fabricantes}"
            )

    df_fabricantes = pd.read_excel(ruta_fabricantes)

    columnas_requeridas = [
        "marca_fabricante",
        "meses_objetivo_cobertura"
    ]

    columnas_faltantes = [
        columna
        for columna in columnas_requeridas
        if columna not in df_fabricantes.columns
    ]

    if columnas_faltantes:
        raise ValueError(
            "Faltan columnas en archivo de fabricantes: "
            + ", ".join(columnas_faltantes)
        )

    df["marca_fabricante_normalizada"] = (
        df["marca_fabricante"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df_parametros = df_fabricantes[columnas_requeridas].copy()

    df_parametros["marca_fabricante_normalizada"] = (
        df_parametros["marca_fabricante"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df_parametros["meses_objetivo_cobertura"] = pd.to_numeric(
        df_parametros["meses_objetivo_cobertura"],
        errors="coerce"
    )

    df_parametros = df_parametros[
        ["marca_fabricante_normalizada", "meses_objetivo_cobertura"]
    ].drop_duplicates(subset=["marca_fabricante_normalizada"])

    df = df.merge(
        df_parametros,
        on="marca_fabricante_normalizada",
        how="left"
    )

    df["requiere_revision_parametro_cobertura"] = (
        df["meses_objetivo_cobertura"].isna()
    )

    df["meses_objetivo_cobertura"] = (
        df["meses_objetivo_cobertura"]
        .fillna(valor_defecto)
    )

    return df


def calcular_politica_stock(
    df,
    factor_seguridad_meses=0.5,
    dias_por_mes=30
):
    """
    Calcula:
    - lead_time_meses
    - factor_seguridad_meses
    - stock_seguridad
    - stock_minimo
    - punto_stock_reorden
    """

    df = df.copy()

    df["lead_time_meses"] = (
        df["lead_time_promedio_dias"] / dias_por_mes
    )

    df["factor_seguridad_meses"] = factor_seguridad_meses

    df["stock_seguridad"] = (
        df["venta_promedio_mensual_24m"]
        * df["factor_seguridad_meses"]
    )

    df["stock_minimo"] = (
        df["venta_promedio_mensual_24m"]
        * df["lead_time_meses"]
    )

    df["punto_stock_reorden"] = (
        df["stock_minimo"]
        + df["stock_seguridad"]
    )

    return df


def calcular_stock_maximo_y_sugerido(df):
    """
    Calcula:
    - stock_maximo
    - cantidad_sugerida_pedir
    - meses_hasta_reorden
    """

    df = df.copy()

    # Si no tuvo venta promedio, no se recomienda cobertura automática.
    df.loc[
        df["venta_promedio_mensual_24m"] == 0,
        "meses_objetivo_cobertura"
    ] = 0

    df["stock_maximo"] = (
        df["venta_promedio_mensual_24m"]
        * (
            df["meses_objetivo_cobertura"]
            + df["factor_seguridad_meses"]
        )
    )

    df["cantidad_sugerida_pedir"] = np.where(
        df["stock_disponible_proyectado"] <= df["punto_stock_reorden"],
        df["stock_maximo"] - df["stock_disponible_proyectado"],
        0
    )

    df["cantidad_sugerida_pedir"] = (
        df["cantidad_sugerida_pedir"]
        .clip(lower=0)
    )

    df["meses_hasta_reorden"] = np.where(
        df["venta_promedio_mensual_24m"] > 0,
        (
            df["stock_disponible_proyectado"]
            - df["punto_stock_reorden"]
        ) / df["venta_promedio_mensual_24m"],
        np.inf
    )

    return df


def calcular_decision_compra(
    df,
    umbral_revision_compra_meses=2
):
    """
    Calcula la decisión de compra del artículo.

    Reglas:
    1. Sin venta 24M.
    2. Sin stock disponible proyectado.
    3. Stock disponible menor o igual al punto de reorden.
    4. Próximo a punto de reorden.
    5. Sobreinventario.
    6. No comprar todavía.
    """

    df = df.copy()

    df["decision_compra"] = np.select(
        [
            df["venta_promedio_mensual_24m"] == 0,

            df["stock_disponible_proyectado"] <= 0,

            df["stock_disponible_proyectado"] <= df["punto_stock_reorden"],

            (
                (df["stock_disponible_proyectado"] > df["punto_stock_reorden"])
                & (df["meses_hasta_reorden"] > 0)
                & (df["meses_hasta_reorden"] <= umbral_revision_compra_meses)
            ),

            df["alcance_inventario_24m"] > (
                df["meses_objetivo_cobertura"]
                + df["factor_seguridad_meses"]
            )
        ],
        [
            "No comprar - sin venta 24M",
            "Comprar urgente - sin stock disponible",
            "Comprar urgente - stock mínimo alcanzado",
            "Evaluar compra - próximo a punto de reorden",
            "No comprar - sobreinventario"
        ],
        default="No comprar todavía"
    )

    return df


def calcular_metricas_riesgo(df):
    """
    Calcula métricas económicas de riesgo para revisión posterior.

    Usa precio_referencia calculado en commercial_rules.py.
    """

    df = df.copy()

    if "precio_referencia" not in df.columns:
        df["precio_referencia"] = 0

    df["deficit_punto_reorden"] = (
        df["punto_stock_reorden"]
        - df["stock_disponible_proyectado"]
    )

    df["deficit_punto_reorden_positivo"] = (
        df["deficit_punto_reorden"]
        .clip(lower=0)
    )

    df["monto_riesgo_inmediato"] = (
        df["deficit_punto_reorden_positivo"]
        * df["precio_referencia"]
    )

    df["valor_venta_mensual_24m"] = (
        df["venta_promedio_mensual_24m"]
        * df["precio_referencia"]
    )

    decisiones_en_revision = [
        "Comprar urgente - sin stock disponible",
        "Comprar urgente - stock mínimo alcanzado",
        "Evaluar compra - próximo a punto de reorden"
    ]

    df["venta_mensual_en_revision"] = np.where(
        df["decision_compra"].isin(decisiones_en_revision),
        df["valor_venta_mensual_24m"],
        0
    )

    df["monto_riesgo_proximo"] = np.where(
        df["decision_compra"] == "Evaluar compra - próximo a punto de reorden",
        df["valor_venta_mensual_24m"],
        0
    )

    return df


def aplicar_reglas_inventario(
    df,
    ruta_fabricantes=None,
    df_fabricantes=None,
    fecha_fin=None,
    meses_historico=24,
    factor_seguridad_meses=0.5,
    umbral_revision_compra_meses=2
):
    """
    Aplica todas las reglas de inventario y reabastecimiento.
    """

    df = df.copy()

    df = asegurar_columnas_numericas_inventario(df)

    df = calcular_stock_disponible_proyectado(df)

    df = calcular_venta_promedio_mensual(
        df=df,
        meses_historico=meses_historico
    )

    df = calcular_alcance_inventario(
        df=df,
        fecha_fin=fecha_fin,
        meses_compra_reciente=12
    )

    df = agregar_meses_objetivo_cobertura(
        df=df,
        ruta_fabricantes=ruta_fabricantes,
        df_fabricantes=df_fabricantes,
        valor_defecto=0
    )

    df = calcular_politica_stock(
        df=df,
        factor_seguridad_meses=factor_seguridad_meses
    )

    df = calcular_stock_maximo_y_sugerido(df)

    df = calcular_decision_compra(
        df=df,
        umbral_revision_compra_meses=umbral_revision_compra_meses
    )

    df = calcular_metricas_riesgo(df)

    return df


def mostrar_resumen_reglas_inventario(df):
    """
    Muestra resumen de reglas de inventario.
    """

    print("=" * 80)
    print("RESUMEN REGLAS INVENTARIO")
    print("=" * 80)

    print(f"Filas: {df.shape[0]:,}")
    print(f"Columnas: {df.shape[1]:,}")

    print("\nClasificación alcance inventario:")
    print(df["clasificacion_alcance_inventario_24m"].value_counts(dropna=False))

    print("\nDecisión de compra:")
    print(df["decision_compra"].value_counts(dropna=False))

    print("\nCantidad sugerida total a pedir:")
    print(round(df["cantidad_sugerida_pedir"].sum(), 2))

    print("\nMonto riesgo inmediato:")
    print(round(df["monto_riesgo_inmediato"].sum(), 2))

    print("\nMonto riesgo próximo:")
    print(round(df["monto_riesgo_proximo"].sum(), 2))


def main():
    """
    Prueba directa de inventory_rules.py usando el archivo generado por
    commercial_rules.py.
    """

    project_root = Path(__file__).resolve().parents[3]
    forecast_app_dir = project_root / "forecast_app"

    ruta_input = (
        forecast_app_dir
        / "data"
        / "output"
        / "test_df_OITM_Ventas_commercial_rules.xlsx"
    )

    ruta_fabricantes = (
        forecast_app_dir
        / "data"
        / "input"
        / "fabricantes_repuestos_cerosa.xlsx"
    )

    ruta_output = (
        forecast_app_dir
        / "data"
        / "output"
        / "test_df_OITM_Ventas_inventory_rules.xlsx"
    )

    print("=" * 80)
    print("PRUEBA INVENTORY_RULES.PY")
    print("=" * 80)

    print("Ruta input:", ruta_input)
    print("Existe input:", ruta_input.exists())

    print("Ruta fabricantes:", ruta_fabricantes)
    print("Existe fabricantes:", ruta_fabricantes.exists())

    df = pd.read_excel(ruta_input)

    df_inventory = aplicar_reglas_inventario(
        df=df,
        ruta_fabricantes=ruta_fabricantes,
        fecha_fin=None,
        meses_historico=24,
        factor_seguridad_meses=0.5,
        umbral_revision_compra_meses=2
    )

    mostrar_resumen_reglas_inventario(df_inventory)

    ruta_output.parent.mkdir(parents=True, exist_ok=True)

    df_inventory.to_excel(
        ruta_output,
        index=False
    )

    print("\nArchivo exportado correctamente ✅")
    print("Ruta output:", ruta_output)


if __name__ == "__main__":
    main()