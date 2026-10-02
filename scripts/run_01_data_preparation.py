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
# IMPORTAR PIPELINE
# ============================================================

from pipeline.data_preparation.main_data_preparation import ejecutar_preparacion_datos


def main():
    """
    Ejecuta el pipeline 01 de preparación de datos.

    Flujo:
    1. Extrae datos desde SAP.
    2. Aplica reglas comerciales.
    3. Aplica reglas de inventario.
    4. Exporta el dataframe final preparado.
    """

    df_final = ejecutar_preparacion_datos(
        fecha_fin=None,
        fecha_inicio_visual="2024-01-01",
        meses_historico=24,
        bodegas_consideradas=["11", "14"],
        listas_precio=[11, 12, 13, 14],
        incluir_solo_stock_positivo=True,
        factor_seguridad_meses=0.5,
        umbral_revision_compra_meses=2,
        exportar_excel=True
    )

    print("\nPipeline 01 finalizado correctamente ✅")
    print("Filas finales:", df_final.shape[0])
    print("Columnas finales:", df_final.shape[1])


if __name__ == "__main__":
    main()