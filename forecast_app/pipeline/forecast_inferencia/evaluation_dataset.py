# ============================================================
# Generar dataframe de evaluación en formato largo
# ============================================================

import pandas as pd
import numpy as np

from statsforecast import StatsForecast
from statsforecast.models import (
    CrostonClassic,
    CrostonOptimized,
    CrostonSBA,
    IMAPA,
    TSB
)


def generar_df_eval_long(
    df_train,
    df_test,
    freq="ME",
    incluir_modelos_stats=True,
    incluir_dummy=True,
    ventana_dummy=24,
    redondeo=None
):
    """
    Genera el dataframe de evaluación en formato largo:

    unique_id | ds | y | modelo | y_pred

    Este dataframe queda listo para entrar en:
    evaluando_metricas_por_articulo_modelo(df_eval_long)

    Parámetros:
    - df_train: dataframe de entrenamiento con columnas unique_id, ds, y
    - df_test: dataframe de evaluación con columnas unique_id, ds, y
    - freq: frecuencia temporal. Para cierre de mes usar "ME"
    - incluir_modelos_stats: si True, calcula modelos Croston, IMAPA y TSB
    - incluir_dummy: si True, calcula Dummy_promedio_Xm
    - ventana_dummy: cantidad de meses usados para promedio histórico
    - redondeo:
        None    -> conserva decimales
        "ceil"  -> redondea hacia arriba
        "round" -> redondea al entero más cercano

    Retorna:
    - df_eval_long
    - df_eval_wide
    - columnas_modelos_evaluar
    """

    # ------------------------------------------------------------
    # Copias defensivas
    # ------------------------------------------------------------

    df_train = df_train.copy()
    df_test = df_test.copy()

    # ------------------------------------------------------------
    # Validaciones básicas
    # ------------------------------------------------------------

    columnas_requeridas = {"unique_id", "ds", "y"}

    faltantes_train = columnas_requeridas - set(df_train.columns)
    faltantes_test = columnas_requeridas - set(df_test.columns)

    if faltantes_train:
        raise ValueError(f"Faltan columnas en df_train: {faltantes_train}")

    if faltantes_test:
        raise ValueError(f"Faltan columnas en df_test: {faltantes_test}")

    # ------------------------------------------------------------
    # Asegurar tipos correctos
    # ------------------------------------------------------------

    df_train["ds"] = pd.to_datetime(df_train["ds"])
    df_test["ds"] = pd.to_datetime(df_test["ds"])

    df_train["y"] = pd.to_numeric(df_train["y"], errors="coerce").fillna(0)
    df_test["y"] = pd.to_numeric(df_test["y"], errors="coerce").fillna(0)

    df_train = df_train.sort_values(["unique_id", "ds"]).reset_index(drop=True)
    df_test = df_test.sort_values(["unique_id", "ds"]).reset_index(drop=True)

    # ------------------------------------------------------------
    # Definir horizonte de evaluación
    # ------------------------------------------------------------

    fechas_test = (
        df_test["ds"]
        .drop_duplicates()
        .sort_values()
        .tolist()
    )

    h = len(fechas_test)

    if h == 0:
        raise ValueError("df_test no contiene fechas de evaluación.")

    unique_ids = (
        df_test["unique_id"]
        .drop_duplicates()
        .sort_values()
    )

    # ------------------------------------------------------------
    # Crear base de predicción:
    # una fila por artículo y mes de evaluación
    # ------------------------------------------------------------

    df_base_pred = pd.MultiIndex.from_product(
        [unique_ids, fechas_test],
        names=["unique_id", "ds"]
    ).to_frame(index=False)

    # Agregamos y real del test
    df_eval_wide = df_base_pred.merge(
        df_test[["unique_id", "ds", "y"]],
        on=["unique_id", "ds"],
        how="left",
        validate="one_to_one"
    )

    df_eval_wide["y"] = pd.to_numeric(
        df_eval_wide["y"],
        errors="coerce"
    ).fillna(0)

    # ============================================================
    # 1. Modelos StatsForecast
    # ============================================================

    if incluir_modelos_stats:

        modelos_stats = [
            CrostonClassic(),
            CrostonOptimized(),
            CrostonSBA(),
            IMAPA(),
            TSB(alpha_d=0.1, alpha_p=0.1)
        ]

        sf = StatsForecast(
            models=modelos_stats,
            freq=freq,
            n_jobs=-1
        )

        df_pred_stats = sf.forecast(
            df=df_train[["unique_id", "ds", "y"]],
            h=h
        )

        df_pred_stats["ds"] = pd.to_datetime(df_pred_stats["ds"])

        df_eval_wide = df_eval_wide.merge(
            df_pred_stats,
            on=["unique_id", "ds"],
            how="left",
            validate="one_to_one"
        )

    # ============================================================
    # 2. Modelo Dummy promedio últimos X meses
    # ============================================================

    if incluir_dummy:

        nombre_dummy = f"Dummy_promedio_{ventana_dummy}m"

        df_promedio_dummy = (
            df_train
            .sort_values(["unique_id", "ds"])
            .groupby("unique_id", group_keys=False)
            .tail(ventana_dummy)
            .groupby("unique_id", as_index=False)
            .agg(promedio_dummy=("y", "mean"))
        )

        df_dummy_pred = df_base_pred.merge(
            df_promedio_dummy,
            on="unique_id",
            how="left"
        )

        df_dummy_pred[nombre_dummy] = (
            df_dummy_pred["promedio_dummy"]
            .fillna(0)
        )

        df_eval_wide = df_eval_wide.merge(
            df_dummy_pred[["unique_id", "ds", nombre_dummy]],
            on=["unique_id", "ds"],
            how="left",
            validate="one_to_one"
        )

    # ------------------------------------------------------------
    # Identificar columnas de modelos
    # ------------------------------------------------------------

    columnas_base = ["unique_id", "ds", "y"]

    columnas_modelos_evaluar = [
        col for col in df_eval_wide.columns
        if col not in columnas_base
    ]

    # ------------------------------------------------------------
    # Asegurar valores numéricos y no negativos
    # ------------------------------------------------------------

    for col in columnas_modelos_evaluar:
        df_eval_wide[col] = pd.to_numeric(
            df_eval_wide[col],
            errors="coerce"
        ).fillna(0)

        df_eval_wide[col] = df_eval_wide[col].clip(lower=0)

    # ------------------------------------------------------------
    # Redondeo opcional
    # ------------------------------------------------------------

    if redondeo == "ceil":
        for col in columnas_modelos_evaluar:
            df_eval_wide[col] = np.ceil(df_eval_wide[col]).astype(int)

    elif redondeo == "round":
        for col in columnas_modelos_evaluar:
            df_eval_wide[col] = df_eval_wide[col].round(0).astype(int)

    # ------------------------------------------------------------
    # Convertir a formato largo
    # ------------------------------------------------------------

    df_eval_long = df_eval_wide.melt(
        id_vars=["unique_id", "ds", "y"],
        value_vars=columnas_modelos_evaluar,
        var_name="modelo",
        value_name="y_pred"
    )

    df_eval_long["y"] = pd.to_numeric(
        df_eval_long["y"],
        errors="coerce"
    ).fillna(0)

    df_eval_long["y_pred"] = pd.to_numeric(
        df_eval_long["y_pred"],
        errors="coerce"
    ).fillna(0)

    df_eval_long = df_eval_long.sort_values(
        ["unique_id", "modelo", "ds"]
    ).reset_index(drop=True)

    return df_eval_long, df_eval_wide, columnas_modelos_evaluar