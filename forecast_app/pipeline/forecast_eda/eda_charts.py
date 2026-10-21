from pathlib import Path
import sys
from pipeline.forecast_eda import eda_config as cfg

from utils.reporting import (
    guardar_grafico_histograma,
    guardar_grafico_boxplot,
    guardar_grafico_dispersion_variables,
    guardar_grafico_barras_conteo,
    guardar_grafico_pastel_conteo,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
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
    incluir_variables_base=True,
    generar_barras=True,
    generar_pasteles=True,
    generar_histogramas=True,
    generar_boxplots=True,
    generar_dispersion=True,
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

    #======================================================================================
    #Generar histogramas y boxplots para variables calculadas y base de demanda
    #======================================================================================

    if df_eda.empty:
        raise ValueError("El DataFrame de EDA está vacío. No se pueden generar gráficos.")  

    if incluir_variables_base:
        candidatas_eda = list(dict.fromkeys(cfg.VARIABLES_BASE_DEMANDA + cfg.VARIABLES_CALCULADAS_EDA))
            
            
        #list(dict.fromkeys( #+ cfg.VARIABLES_BASE_DEMANDA#))
        

    resultados = {
        "histogramas": [], "boxplots": [], "dispersion": [],
        "Distribución de barras": [], "Distribución de pasteles": []
    }

    for variable in candidatas_eda:
        if generar_histogramas:
            ruta_hist = guardar_grafico_histograma(
                df=df_eda,
                columna=variable,
                directorio_salida=directorio_figuras,
                titulo=f"Histograma de {variable}",
                bins=30
            )
            resultados["histogramas"].append(ruta_hist)

        if generar_boxplots:
            ruta_box = guardar_grafico_boxplot(
                df=df_eda,
                columna=variable,
                directorio_salida=directorio_figuras,
                titulo=f"Boxplot de {variable}"
            )
            resultados["boxplots"].append(ruta_box)

 
    pares=cfg.PARES_DISPERSION_EXPLORATORIO_EDA
    if generar_dispersion:
        for x, y in pares:
            ruta_disp = guardar_grafico_dispersion_variables(
                df=df_eda,
                columna_x=x,
                columna_y=y,
                directorio_salida=directorio_figuras,
                titulo=f"Dispersión de {x} vs. {y}"
            )
            resultados["dispersion"].append(ruta_disp)

    for variable in df_eda.columns:
        if variable not in df_eda.columns:
            print(f"Advertencia: La columna '{variable}' no está presente en el DataFrame de EDA.")

    #======================================================================
    #Generar diagramas de barras y pasteles para clasificaciones
    #=======================================================================

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

            resultados["Distribución de barras"].append(ruta)

        if generar_pasteles:

            ruta = guardar_grafico_pastel_conteo(
                df=df_eda,
                columna=columna,
                directorio_salida=directorio_figuras,
                titulo=f"Participación de {titulo}",
                mostrar_leyenda=True
            )

            resultados["Distribución de pasteles"].append(ruta)

    return resultados