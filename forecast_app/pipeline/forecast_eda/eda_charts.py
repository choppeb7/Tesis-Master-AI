from pathlib import Path
import sys
from pipeline.forecast_eda import eda_config as cfg

from utils.reporting import (
    guardar_grafico_barras_conteo,
    guardar_grafico_pastel_conteo
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FORECAST_APP_DIR = PROJECT_ROOT / "forecast_app"

if str(FORECAST_APP_DIR) not in sys.path:
    sys.path.insert(0, str(FORECAST_APP_DIR))
    
    # if ruta_input is None: 
    #     ruta_input= Path(FORECAST_APP_DIR) / "data" / "output" / "df_OITM_Ventas_preparado.xlsx"

    # if ruta_output is None: 
    #     ruta_output= Path(FORECAST_APP_DIR) / "data" / "output" / "df_OITM_Ventas_after_forecast_filter.xlsx"

    # if directorio_figuras is None:
    #     directorio_figuras= Path(FORECAST_APP_DIR) / "reports" / "figures" / "02_forecast_filter"

    # if directorio_tablas is None: 
    #     directorio_tablas= Path(FORECAST_APP_DIR) / "reports" / "tables" / "02_forecast_filter"

    # ruta_input = Path(ruta_input)
    # ruta_output = Path(ruta_output)
    # directorio_figuras = Path(directorio_figuras)
    # directorio_tablas = Path(directorio_tablas)

    # print(f"Ruta de entrada: {ruta_input}")
    # print(f"Ruta de salida: {ruta_output}")
    # print(f"Directorio de figuras: {directorio_figuras}")
    # print(f"Directorio de tablas: {directorio_tablas}")

def generar_graficos_clasificaciones_eda(
    df_eda,
    directorio_salida=None,
    directorio_figuras=None,
    directorio_tablas=None,
    generar_barras=True,
    generar_pasteles=True
):
    """
    Genera gráficos para las clasificaciones del Pipeline 03.

    No modifica el DataFrame original.
    Devuelve las rutas de los archivos generados.
    """
    if directorio_salida is None: 
        directorio_salida= Path(FORECAST_APP_DIR) / "data" / "output" / "df_OITM_EDA_after_Clasificacion_rules.xlsx"

    if directorio_figuras is None:
        directorio_figuras= Path(FORECAST_APP_DIR) / "reports" / "figures" / "03_forecast_eda"

    if directorio_tablas is None: 
        directorio_tablas= Path(FORECAST_APP_DIR) / "reports" / "tables" / "03_forecast_eda"

    #ruta_input = Path(ruta_input)
    directorio_salida = Path(directorio_salida)
    directorio_figuras = Path(directorio_figuras)
    directorio_tablas = Path(directorio_tablas)

    columnas_faltantes = [
        columna
        for columna in cfg.COLUMNAS_CLASIFICACION_EDA
        if columna not in df_eda.columns
    ]

    if columnas_faltantes:
        raise ValueError(
            f"Faltan clasificaciones para generar gráficos: "
            f"{columnas_faltantes}"
        )

    rutas_generadas = []

    for columna in cfg.COLUMNAS_CLASIFICACION_EDA:

        titulo = columna.replace(
            "clasificacion_", ""
        ).replace(
            "_24m", ""
        ).replace(
            "_", " "
        ).title()

        if generar_barras:
            
            ruta = guardar_grafico_barras_conteo(
                df=df_eda,
                columna=columna,
                directorio_salida=directorio_figuras,
                titulo=f"Distribución de {titulo}",
                rotacion_xticks=45
            )

            rutas_generadas.append(ruta)

        if generar_pasteles:

            ruta = guardar_grafico_pastel_conteo(
                df=df_eda,
                columna=columna,
                directorio_salida=directorio_figuras,
                titulo=f"Participación de {titulo}",
                mostrar_leyenda=True
            )

            rutas_generadas.append(ruta)

    return rutas_generadas