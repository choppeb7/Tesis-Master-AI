# ============================================================
# Construir dataframe consolidado para graficar:
# entrenamiento + validación + forecast futuro
# ============================================================
import pandas as pd
import numpy as np
from pipeline.forecast import predecir_best_model_por_articulo

def construir_df_forecast_visualizacion(
    df_inferencia,
    df_best_model,
    meses_evaluacion=6,
    meses_forecast_futuro=6,
    freq="ME",
    redondeo=None
):
    """
    Construye un dataframe final para graficar la serie real,
    la predicción en validación y el forecast futuro.

    Requiere:
    - df_inferencia: columnas ["unique_id", "ds", "y"]
    - df_best_model: columnas ["unique_id", "best_model"]

    Retorna:
    - df_forecast_visual
    - info_split
    """

    df_temp = df_inferencia.copy()

    # ------------------------------------------------------------
    # Validaciones básicas
    # ------------------------------------------------------------

    columnas_requeridas = {"unique_id", "ds", "y"}
    faltantes = columnas_requeridas - set(df_temp.columns)

    if faltantes:
        raise ValueError(f"Faltan columnas requeridas en df_inferencia: {faltantes}")

    df_temp["ds"] = pd.to_datetime(df_temp["ds"])
    df_temp["y"] = pd.to_numeric(df_temp["y"], errors="coerce").fillna(0)

    df_temp = df_temp.sort_values(["ds", "unique_id"]).reset_index(drop=True)

    df_best_model = (
        df_best_model[["unique_id", "best_model"]]
        .drop_duplicates(subset=["unique_id"])
        .copy()
    )

    # ------------------------------------------------------------
    # Definir fechas de train y validación
    # ------------------------------------------------------------

    fechas_disponibles = (
        df_temp["ds"]
        .drop_duplicates()
        .sort_values()
        .tolist()
    )

    if meses_evaluacion >= len(fechas_disponibles):
        raise ValueError(
            "meses_evaluacion no puede ser mayor o igual al total de meses disponibles."
        )

    fechas_validacion = fechas_disponibles[-meses_evaluacion:]
    fechas_train = fechas_disponibles[:-meses_evaluacion]

    fecha_inicio_train = min(fechas_train)
    fecha_fin_train = max(fechas_train)

    fecha_inicio_validacion = min(fechas_validacion)
    fecha_fin_validacion = max(fechas_validacion)

    df_train = df_temp[df_temp["ds"].isin(fechas_train)].copy()
    df_validacion_real = df_temp[df_temp["ds"].isin(fechas_validacion)].copy()

    # ------------------------------------------------------------
    # Predicción sobre validación
    # ------------------------------------------------------------
    # Aquí entrenamos únicamente con df_train y predecimos los meses
    # de validación para poder comparar y_real vs y_pred.
    # ------------------------------------------------------------

    df_pred_validacion = predecir_best_model_por_articulo(
        df_train=df_train[["unique_id", "ds", "y"]],
        df_best_model=df_best_model,
        h=meses_evaluacion,
        freq=freq,
        redondeo=redondeo
    )

    df_pred_validacion = df_pred_validacion.merge(
        df_validacion_real[["unique_id", "ds", "y"]],
        on=["unique_id", "ds"],
        how="left",
        validate="one_to_one"
    )

    df_pred_validacion = df_pred_validacion.rename(
        columns={"y": "y_real"}
    )

    df_pred_validacion["periodo"] = "Validación"

    # ------------------------------------------------------------
    # Forecast futuro
    # ------------------------------------------------------------
    # Aquí usamos todo el historial real disponible para proyectar
    # los próximos meses futuros.
    # ------------------------------------------------------------

    df_pred_futuro = predecir_best_model_por_articulo(
        df_train=df_temp[["unique_id", "ds", "y"]],
        df_best_model=df_best_model,
        h=meses_forecast_futuro,
        freq=freq,
        redondeo=redondeo
    )

    df_pred_futuro["y_real"] = np.nan
    df_pred_futuro["periodo"] = "Forecast futuro"

    # ------------------------------------------------------------
    # Dataset de entrenamiento para graficar
    # ------------------------------------------------------------

    df_train_plot = df_train.merge(
        df_best_model,
        on="unique_id",
        how="left",
        validate="many_to_one"
    )

    df_train_plot = df_train_plot.rename(
        columns={"y": "y_real"}
    )

    df_train_plot["y_pred"] = np.nan
    df_train_plot["periodo"] = "Entrenamiento"

    # ------------------------------------------------------------
    # Ordenar columnas comunes
    # ------------------------------------------------------------

    columnas_finales = [
        "unique_id",
        "ds",
        "periodo",
        "best_model",
        "y_real",
        "y_pred"
    ]

    df_train_plot = df_train_plot[columnas_finales]
    df_pred_validacion = df_pred_validacion[columnas_finales]
    df_pred_futuro = df_pred_futuro[columnas_finales]

    # ------------------------------------------------------------
    # Consolidar todo
    # ------------------------------------------------------------

    df_forecast_visual = pd.concat(
        [
            df_train_plot,
            df_pred_validacion,
            df_pred_futuro
        ],
        ignore_index=True
    )

    df_forecast_visual = df_forecast_visual.sort_values(
        ["unique_id", "ds"]
    ).reset_index(drop=True)

    # ------------------------------------------------------------
    # Información del split
    # ------------------------------------------------------------

    info_split = {
        "fecha_inicio_train": fecha_inicio_train,
        "fecha_fin_train": fecha_fin_train,
        "fecha_inicio_validacion": fecha_inicio_validacion,
        "fecha_fin_validacion": fecha_fin_validacion,
        "fecha_inicio_forecast": df_pred_futuro["ds"].min(),
        "fecha_fin_forecast": df_pred_futuro["ds"].max(),
        "meses_train": len(fechas_train),
        "meses_validacion": len(fechas_validacion),
        "meses_forecast_futuro": meses_forecast_futuro,
        "cantidad_articulos": df_temp["unique_id"].nunique()
    }

    return df_forecast_visual, info_split