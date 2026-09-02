
import pandas as pd
import numpy as np


           


# =========================================================================================
# Filtrar dataframe por codigo de articulo para entrenar con dataframe y modelo definido
# =====================================================================================
def crear_df_por_articulo_modelo(df, codigo_articulo, modelo):
    """
    Crea un DataFrame filtrado por código de artículo y modelo.
    """
    df_filtrado = df[
        (df["unique_id"] == codigo_articulo) &
        (df["modelo"] == modelo)
    ].copy()
    
    return df_filtrado


from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score


# =========================================================================================
# Calculando metricas en articulo y modelo correspondiente a la iteracion 

# =====================================================================================
def calcular_metricas(df_articulo_modelo_filtrado):
    """
    Evalúa métricas de error para un DataFrame filtrado por artículo y modelo.
    """
    # Asegurar formato numérico
    df=df_articulo_modelo_filtrado.copy()
    df["y"] = pd.to_numeric(df["y"], errors="coerce").fillna(0)
    df["y_pred"] = pd.to_numeric(df["y_pred"], errors="coerce").fillna(0)
    venta_real_total = int(df["y"].sum())
    prediccion_total = int(df["y_pred"].sum())


    # Crear métricas de desempate

    bias_total_periodo_evaluacion=float(venta_real_total-prediccion_total)
    # abs_bias_total_periodo_evaluacio=bias_total_periodo_evaluacion.abs()

    # #df["bias_total"] = df["y"] - df["y_pred"]

    # #df["abs_bias_total"] = df["bias_total"].abs()
    if bias_total_periodo_evaluacion < 0:
        sesgo = "Sobrepronóstico"
    elif bias_total_periodo_evaluacion > 0:
        sesgo = "Subpronóstico"
    else:
        sesgo = "Exacto"


    # df["tipo_sesgo"] = np.where(
    #     df["bias_total"] > 0,
    #     "Subpronóstico",
    #     np.where(
    #         df["bias_total"] < 0,
    #         "Sobrepronóstico",
    #         "Exacto"
    #     )
    # )

    # Calcular métricas
    mse = mean_squared_error(df["y"], df["y_pred"])
    rmse = np.sqrt(mse)
    mae = np.abs(df["y"] - df["y_pred"]).mean()
    error_absoluto_total=mae * len(df)

    r2 = r2_score(df["y"], df["y_pred"])
    
    mape = np.mean(np.abs((df["y"] - df["y_pred"]) / df["y"].replace(0, np.nan))) * 100

     # WAPE estándar
    if venta_real_total != 0:
        wape = error_absoluto_total / venta_real_total * 100
    else:
        wape = np.nan

    # WAPE para ranking operativo
    # Si no hubo venta real y el modelo predijo 0, es perfecto.
    # Si no hubo venta real y el modelo predijo más de 0, lo castigamos con infinito.
    if venta_real_total == 0 and prediccion_total == 0:
        wape_ranking = 0
        caso_demanda_test = "Sin demanda real y predicción cero, Wappe perfecto "
    elif venta_real_total == 0 and prediccion_total > 0:
        wape_ranking = np.inf
        caso_demanda_test = "Sin demanda real en test con sobrepronóstico Wape infinito"
    else:
        wape_ranking = wape
        caso_demanda_test = "Con demanda real en test y pronóstico"


    Serie_filtrada_con_metricas = pd.Series({
        "unique_id": df["unique_id"].iloc[0],
        "modelo": df["modelo"].iloc[0],
        "y_real":venta_real_total,
        "y_pred":prediccion_total,
        "MSE": float(f"{mse:.2f}"),
        "RMSE": float(f"{rmse:.2f}"),
        "MAE": float(f"{mae:.2f}"),
        "MAPE": float(f"{mape:.2f}"),
        "error_absoluto_total": float(f"{error_absoluto_total:.2f}"),
        "WAPE": float(f"{wape:.2f}"),
        "WAPE_ranking": float(f"{wape_ranking:.2f}"),
        "caso_demanda_test": caso_demanda_test,
        "bias_total_abs_periodo_evaluacion":float(f"{abs(bias_total_periodo_evaluacion):.2f}"),
        "sesgo":sesgo
    })

    df_metricas_articulo_modelo= Serie_filtrada_con_metricas.to_frame().T
    return df_metricas_articulo_modelo


#=========================================================================================
# Funcion principal del calculo de metricas
# =====================================================================================
def evaluando_metricas_por_articulo_modelo(df):
    lista_resultados=[]
    articulos=df["unique_id"].dropna().unique().tolist()
    modelos=df["modelo"].dropna().unique().tolist()
  

    for articulo in articulos:
        for modelo in modelos:
            df_filtrado = crear_df_por_articulo_modelo(df, articulo, modelo)
            df_metricas_articulo_modelo=calcular_metricas(df_filtrado)
            lista_resultados.append(df_metricas_articulo_modelo)

    df_metricas = pd.concat(
    lista_resultados,
    axis=0,
    ignore_index=True
) 
    return df_metricas
           
