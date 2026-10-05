from pathlib import Path
import sys


# ============================================================
# CONFIGURAR RUTA DEL PROYECTO
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FORECAST_APP_DIR = PROJECT_ROOT / "forecast_app"

if str(FORECAST_APP_DIR) not in sys.path:
    sys.path.insert(0, str(FORECAST_APP_DIR))


# ============================================================
# IMPORTAR PIPELINE 02
# ============================================================

from pipeline.forecast_filter.main_forecast_filter import ejecutar_forecast_filter


def main():
    """
    Ejecuta el pipeline 02 - Forecast Filter.

    Este script:
    1. Lee el archivo generado por el pipeline 01:
       forecast_app/data/output/df_OITM_Ventas_preparado.xlsx

    2. Aplica las reglas de segmentación forecast:
       - forecast_automatico
       - forecast_revision_manual
       - pedido_especial
       - sin_forecast_infinito
       - sin_forecast_infinito_nuevo
       - sin_forecast_sin_demanda

    3. Exporta el resultado final:
       forecast_app/data/output/df_OITM_Ventas_forecast_filter.xlsx

    4. Guarda gráficas y tablas resumen.
    """

    df_segmentado = ejecutar_forecast_filter(
        exportar_excel=True,
        exportar_graficas=True,
        exportar_tablas=True
    )

    print("\n" + "=" * 100)
    print("PIPELINE 02 FINALIZADO CORRECTAMENTE")
    print("=" * 100)

    print("\nResumen final:")
    print("Filas:", df_segmentado.shape[0])
    print("Columnas:", df_segmentado.shape[1])

    if "segmento_forecast" in df_segmentado.columns:
        print("\nDistribución por segmento_forecast:")
        print(df_segmentado["segmento_forecast"].value_counts(dropna=False))

    if "aplica_forecast_automatico" in df_segmentado.columns:
        print("\nForecast automático:")
        print(df_segmentado["aplica_forecast_automatico"].value_counts(dropna=False))

    if "aplica_forecast_revision_manual" in df_segmentado.columns:
        print("\nForecast revisión manual:")
        print(df_segmentado["aplica_forecast_revision_manual"].value_counts(dropna=False))


if __name__ == "__main__":
    main()