import pandas as pd



def mejor_modelo_por_articulo(df_metricas):
    df_mejor_modelo = (
        df_metricas
        .sort_values(
            by=[
                "unique_id",
                "WAPE_ranking",
                "bias_total_abs_periodo_evaluacion",
                "RMSE",
                "MAE"
            ],
            ascending=[True, True, True, True, True]
        )
        .groupby("unique_id", as_index=False)
        .first()
    )

    df_mejor_modelo = df_mejor_modelo.rename(
        columns={"modelo": "best_model"}.copy()
    )

    return df_mejor_modelo