import pandas as pd
import numpy as np

from pathlib import Path
import pandas as pd

# ============================================================
# Agregar forecast futuro a todos los artículos
# ============================================================

def agregar_forecast_todos_los_articulos(
    df,
    df_forecast,
    columna_codigo_df="unique_id",
    columna_id_forecast="unique_id",
    columna_fecha="ds",
    columna_prediccion="y_pred",
    columna_periodo="periodo",
    valor_periodo_forecast="Forecast futuro",
    prefijo_forecast="forecast",
    redondeo=None
):
    """
    Agrega las predicciones futuras de todos los artículos al dataframe original.

    Entrada:
    - df: dataframe consolidado, una fila por artículo.
    - df_forecast: dataframe de forecast en formato largo:
        unique_id | ds | y_pred

      También puede venir de df_forecast_visual, en cuyo caso se filtra:
        periodo == "Forecast futuro"

    Salida:
    - df_resultado: dataframe original + columnas forecast_YYYY_MM + compra_sugerida
    - df_forecast_wide: matriz de forecast futuro por artículo
    - columnas_forecast: lista de columnas forecast creadas
    """

    df_base = df.copy()
    df_pred = df_forecast[df_forecast["periodo"] == "Forecast futuro"].copy()

    # ------------------------------------------------------------
    # Asegurar que el código del artículo esté como columna
    # ------------------------------------------------------------

    if columna_codigo_df not in df_base.columns:
        if df_base.index.name == columna_codigo_df:
            df_base = df_base.reset_index()
        else:
            raise ValueError(
                f"No se encontró la columna {columna_codigo_df} en df."
            )

    # ------------------------------------------------------------
    # Si viene df_forecast_visual, filtrar solo Forecast futuro
    # ------------------------------------------------------------

    if columna_periodo in df_pred.columns:
        df_pred = df_pred[
            df_pred[columna_periodo] == valor_periodo_forecast
        ].copy()

    # ------------------------------------------------------------
    # Validar columnas requeridas
    # ------------------------------------------------------------

    columnas_requeridas = {
        columna_id_forecast,
        columna_fecha,
        columna_prediccion
    }

    faltantes = columnas_requeridas - set(df_pred.columns)

    if faltantes:
        raise ValueError(
            f"Faltan columnas requeridas en df_forecast: {faltantes}"
        )

    # ------------------------------------------------------------
    # Asegurar tipos
    # ------------------------------------------------------------

    df_pred[columna_fecha] = pd.to_datetime(df_pred[columna_fecha])

    df_pred[columna_prediccion] = pd.to_numeric(
        df_pred[columna_prediccion],
        errors="coerce"
    ).fillna(0)

    df_pred[columna_prediccion] = df_pred[columna_prediccion].clip(lower=0)

    # ------------------------------------------------------------
    # Redondeo operativo
    # ------------------------------------------------------------

    if redondeo == "ceil":
        df_pred[columna_prediccion] = (
            np.ceil(df_pred[columna_prediccion])
            .astype(int)
        )

    elif redondeo == "round":
        df_pred[columna_prediccion] = (
            df_pred[columna_prediccion]
            .round(0)
            .astype(int)
        )

    # ------------------------------------------------------------
    # Crear nombres de columnas forecast_YYYY_MM
    # ------------------------------------------------------------

    df_pred["columna_forecast"] = df_pred[columna_fecha].apply(
        lambda fecha: f"{prefijo_forecast}_{fecha.year}_{fecha.month:02d}"
    )

    # ------------------------------------------------------------
    # Convertir forecast largo a matriz ancha
    # ------------------------------------------------------------

    df_forecast_wide = (
        df_pred
        .pivot_table(
            index=columna_id_forecast,
            columns="columna_forecast",
            values=columna_prediccion,
            aggfunc="sum",
            fill_value=0
        )
        .reset_index()
    )

    # ------------------------------------------------------------
    # Ordenar columnas forecast cronológicamente
    # ------------------------------------------------------------

    columnas_forecast = [
        col for col in df_forecast_wide.columns
        if col.startswith(prefijo_forecast + "_")
    ]

    columnas_forecast = sorted(
        columnas_forecast,
        key=lambda col: pd.to_datetime(
            col.replace(prefijo_forecast + "_", ""),
            format="%Y_%m"
        )
    )

    df_forecast_wide = df_forecast_wide[
        [columna_id_forecast] + columnas_forecast
    ]

    # ------------------------------------------------------------
    # Compra sugerida = suma total del forecast futuro
    # ------------------------------------------------------------

    df_forecast_wide["compra_sugerida"] = (
        df_forecast_wide[columnas_forecast]
        .sum(axis=1)
    )

    # ------------------------------------------------------------
    # Merge contra todos los artículos del dataframe original
    # ------------------------------------------------------------

    df_resultado = df_base.merge(
        df_forecast_wide,
        left_on=columna_codigo_df,
        right_on=columna_id_forecast,
        how="left",
        validate="one_to_one"
    )

    # Eliminar columna duplicada si se llama diferente
    if columna_codigo_df != columna_id_forecast:
        df_resultado = df_resultado.drop(
            columns=[columna_id_forecast]
        )

    # ------------------------------------------------------------
    # Rellenar artículos sin forecast con cero
    # ------------------------------------------------------------

    columnas_nuevas = columnas_forecast + ["compra_sugerida"]

    df_resultado[columnas_nuevas] = (
        df_resultado[columnas_nuevas]
        .fillna(0)
    )

    if redondeo in ["ceil", "round"]:
        df_resultado[columnas_nuevas] = (
            df_resultado[columnas_nuevas]
            .astype(int)
        )

    return df_resultado, df_forecast_wide, columnas_forecast




def exportar_dataframe_excel(
    df_exportar,
    ruta_exportacion,
    nombre_hoja="resultado_forecast",
    index=False
):
    ruta_exportacion = Path(ruta_exportacion)

    ruta_exportacion.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with pd.ExcelWriter(ruta_exportacion, engine="openpyxl") as writer:
        df_exportar.to_excel(
            writer,
            sheet_name=nombre_hoja[:31],
            index=index
        )

    return ruta_exportacion