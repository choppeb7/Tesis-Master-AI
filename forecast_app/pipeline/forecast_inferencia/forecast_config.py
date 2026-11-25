from pathlib import Path
# ============================================================
# 1. RUTAS Y ARCHIVOS
# ============================================================

# Este archivo está ubicado en:
# forecast_app/pipeline/forecast_eda/eda_config.py
#
# parents[0] -> forecast_eda
# parents[1] -> pipeline
# parents[2] -> forecast_app
# parents[3] -> raíz del proyecto Tesis-Master-AI

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FORECAST_APP_DIR = PROJECT_ROOT / "forecast_app"

DATA_DIR = FORECAST_APP_DIR / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"

PROJECT_DIR = Path(__file__).resolve().parent

INPUT_ARCHIVO_EXCEL = (
    OUTPUT_DIR
    / "pipeline04_clusters_consolidados.xlsx"
)

RUTA_EXPORTACION = (
    OUTPUT_DIR
    / "pipeline05_resultados_forecast_inferencia.xlsx"
)


NOMBRE_HOJA_EXPORTACION = "resultado_forecast"


# ============================================================
# 2. VENTANAS TEMPORALES
# ============================================================

FRECUENCIA = "ME"

MESES_EVALUACION = 6
MESES_ENTRENAMIENTO = None
MESES_FORECAST_FUTURO = 6

VENTANA_DUMMY = 24


# ============================================================
# 3. MODELOS A EVALUAR
# ============================================================

INCLUIR_MODELOS_STATS = True
INCLUIR_DUMMY = True


# ============================================================
# 4. REDONDEO DE PREDICCIONES
# ============================================================

REDONDEO_EVALUACION = None
REDONDEO_OPERATIVO = "ceil"
