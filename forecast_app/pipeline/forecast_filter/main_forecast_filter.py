from pathlib import Path 
import sys
import pandas as pd

## ========================================0
# AJUSTE DE RUTA PARA IMPORTAR forecast_app
## ========================================0

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FORECAST_APP_DIR = PROJECT_ROOT / "forecast_app"

if str(FORECAST_APP_DIR) not in sys.path:
    sys.path.insert(0, str(FORECAST_APP_DIR))

from pipeline.forecast_filter.forecast_filter_rules import clasificar_segmento_forecast
from utils.reporting import guardar_grafico_barras_conteo, asegurar_directorio, limpiar_nombre_archivo, guardar_grafico_pastel_conteo, guardar_tabla_resumen_segmento

def ejecutar_forecast_filter(
    ruta_input=None, 
    ruta_output=None,
    directorio_figuras=None,
    directorio_tablas=None,
    exportar_excel=True,
    exportar_graficas=True,
    exportar_tablas=True,
):
    """
    Ejecuta el pipeline 02 de filtro y segmentación de forecast.
    
    Flujo: 
    1. Lee le dataframe preparado del pipeline 01.
    2. Clasifica artículos en segmentos de forecast.
    3. Exporta Excel final. 
    4. Guarda gráficas y tablas de resumen de los segmentos.
    """

    print("=" * 80)
    print("Ejecutando pipeline 02: Filtro y Segmentación de Forecast")
    print("=" * 80)

    #============================================================
    #1. Rutas de entrada y salida
    #============================================================
    if ruta_input is None: 
        ruta_input= Path(FORECAST_APP_DIR) / "data" / "output" / "df_forecast_preparado.xlsx"

    if ruta_output is None: 
        ruta_output= Path(FORECAST_APP_DIR) / "data" / "output" / "df_forecast_segmentado.xlsx"

    if directorio_figuras is None:
        directorio_figuras= Path(FORECAST_APP_DIR) / "reports" / "figures" / "02_forecast_filter"

    if directorio_tablas is None: 
        directorio_tablas= Path(FORECAST_APP_DIR) / "reports" / "tables" / "02_forecast_filter"

    ruta_input = Path(ruta_input)
    ruta_output = Path(ruta_output)
    directorio_figuras = Path(directorio_figuras)
    directorio_tablas = Path(directorio_tablas)

    print(f"Ruta de entrada: {ruta_input}")
    print(f"Ruta de salida: {ruta_output}")
    print(f"Directorio de figuras: {directorio_figuras}")
    print(f"Directorio de tablas: {directorio_tablas}")

    #============================================================
    #2. Cargar dataframe de entrada
    #============================================================
    print("Cargando dataframe de entrada...")

    if not ruta_input.exists():
        raise FileNotFoundError(f"No se encontró el archivo de entrada: {ruta_input}")

    df_forecast_preparado = pd.read_excel(ruta_input)
    print("Dataframe cargado exitosamente ✅ Número de filas:", len(df_forecast_preparado), "Número de columnas:", len(df_forecast_preparado.columns))
    
    #============================================================
    #3. Aplicar reglas de filtro y segmentación de forecast
    #============================================================
    print("Aplicando reglas de filtro y segmentación de forecast...")

    df_segmentado= clasificar_segmento_forecast(df_forecast_preparado)
    print("Segmentación aplicada correctamente ✅")

    print("\nDistribución segmento_forecast:")
    print(df_segmentado["segmento_forecast"].value_counts(dropna=False))
    #============================================================
    #4. Exportar excel final
    #============================================================

    if exportar_excel:
        print("Exportando Excel final...")
        df_segmentado.to_excel(ruta_output, index=False)
        print(f"Excel exportado correctamente ✅ Ruta: {ruta_output}")

    #===========================================================
    #5. Exportar gráficas de resumen de los segmentos
    #===========================================================

    rutas_graficas=[]

    if exportar_graficas:
        print("Exportando gráficas de resumen de los segmentos...")

        # Gráfico de barras del conteo de artículos por segmento
        rutas_graficas.append(guardar_grafico_barras_conteo(
            df=df_segmentado,
            columna="segmento_forecast",
            directorio_salida=directorio_figuras,
            titulo="Conteo de artículos por segmento de forecast",
            nombre_archivo="01_grafico_barras_segmento_forecast.png"
        ))
        print(f"Gráfico de barras exportado correctamente ✅ Ruta: {rutas_graficas[-1]}")

        # Gráfico de pastel del conteo porcentual de artículos por segmento
        rutas_graficas.append(guardar_grafico_pastel_conteo(
            df=df_segmentado,
            columna="segmento_forecast",
            directorio_salida=directorio_figuras,
            titulo="Distribución porcentual de artículos por segmento de forecast",
            nombre_archivo="02_grafico_pastel_segmento_forecast.png"
        ))
        
        print(f"Gráfico de pastel exportado correctamente ✅ Ruta: {rutas_graficas[-1]}")

        rutas_graficas.append(guardar_grafico_barras_conteo(
            df=df_segmentado,
            columna="aplica_forecast_automatico",
            directorio_salida=directorio_figuras,
            titulo="Conteo de artículos por aplicación de forecast automático",
            nombre_archivo="03_grafico_barras_aplica_forecast_automatico.png"
        ))
        print(f"Gráfico de barras seg. aplica a Forecastautomático exportado correctamente ✅ Ruta: {rutas_graficas[-1]}")

        rutas_graficas.append(guardar_grafico_barras_conteo(
                    df=df_segmentado,
                    columna="aplica_forecast_automatico",
                    directorio_salida=directorio_figuras,
                    titulo="Conteo de artículos por aplicación de forecast automático",
                    nombre_archivo="04_grafico_barras_aplica_forecast_automatico.png"
                ))
        print(f"Gráfico de barras seg. aplica a Forecastautomático exportado correctamente ✅ Ruta: {rutas_graficas[-1]}")

        if tipo
        



