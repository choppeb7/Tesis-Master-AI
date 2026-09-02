import pandas as pd

# ============================================================
# Separar train/test temporal desde df_inferencia
# ============================================================

def separar_train_test_df_inferencia(
    df_inferencia,
    meses_evaluacion=6,
    meses_entrenamiento=None
):
    """
    Separa df_inferencia en train y test usando partición temporal global.

    df_inferencia debe tener:
    - unique_id
    - ds
    - y

    Lógica:
    - Ordena las fechas ds de más antigua a más reciente.
    - Los últimos meses_evaluacion meses son test.
    - Todo lo anterior es train.
    - Si meses_entrenamiento tiene valor, usa solo los últimos X meses antes del test.
    """

    columnas_requeridas = {"unique_id", "ds", "y"}
    faltantes = columnas_requeridas - set(df_inferencia.columns)

    if faltantes:
        raise ValueError(f"Faltan columnas requeridas: {faltantes}")

    df_temp = df_inferencia.copy()

    df_temp["ds"] = pd.to_datetime(df_temp["ds"])
    df_temp["y"] = pd.to_numeric(df_temp["y"], errors="coerce").fillna(0)

    df_temp = df_temp.sort_values(
        by=["ds", "unique_id"]
    ).reset_index(drop=True)

    fechas_disponibles = (
        df_temp["ds"]
        .drop_duplicates()
        .sort_values()
        .tolist()
    )

    if meses_evaluacion <= 0:
        raise ValueError("meses_evaluacion debe ser mayor que cero.")

    if meses_evaluacion >= len(fechas_disponibles):
        raise ValueError(
            "meses_evaluacion no puede ser mayor o igual al total de meses disponibles."
        )

    fechas_test = fechas_disponibles[-meses_evaluacion:]
    fechas_train_disponibles = fechas_disponibles[:-meses_evaluacion]

    if meses_entrenamiento is not None:
        fechas_train = fechas_train_disponibles[-meses_entrenamiento:]
    else:
        fechas_train = fechas_train_disponibles

    df_train = df_temp[df_temp["ds"].isin(fechas_train)].copy()
    df_test = df_temp[df_temp["ds"].isin(fechas_test)].copy()

    info_split = {
        "fecha_inicio_train": min(fechas_train),
        "fecha_fin_train": max(fechas_train),
        "fecha_inicio_test": min(fechas_test),
        "fecha_fin_test": max(fechas_test),
        "meses_train": len(fechas_train),
        "meses_test": len(fechas_test),
        "cantidad_articulos_train": df_train["unique_id"].nunique(),
        "cantidad_articulos_test": df_test["unique_id"].nunique()
    }

    return df_train, df_test, info_split