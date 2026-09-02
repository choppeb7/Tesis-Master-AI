import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from statsforecast import StatsForecast
from statsforecast.models import CrostonClassic, CrostonOptimized, CrostonSBA, IMAPA, TSB
from tbats import TBATS
from sklearn.metrics import mean_squared_error, mean_absolute_error
from statsforecast import StatsForecast
from statsforecast.models import AutoTBATS
import warnings

# ===============================================================
# Funcion clave funcion Listado de modelos Statsforecast a evaluar
# ===============================================================

def obtener_modelos_statsforecast():
    return {
        "CrostonClassic": CrostonClassic(),
        "CrostonOptimized": CrostonOptimized(),
        "CrostonSBA": CrostonSBA(),
        "IMAPA": IMAPA(),
        "TSB": TSB(alpha_d=0.1, alpha_p=0.1)
    }


# ===============================================================
# Funcion clave funcion Listado de modelos Statsforecast a evaluar
# ===============================================================

def calcular_dummy_promedio(df_train, ventana=24):
    df_promedio = (
        df_train
        .sort_values(["unique_id", "ds"])
        .groupby("unique_id", group_keys=False)
        .tail(ventana)
        .groupby("unique_id", as_index=False)
        .agg(Dummy_promedio_24m=("y", "mean"))
    )

    return df_promedio