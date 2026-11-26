"""Ejecutor del Pipeline 05: evaluación y generación de pronósticos.

Colocar este archivo en <raíz del proyecto>/scripts/ y ejecutarlo desde
la raíz con: python scripts/run_05_forecast_inferencia.py

Si el módulo que contiene ejecutar_pipeline_forecast tiene otro nombre,
modificar únicamente la línea de importación de main_pipeline.
"""

from pathlib import Path
import sys
import traceback



# Permite importar `pipeline` aun ejecutando este archivo dentro de scripts/.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from forecast_app.pipeline.forecast_inferencia import forecast_config as cfg
from forecast_app.pipeline.forecast_inferencia.main_pipeline import ejecutar_pipeline_forecast
from pipeline.forecast_inferencia.forecast_charts import guardar_graficos_forecast

def main():
    """Ejecuta el pipeline con los valores definidos en forecast_config.py."""
    print("\n" + "=" * 70)
    print("PIPELINE 05 | FORECAST: EVALUACIÓN, SELECCIÓN E INFERENCIA")
    print("=" * 70)

    print(f"Entrada:                {cfg.INPUT_ARCHIVO_EXCEL}")
    print(f"Meses evaluación:       {cfg.MESES_EVALUACION}")
    print(f"Meses forecast futuro:  {cfg.MESES_FORECAST_FUTURO}")
    print(f"Ventana Dummy:          {cfg.VENTANA_DUMMY}")
    print(f"Redondeo evaluación:    {cfg.REDONDEO_EVALUACION}")
    print(f"Redondeo operativo:     {cfg.REDONDEO_OPERATIVO}")
    print(f"Exportación:            {cfg.RUTA_EXPORTACION}")

    if not Path(cfg.INPUT_ARCHIVO_EXCEL).is_file():
        raise FileNotFoundError(
            f"No existe el Excel de entrada: {cfg.INPUT_ARCHIVO_EXCEL}"
        )

    # El orquestador utiliza sus valores por defecto, leídos desde cfg.
    resultados = ejecutar_pipeline_forecast()
    guardar_graficos_forecast(resultados)

    print("\n" + "=" * 70)
    print("PIPELINE 05 | FINALIZADO")
    print("=" * 70)
    print(f"Artículos originales:   {len(resultados['df_original']):,}")
    print(f"Filas de inferencia:    {len(resultados['df_inferencia']):,}")
    print(f"Filas de entrenamiento: {len(resultados['df_train']):,}")
    print(f"Filas de evaluación:    {len(resultados['df_test']):,}")
    print(f"Modelos evaluados:      {resultados['columnas_modelos_evaluar']}")
    print(f"Artículos con modelo:   {len(resultados['df_best_model']):,}")
    print(f"Artículos en resultado: {len(resultados['df_resultado_final']):,}")
    print(f"Archivo exportado:      {resultados.get('ruta_archivo_exportado')}")

    print("\nDistribución de mejores modelos:")
    print(
        resultados["df_best_model"]["best_model"]
        .value_counts(dropna=False)
        .to_string()
    )

    return resultados


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("\nERROR AL EJECUTAR EL PIPELINE 05:\n", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
