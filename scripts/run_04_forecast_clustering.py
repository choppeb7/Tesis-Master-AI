
"""
SCRIPT EJECUTOR - PIPELINE 04
============================
Ejecuta el pipeline de clustering para el TFM IA.

Entrada:
    Dataset generado por Pipeline 03.

Salida:
    Dataset clusterizado, métricas, perfiles,
    gráficos y modelo K-Means entrenado.
"""

import sys
from pathlib import Path

# Directorio raíz del proyecto
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Permitir importar los módulos del proyecto
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Importar función principal del pipeline
# Ajustar según la ubicación real de los módulos.
from forecast_app.pipeline.forecast_clustering.main_forecast_clustering import (
    ejecutar_pipeline_clustering,
)


def main():
    """Punto de entrada del Pipeline 04."""

    print("=" * 60)
    print("TFM IA - PIPELINE 04: FORECAST CLUSTERING")
    print("=" * 60)

    # Ejecutar todas las etapas del pipeline
    resultados = ejecutar_pipeline_clustering()

    # Mostrar resumen de resultados
    print("\nRESUMEN FINAL")
    print("-" * 60)

    print(f"K óptimo: {resultados['k_optimo']}")
    print(f"Criterio: {resultados['criterio']}")
    print(f"Dataset: {resultados['ruta_dataset']}")
    print(f"Modelo: {resultados['ruta_modelo']}")
    print(f"Metadata: {resultados['ruta_metadata']}")

    print("\nPipeline 04 finalizado correctamente.")

    return resultados


if __name__ == "__main__":
    main()
