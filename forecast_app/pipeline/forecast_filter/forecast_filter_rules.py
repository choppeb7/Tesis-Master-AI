import numpy as np
import pandas as pd


def clasificar_segmento_forecast(
    df,
    umbral_auto_meses_con_venta=6,
    umbral_auto_frecuencia_pct=25,
    #umbral_auto_facturas=6,
    umbral_manual_meses_min=2,
    umbral_manual_meses_max=5,
    #umbral_manual_facturas_min=2,
    #umbral_manual_facturas_max=5
):
    df = df.copy()

    columnas_numericas = [
        "total_unidades_vendidas_24m",
        "venta_promedio_mensual_24m",
        "meses_con_venta_24m",
        "frecuencia_venta_24m_pct",
        "conteo_facturas_24m",
        "alcance_inventario_24m"
    ]

    for col in columnas_numericas:
        if col not in df.columns:
            df[col] = 0

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        ).fillna(0)

    if "clasificacion_alcance_inventario_24m" not in df.columns:
        df["clasificacion_alcance_inventario_24m"] = ""

    if "tipo_abastecimiento" not in df.columns:
        df["tipo_abastecimiento"] = ""

    df["clasificacion_alcance_inventario_24m"] = (
        df["clasificacion_alcance_inventario_24m"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df["tipo_abastecimiento"] = (
        df["tipo_abastecimiento"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # ============================================================
    # Condiciones base
    # ============================================================

    condicion_con_venta = (
        df["total_unidades_vendidas_24m"] > 0
    )

    condicion_sin_venta = (
        df["total_unidades_vendidas_24m"] <= 0
    )

    condicion_infinito = (
        df["clasificacion_alcance_inventario_24m"] == "Infinito"
    )

    condicion_infinito_nuevo = (
        df["clasificacion_alcance_inventario_24m"] == "Infinito nuevo"
    )

    condicion_no_infinito = (
        ~df["clasificacion_alcance_inventario_24m"]
        .isin(["Infinito", "Infinito nuevo"])
    )

    # ============================================================
    # Forecast automático
    # ============================================================

    condicion_forecast_automatico = (
        condicion_con_venta
        & condicion_no_infinito
        & (df["meses_con_venta_24m"] >= umbral_auto_meses_con_venta)
        & (df["frecuencia_venta_24m_pct"] >= umbral_auto_frecuencia_pct)
        #& (df["conteo_facturas_24m"] >= umbral_auto_facturas)
    )

    # ============================================================
    # Forecast por revisión manual
    # ============================================================

    condicion_demanda_manual = (
        condicion_con_venta
        & condicion_no_infinito
        & ~condicion_forecast_automatico
        & (
            df["meses_con_venta_24m"].between(
                umbral_manual_meses_min,
                umbral_manual_meses_max,
                inclusive="both"
            )
            | df["tipo_abastecimiento"].isin([
                "stock_regular",
                "stock_puntual"
            ])
        )
    )

    # ============================================================
    # Pedido especial
    # ============================================================

    condicion_pedido_especial = (
        condicion_con_venta
        & condicion_no_infinito
        & ~condicion_forecast_automatico
        & ~condicion_demanda_manual
    )

    # ============================================================
    # Clasificación final
    # ============================================================

    df["segmento_forecast"] = np.select(
        [
            condicion_forecast_automatico,
            condicion_demanda_manual,
            condicion_pedido_especial,
            condicion_sin_venta & condicion_infinito_nuevo,
            condicion_sin_venta & condicion_infinito,
            condicion_sin_venta
        ],
        [
            "forecast_automatico",
            "forecast_revision_manual",
            "pedido_especial",
            "sin_forecast_infinito_nuevo",
            "sin_forecast_infinito",
            "sin_forecast_sin_demanda"
        ],
        default="revisar"
    )

    # ============================================================
    # Booleanos derivados
    # ============================================================

    df["aplica_forecast_automatico"] = (
        df["segmento_forecast"] == "forecast_automatico"
    )

    df["aplica_forecast_revision_manual"] = (
        df["segmento_forecast"] == "forecast_revision_manual"
    )

    df["aplica_forecast_total"] = (
        df["aplica_forecast_automatico"]
        | df["aplica_forecast_revision_manual"]
    )

    return df