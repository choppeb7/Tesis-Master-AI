from pathlib import Path
import sys

# ============================================================
# IMPORTACIONES DEL PROYECTO
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FORECAST_APP_DIR = PROJECT_ROOT / "forecast_app"

if str(FORECAST_APP_DIR) not in sys.path:
    sys.path.insert(0, str(FORECAST_APP_DIR))

from pipeline.forecast_eda.main_forecast_eda import ejecutar_eda

from pipeline.forecast_eda.eda_charts import (
    generar_graficos_clasificaciones_eda
)


def main():

    # ========================================================
    # 1. EJECUTAR PIPELINE 03
    # ========================================================

    df_eda_final, ventas_24m, columnas_venta_24m = ejecutar_eda(
        exportar_excel=True,
        exportar_validacion=True
    )

    # ========================================================
    # 2. GENERAR GRÁFICOS EDA
    # ========================================================

    rutas_graficos = generar_graficos_clasificaciones_eda(
        df_eda=df_eda_final,
        generar_barras=True,
        generar_pasteles=True
    )

    print("\nGráficos generados:")
    for ruta in rutas_graficos:
        print(ruta)

    print("\nPipeline 03 y reporting finalizados.")


if __name__ == "__main__":
    main()