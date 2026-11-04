from pathlib import Path

PROJECT_ROOT=Path(__file__).resolve().parents[3]
FORECAST_APP_DIR=PROJECT_ROOT/"forecast_app"

RUTA_INPUT_CLUSTER_READY=(
    FORECAST_APP_DIR / "data"/"output"
    / "df_OITM_Ventas_cluster_ready.xlsx"
)

RUTA_OUTPUT_CLUSTERIZADO=(
    FORECAST_APP_DIR/ "data"/"output"/"df_OITM_Ventas_forecast_clusterizado.xlsx"
)
HOJA_EDA_COMPLETO="matriz_con_ventas_con_feature_eng"
HOJA_INPUT_CLUSTER="cluster_input"
REPORTS_DIR=FORECAST_APP_DIR/"reports"
TABLES_DIR= REPORTS_DIR / "tables" /"04_Clustering"
FIGURES_DIR= REPORTS_DIR/"figures"/"04_Clustering"

MODELS_DIR = FORECAST_APP_DIR / "models" / "forecast_clustering"

APLICAR_WINSORIZACION=True
UMBRAL_SKEW_WINSOR = 2.0
UMBRAL_KURTOSIS_WINSOR = 5.0

FACTOR_IQR_WINSOR = 2.0

K_EVALUACION_MIN = 2
K_EVALUACION_MAX = 9

K_PRACTICO_MAX = 5
TOLERANCIA_SILUETA = 0.02

K_FORZADO = None

RANDOM_STATE = 42
N_INIT_KMEANS = 10

SEMILLAS_ESTABILIDAD = [11, 21, 31, 41, 51]

EXPORTAR_MATRICES_INTERMEDIAS = True

DPI_FIGURAS = 300

N_COMPONENTES_PCA_VISUALIZACION = 3

NOMBRE_MODELO_KMEANS = "pipeline04_kmeans.joblib"
NOMBRE_METADATA_MODELO = "pipeline04_metadata.json"

# ============================================================
# COLUMNAS DE CONTEXTO PARA OUTPUT DE FORECASTING
# ============================================================

COLUMNAS_CONTEXTO_FORECAST = [
    "codigo_articulo",
    "descripcion_completa",
    "marca_fabricante",
    "grupo_articulo",
    "categoria",
    "subcategoria",
    "stock_en_mano",
    "stock_disponible_proyectado",
    "fecha_ultima_compra",
]