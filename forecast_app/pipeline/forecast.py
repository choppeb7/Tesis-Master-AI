# ============================================================
# Predicción usando best_model por artículo
# ============================================================

import numpy as np
import pandas as pd
import re

from statsforecast import StatsForecast
from statsforecast.models import CrostonClassic, CrostonOptimized, CrostonSBA, IMAPA, TSB


#============================================================
# Predicción usando best_model por artículo
# ============================================================

import numpy as np
import pandas as pd
import re

from statsforecast import StatsForecast
from statsforecast.models import CrostonClassic, CrostonOptimized, CrostonSBA, IMAPA, TSB


def predecir_best_model_por_articulo(
    df_train,
    df_best_model,
    h,
    freq="ME",
    redondeo=None
):
    """
    Genera predicciones usando el modelo ganador de cada artículo.

    df_train:
    - unique_id
    - ds
    - y

    df_best_model:
    - unique_id
    - best_model

    Retorna:
    - unique_id
    - ds
    - best_model
    - y_pred
    """

    df_train = df_train.copy()
    df_best_model = df_best_model[["unique_id", "best_model"]].drop_duplicates().copy()

    df_train["ds"] = pd.to_datetime(df_train["ds"])
    df_train["y"] = pd.to_numeric(df_train["y"], errors="coerce").fillna(0)

    modelos_ganadores = df_best_model["best_model"].dropna().unique().tolist()

    mapa_modelos_stats = {
        "CrostonClassic": CrostonClassic(),
        "CrostonOptimized": CrostonOptimized(),
        "CrostonSBA": CrostonSBA(),
        "IMAPA": IMAPA(),
        "TSB": TSB(alpha_d=0.1, alpha_p=0.1)
    }

    modelos_stats_necesarios = [
        mapa_modelos_stats[m]
        for m in modelos_ganadores
        if m in mapa_modelos_stats
    ]

    unique_ids = df_train["unique_id"].drop_duplicates().sort_values()

    fecha_fin_train = df_train["ds"].max()
#Crearr fechas futuras a predecir 
    fechas_pred = pd.date_range(
        start=fecha_fin_train + pd.offsets.MonthEnd(1),
        periods=h,
        freq=freq
    )
#Crear todas las combinaciones posibles a nivel de dos columnas entre articulo y fechas futuras
    df_base_pred = pd.MultiIndex.from_product(
        [unique_ids, fechas_pred],
        names=["unique_id", "ds"]
    ).to_frame(index=False)

    df_pred_all = df_base_pred.copy()

    # ------------------------------------------------------------
    # Modelos StatsForecast
    # ------------------------------------------------------------

    if len(modelos_stats_necesarios) > 0:

        sf = StatsForecast(
            models=modelos_stats_necesarios,
            freq=freq,
            n_jobs=-1
        )

        df_pred_stats = sf.forecast(
            df=df_train[["unique_id", "ds", "y"]],
            h=h
        )

        df_pred_all = df_pred_all.merge(
            df_pred_stats,
            on=["unique_id", "ds"],
            how="left"
        )

    # ------------------------------------------------------------
    # Modelos dummy de promedio
    # ------------------------------------------------------------

    modelos_dummy = [
        modelo for modelo in modelos_ganadores
        if "promedio" in str(modelo).lower()
    ]

    for modelo_dummy in modelos_dummy:

        match = re.search(r"(\d+)m", str(modelo_dummy).lower())

        if match:
            ventana = int(match.group(1))
        else:
            ventana = 24

        df_promedio = (
            df_train
            .sort_values(["unique_id", "ds"])
            .groupby("unique_id", group_keys=False)
            .tail(ventana)
            .groupby("unique_id", as_index=False)
            .agg(promedio_dummy=("y", "mean"))
        )

        df_dummy_pred = df_base_pred.merge(
            df_promedio,
            on="unique_id",
            how="left"
        )

        df_dummy_pred[modelo_dummy] = df_dummy_pred["promedio_dummy"].fillna(0)

        df_pred_all = df_pred_all.merge(
            df_dummy_pred[["unique_id", "ds", modelo_dummy]],
            on=["unique_id", "ds"],
            how="left"
        )

    # ------------------------------------------------------------
    # Seleccionar la columna correspondiente al best_model
    # ------------------------------------------------------------

    df_pred_all = df_pred_all.merge(
        df_best_model,
        on="unique_id",
        how="left",
        validate="many_to_one"
    )

    def seleccionar_y_pred(row):
        modelo = row["best_model"]

        if modelo in row.index:
            return row[modelo]
        else:
            return np.nan

    df_pred_all["y_pred"] = df_pred_all.apply(
        seleccionar_y_pred,
        axis=1
    )

    df_pred_all["y_pred"] = pd.to_numeric(
        df_pred_all["y_pred"],
        errors="coerce"
    ).fillna(0)

    df_pred_all["y_pred"] = df_pred_all["y_pred"].clip(lower=0)

    if redondeo == "ceil":
        df_pred_all["y_pred"] = np.ceil(df_pred_all["y_pred"]).astype(int)

    elif redondeo == "round":
        df_pred_all["y_pred"] = df_pred_all["y_pred"].round(0).astype(int)

    df_pred = df_pred_all[
        ["unique_id", "ds", "best_model", "y_pred"]
    ].copy()

    return df_pred