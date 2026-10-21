from pathlib import Path

#====================
# Configuración General del Pipeline 03 -FORECAST EDA
#====================

NOMBRE_PIPELINE = "Pipeline 03 - Forecast EDA"

DESCRIPCION_PIPELINE = """
Este pipeline realiza un análisis exploratorio de los datos de forecast.
incluyendo variables de volumen, frecuencia, intermitencia, recencia, 
variabilidad, tendencia, concentración de picos y posible estacionalidad.
"""
# ============================================================
# RUTAS BASE DEL PROYECTO
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

REPORTS_DIR = FORECAST_APP_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures" / "03_forecast_eda"
TABLES_DIR = REPORTS_DIR / "tables" / "03_forecast_eda"

# ============================================================
# ARCHIVOS DE ENTRADA Y SALIDA
# ============================================================

NOMBRE_ARCHIVO_ENTRADA = "df_OITM_Ventas_after_forecast_filter.xlsx"

RUTA_INPUT_FORECAST_FILTER = OUTPUT_DIR / NOMBRE_ARCHIVO_ENTRADA

#OUTPUT ENRIQUECIDO CON VARIABLES Y CLASIFICACIONES PARA EDA
NOMBRE_ARCHIVO_OUTPUT = "df_OITM_Ventas_forecast_eda.xlsx"

RUTA_OUTPUT_FORECAST_EDA = OUTPUT_DIR / NOMBRE_ARCHIVO_OUTPUT

#Dataset final para alimentar el pipeline 04 de clusterización 

NOMBRE_ARCHIVO_OUTPUT_CLUSTER = "df_OITM_Ventas_forecast_eda_cluster.xlsx"
RUTA_OUTPUT_FORECAST_EDA_CLUSTER = OUTPUT_DIR / NOMBRE_ARCHIVO_OUTPUT_CLUSTER

#================================================================
#FILTRO PRINCIPAL DEL PIPELINE 03
#=====================================================================0

# En el flujo nuevo ya no conviene usar "aplica_forecast" genérico.
# El pipeline 02 de forecast_filter ya clasifica los artículos en segmentos de forecast.
# Por lo tanto, el filtro principal del pipeline 03 será:

COLUMNA_FILTRO_SEGMENTO_FORECAST = "aplica_forecast_automatico"

VALOR_FILTRO_SEGMENTO_FORECAST = True

#================================================
#CONFIGURACION DE HISTORICO DE VENTAS
#=================================================

MESES_HISTORICO_EDA = 24
MESES_RECIENTES_EDA = 6

PATRONES_COLUMNAS_VENTA_MENSUAL = [
    r"^venta_\d{4}_\d{2}$",
    r"^venta_[a-zA-ZáéíóúÁÉÍÓÚñÑ]+_\d{4}$"
]


# ============================================================
# COLUMNAS IDENTIFICADORAS
# ============================================================

COLUMNAS_IDENTIFICADORAS = [
    "codigo_articulo",
    "descripcion_completa",
    "grupo_articulo",
    "categoria",
    "subcategoria",
    "tipo",
    "marca_fabricante"
]

COLUMNAS_IDENTIFICADORAS_MINIMAS = [
    "codigo_articulo",
    "descripcion_completa"
]


# ============================================================
# VARIABLES BASE QUE YA DEBERÍAN VENIR DEL PIPELINE 01 Y 02
# ============================================================

VARIABLES_BASE_DEMANDA = [
    "total_unidades_vendidas_24m",
    "venta_promedio_mensual_24m",
    "conteo_facturas_24m",
    "cantidad_clientes_24m",
    "meses_con_venta_24m",
    "frecuencia_venta_24m_pct",
    #"venta_promedio_reciente_last_6m",
    #"ratio_venta_reciente_6m"
]

COLUMNAS_CONTEXTO_EDA = [
    "marca_fabricante",
    "grupo_articulo",
    "categoria",
    "subcategoria",
    # "tipo_abastecimiento",
    # "criticidad_comercial",
    # "segmento_forecast",
    # "clasificacion_alcance_inventario_24m",
    "stock_en_mano",
    "stock_disponible_proyectado",
    "precio_referencia",
    *VARIABLES_BASE_DEMANDA,
]

# ============================================================
# VARIABLES CALCULADAS EN EL EDA
# ============================================================
# Estas variables describen el comportamiento histórico de venta.
# El notebook las utiliza para capturar variabilidad, picos,
# intermitencia, recencia, tendencia y estacionalidad.

VARIABLES_CALCULADAS_EDA = [
    # ------------------------------------------------------------
    # Distribución mensual
    # ------------------------------------------------------------
    "desviacion_std_venta_24m",
    "coeficiente_variacion_venta_24m",
    "venta_maxima_mensual_24m",
    "venta_mediana_mensual_24m",
    "iqr_venta_24m",

    # ------------------------------------------------------------
    # Picos y concentración de demanda
    # ------------------------------------------------------------
    "cantidad_meses_pico_24m",
    "ratio_max_vs_promedio_24m",
    "indice_concentracion_picos_24m",

    # ------------------------------------------------------------
    # Intermitencia y frecuencia
    # ------------------------------------------------------------
    "porcentaje_meses_sin_venta_24m",
    "venta_promedio_meses_con_venta_24m",
    "adi_24m",
    "max_meses_consecutivos_sin_venta",

    # ------------------------------------------------------------
    # Recencia
    # ------------------------------------------------------------
    "meses_desde_ultima_venta",

    # ------------------------------------------------------------
    # Tendencia
    # ------------------------------------------------------------
    "pendiente_tendencia_24m",

    # ------------------------------------------------------------
    # Estacionalidad
    # ------------------------------------------------------------
    "correlacion_estacional_12m",

    # ------------------------------------------------------------
    # Variabilidad solo en meses con venta
    # ------------------------------------------------------------
    "cv_meses_con_venta_24m",

    # ------------------------------------------------------------
    # Venta reciente y ratio de venta reciente
    # ------------------------------------------------------------
    "venta_promedio_reciente_last_6m",
    "ratio_venta_reciente_6m"
]

# ============================================================
# PARES DE VARIABLES CANDIDATAS PARA ANÁLISIS DE DISPERSIÓN
# ============================================================

PARES_DISPERSION_EXPLORATORIO_EDA = [
    ("adi_24m", "cv_meses_con_venta_24m"),
    ("meses_con_venta_24m", "coeficiente_variacion_venta_24m"),
    ("venta_promedio_mensual_24m", "desviacion_std_venta_24m"),
    ("ratio_venta_reciente_6m", "pendiente_tendencia_24m"),
    ("meses_desde_ultima_venta", "max_meses_consecutivos_sin_venta"),
    ("cantidad_meses_pico_24m", "indice_concentracion_picos_24m"),
    ("total_unidades_vendidas_24m", "cantidad_clientes_24m"),
    ("correlacion_estacional_12m", "coeficiente_variacion_venta_24m"),
]

# ============================================================
# VARIABLES CANDIDATAS PARA ANÁLISIS Y CLUSTERIZACIÓN
# ============================================================

VARIABLES_CLUSTER_CANDIDATAS = [
    # Variables base
    "total_unidades_vendidas_24m",
    "venta_promedio_mensual_24m",
    "conteo_facturas_24m",
    "cantidad_clientes_24m",
    "meses_con_venta_24m",
    "frecuencia_venta_24m_pct",
    "venta_promedio_reciente_last_6m",
    "ratio_venta_reciente_6m",

    # Variables calculadas
    "desviacion_std_venta_24m",
    "coeficiente_variacion_venta_24m",
    "venta_maxima_mensual_24m",
    "venta_mediana_mensual_24m",
    "iqr_venta_24m",
    "cantidad_meses_pico_24m",
    "ratio_max_vs_promedio_24m",
    "indice_concentracion_picos_24m",
    "porcentaje_meses_sin_venta_24m",
    "venta_promedio_meses_con_venta_24m",
    "adi_24m",
    "max_meses_consecutivos_sin_venta",
    "meses_desde_ultima_venta",
    "pendiente_tendencia_24m",
    "correlacion_estacional_12m",
    "cv_meses_con_venta_24m"
]


# ============================================================
# VARIABLES FINALES SUGERIDAS PARA CLUSTERIZACIÓN
# ============================================================
# En el notebook, después de revisar correlaciones, se obtiene una lista
# final sugerida de 12 variables. Esta lista sirve como base para
# df_cluster_base y para el pipeline 04 de clusterización.

VARIABLES_CLUSTER_FINAL = [
    "total_unidades_vendidas_24m",
    "conteo_facturas_24m",
    "cantidad_clientes_24m",
    "meses_con_venta_24m",
    "ratio_venta_reciente_6m",
    "coeficiente_variacion_venta_24m",
    "cantidad_meses_pico_24m",
    "max_meses_consecutivos_sin_venta",
    "meses_desde_ultima_venta",
    "pendiente_tendencia_24m",
    "correlacion_estacional_12m",
    "cv_meses_con_venta_24m"
]


# ============================================================
# CONFIGURACIÓN DE CORRELACIÓN
# ============================================================

# Umbral inicial visto en el notebook para eliminar variables con
# alta redundancia.
UMBRAL_CORRELACION_INICIAL = 0.85

# Umbral más exigente para revisar variables finales del EDA.
UMBRAL_CORRELACION_EDA_FINAL = 0.70

METODO_CORRELACION = "pearson"

# ============================================================
# UMBRALES DE CLASIFICACIÓN - ESTACIONALIDAD
# ============================================================
# La correlación estacional compara el patrón mensual de un año contra
# el siguiente año. En el notebook se interpreta como señal preliminar
# de estacionalidad.

UMBRAL_ESTACIONALIDAD_FUERTE = 0.70
UMBRAL_ESTACIONALIDAD_MODERADA = 0.50
UMBRAL_ESTACIONALIDAD_DEBIL = 0.30

ETIQUETA_ESTACIONALIDAD_FUERTE = "Estacionalidad fuerte"
ETIQUETA_ESTACIONALIDAD_MODERADA = "Estacionalidad moderada"
ETIQUETA_ESTACIONALIDAD_DEBIL = "Estacionalidad débil"
ETIQUETA_ESTACIONALIDAD_SIN_CLARA = "Sin estacionalidad clara"


# ============================================================
# UMBRALES DE CLASIFICACIÓN - FRECUENCIA DE VENTA
# ============================================================

# Estos rangos permiten interpretar cuántos meses con venta tuvo
# el artículo en una ventana de 24 meses.

UMBRAL_ALTA_FRECUENCIA_MESES = 18
UMBRAL_FRECUENCIA_MEDIA_MESES = 12
UMBRAL_BAJA_FRECUENCIA_MESES = 6
UMBRAL_FRECUENCIA_ESPORADICA_MESES = 3

ETIQUETA_ALTA_FRECUENCIA = "Alta frecuencia"
ETIQUETA_FRECUENCIA_MEDIA = "Frecuencia media"
ETIQUETA_BAJA_FRECUENCIA = "Baja frecuencia"
ETIQUETA_FRECUENCIA_ESPORADICA = "Frecuencia esporádica"
ETIQUETA_MUY_BAJA_FRECUENCIA = "Muy baja frecuencia"


# ============================================================
# UMBRALES DE CLASIFICACIÓN - INTERMITENCIA
# ============================================================
# Se basa principalmente en el porcentaje de meses sin venta.

UMBRAL_BAJA_INTERMITENCIA_PCT = 25
UMBRAL_INTERMITENCIA_MODERADA_PCT = 50
UMBRAL_ALTA_INTERMITENCIA_PCT = 75

ETIQUETA_BAJA_INTERMITENCIA = "Baja intermitencia"
ETIQUETA_INTERMITENCIA_MODERADA = "Intermitencia moderada"
ETIQUETA_ALTA_INTERMITENCIA = "Alta intermitencia"
ETIQUETA_INTERMITENCIA_CRITICA = "Intermitencia crítica"


# ============================================================
# UMBRALES DE CLASIFICACIÓN - RECENCIA DE VENTA
# ============================================================
# Se basa en meses desde la última venta.

UMBRAL_VENTA_MUY_RECIENTE_MESES = 1
UMBRAL_VENTA_RECIENTE_MESES = 3
UMBRAL_VENTA_MODERADAMENTE_RECIENTE_MESES = 6
UMBRAL_VENTA_ANTIGUA_MESES = 12

ETIQUETA_VENTA_MUY_RECIENTE = "Venta muy reciente"
ETIQUETA_VENTA_RECIENTE = "Venta reciente"
ETIQUETA_VENTA_MODERADAMENTE_RECIENTE = "Venta moderadamente reciente"
ETIQUETA_VENTA_ANTIGUA = "Venta antigua"
ETIQUETA_VENTA_MUY_ANTIGUA = "Venta muy antigua"


# ============================================================
# UMBRALES DE CLASIFICACIÓN - VARIABILIDAD
# ============================================================
# Se basa en el coeficiente de variación de venta mensual. basado en coeficientes de variación, que es la desviación estándar dividida por el promedio.

UMBRAL_BAJA_VARIABILIDAD_CV = 0.50
UMBRAL_VARIABILIDAD_MODERADA_CV = 1.00
UMBRAL_ALTA_VARIABILIDAD_CV = 1.50

ETIQUETA_BAJA_VARIABILIDAD = "Baja variabilidad"
ETIQUETA_VARIABILIDAD_MODERADA = "Variabilidad moderada"
ETIQUETA_ALTA_VARIABILIDAD = "Alta variabilidad"
ETIQUETA_VARIABILIDAD_EXTREMA = "Variabilidad extrema"


# ============================================================
# UMBRALES DE CLASIFICACIÓN - TENDENCIA
# ============================================================
# En el notebook se utiliza una banda pequeña para considerar estabilidad.

UMBRAL_TENDENCIA = 0.10

ETIQUETA_TENDENCIA_CRECIENTE = "Tendencia creciente"
ETIQUETA_TENDENCIA_DECRECIENTE = "Tendencia decreciente"
ETIQUETA_TENDENCIA_ESTABLE = "Tendencia estable"


# ============================================================
# UMBRALES DE CLASIFICACIÓN - CONCENTRACIÓN DE PICOS
# ============================================================
# El índice se calcula como:
# promedio de los 3 meses más altos / promedio mensual general.

UMBRAL_BAJA_CONCENTRACION_PICOS = 1.50
UMBRAL_CONCENTRACION_MODERADA_PICOS = 3.00

ETIQUETA_BAJA_CONCENTRACION = "Baja concentración"
ETIQUETA_CONCENTRACION_MODERADA = "Concentración moderada"
ETIQUETA_ALTA_CONCENTRACION = "Alta concentración"


# ============================================================
# COLUMNAS DE CLASIFICACIÓN EDA
# ============================================================

COLUMNAS_CLASIFICACION_EDA = [
    "clasificacion_estacionalidad_24m",
    "clasificacion_frecuencia_venta_24m",
    "clasificacion_intermitencia_24m",
    "clasificacion_recencia_venta_24m",
    "clasificacion_variabilidad_24m",
    "clasificacion_tendencia_24m",
    "clasificacion_concentracion_picos_24m"
]

# ============================================================
# VARIABLES REQUERIDAS PARA CLASIFICACIÓN EDA
# ============================================================

VARIABLES_REQUERIDAS_CLASIFICACION_EDA = [
    "meses_con_venta_24m",
    "porcentaje_meses_sin_venta_24m",
    "meses_desde_ultima_venta",
    "coeficiente_variacion_venta_24m",
    "pendiente_tendencia_24m",
    "correlacion_estacional_12m",
    "indice_concentracion_picos_24m"
]
# ============================================================
# VARIABLES NUMÉRICAS PARA TABLAS DESCRIPTIVAS
# ============================================================

VARIABLES_DESCRIPTIVAS_EDA = [
    "total_unidades_vendidas_24m",
    "venta_promedio_mensual_24m",
    "conteo_facturas_24m",
    "cantidad_clientes_24m",
    "meses_con_venta_24m",
    "frecuencia_venta_24m_pct",
    "ratio_venta_reciente_6m",
    "coeficiente_variacion_venta_24m",
    "cantidad_meses_pico_24m",
    "indice_concentracion_picos_24m",
    "porcentaje_meses_sin_venta_24m",
    "adi_24m",
    "max_meses_consecutivos_sin_venta",
    "meses_desde_ultima_venta",
    "pendiente_tendencia_24m",
    "correlacion_estacional_12m",
    "cv_meses_con_venta_24m"
]


# ============================================================
# CONFIGURACIÓN DE GRÁFICAS
# ============================================================

DPI_FIGURAS = 500

FIGSIZE_BARRAS = (10, 6)
FIGSIZE_HISTOGRAMA = (10, 6)
FIGSIZE_BOXPLOT = (10, 6)
FIGSIZE_CORRELACION = (12, 10)
FIGSIZE_SCATTER = (10, 6)

ROTACION_XTICKS = 45

MOSTRAR_CANTIDAD_Y_PORCENTAJE = True


# ============================================================
# GRÁFICAS DE CLASIFICACIONES
# ============================================================

GRAFICAS_BARRAS_CLASIFICACIONES = [
    {
        "columna": "clasificacion_estacionalidad_24m",
        "titulo": "Distribución de artículos según estacionalidad",
        "nombre_archivo": "01_barras_clasificacion_estacionalidad.png"
    },
    {
        "columna": "clasificacion_frecuencia_venta_24m",
        "titulo": "Distribución de artículos según frecuencia de venta",
        "nombre_archivo": "02_barras_clasificacion_frecuencia.png"
    },
    {
        "columna": "clasificacion_intermitencia_24m",
        "titulo": "Distribución de artículos según intermitencia",
        "nombre_archivo": "03_barras_clasificacion_intermitencia.png"
    },
    {
        "columna": "clasificacion_recencia_venta_24m",
        "titulo": "Distribución de artículos según recencia de venta",
        "nombre_archivo": "04_barras_clasificacion_recencia.png"
    },
    {
        "columna": "clasificacion_variabilidad_24m",
        "titulo": "Distribución de artículos según variabilidad",
        "nombre_archivo": "05_barras_clasificacion_variabilidad.png"
    },
    {
        "columna": "clasificacion_tendencia_24m",
        "titulo": "Distribución de artículos según tendencia",
        "nombre_archivo": "06_barras_clasificacion_tendencia.png"
    },
    {
        "columna": "clasificacion_concentracion_picos_24m",
        "titulo": "Distribución de artículos según concentración de picos",
        "nombre_archivo": "07_barras_clasificacion_concentracion_picos.png"
    }
]


# ============================================================
# HISTOGRAMAS RECOMENDADOS
# ============================================================

VARIABLES_HISTOGRAMAS_EDA = [
    "total_unidades_vendidas_24m",
    "conteo_facturas_24m",
    "cantidad_clientes_24m",
    "meses_con_venta_24m",
    "frecuencia_venta_24m_pct",
    "coeficiente_variacion_venta_24m",
    "porcentaje_meses_sin_venta_24m",
    "adi_24m",
    "max_meses_consecutivos_sin_venta",
    "meses_desde_ultima_venta",
    "pendiente_tendencia_24m",
    "correlacion_estacional_12m",
    "cv_meses_con_venta_24m"
]


# ============================================================
# SCATTER PLOTS RECOMENDADOS
# ============================================================

SCATTER_PLOTS_EDA = [
    {
        "x": "meses_con_venta_24m",
        "y": "total_unidades_vendidas_24m",
        "hue": "clasificacion_frecuencia_venta_24m",
        "titulo": "Volumen vendido vs meses con venta",
        "nombre_archivo": "08_scatter_volumen_vs_meses_con_venta.png"
    },
    {
        "x": "frecuencia_venta_24m_pct",
        "y": "porcentaje_meses_sin_venta_24m",
        "hue": "clasificacion_intermitencia_24m",
        "titulo": "Frecuencia de venta vs meses sin venta",
        "nombre_archivo": "09_scatter_frecuencia_vs_intermitencia.png"
    },
    {
        "x": "meses_con_venta_24m",
        "y": "coeficiente_variacion_venta_24m",
        "hue": "clasificacion_variabilidad_24m",
        "titulo": "Meses con venta vs variabilidad",
        "nombre_archivo": "10_scatter_meses_con_venta_vs_variabilidad.png"
    },
    {
        "x": "indice_concentracion_picos_24m",
        "y": "correlacion_estacional_12m",
        "hue": "clasificacion_concentracion_picos_24m",
        "titulo": "Concentración de picos vs señal estacional",
        "nombre_archivo": "11_scatter_picos_vs_estacionalidad.png"
    }
]


# ============================================================
# MATRIZ DE CORRELACIÓN
# ============================================================

NOMBRE_ARCHIVO_MATRIZ_CORRELACION = "12_matriz_correlacion_variables_cluster.png"

TITULO_MATRIZ_CORRELACION = "Matriz de correlación de variables candidatas para clusterización"


# ============================================================
# TABLAS RESUMEN
# ============================================================

NOMBRE_TABLA_RESUMEN_CLASIFICACIONES = "01_resumen_clasificaciones_eda.xlsx"
NOMBRE_TABLA_FOTOGRAFIA_MATEMATICA = "02_fotografia_matematica_por_clasificacion.xlsx"
NOMBRE_TABLA_PARES_CORRELACIONADOS = "03_pares_variables_correlacionadas.xlsx"
NOMBRE_TABLA_VARIABLES_FINALES_CLUSTER = "04_variables_finales_cluster.xlsx"
NOMBRE_TABLA_DESCRIPTIVOS_VARIABLES_CLUSTER = "05_descriptivos_variables_cluster.xlsx"


# ============================================================
# OPCIONES DE EXPORTACIÓN
# ============================================================

EXPORTAR_EXCEL_EDA = True
EXPORTAR_CLUSTER_BASE = True
EXPORTAR_FIGURAS = True
EXPORTAR_TABLAS = True


# ============================================================
# COLUMNAS ESPERADAS PARA VALIDACIÓN
# ============================================================

COLUMNAS_REQUERIDAS_INPUT = [
    "codigo_articulo",
    "descripcion_completa",
    COLUMNA_FILTRO_SEGMENTO_FORECAST,
    "total_unidades_vendidas_24m",
    "conteo_facturas_24m",
    "cantidad_clientes_24m",
    "meses_con_venta_24m",
    "frecuencia_venta_24m_pct",
    #"ratio_venta_reciente_6m"
]


# ============================================================
# CONFIGURACIÓN PARA STREAMLIT
# ============================================================
# Estas listas permiten reutilizar las mismas funciones del script
# en una app Streamlit sin duplicar nombres de variables ni títulos.

STREAMLIT_SECCIONES_EDA = [
    {
        "nombre": "Resumen general",
        "tipo": "tabla",
        "descripcion": "Resumen de artículos y variables principales del EDA."
    },
    {
        "nombre": "Clasificaciones de demanda",
        "tipo": "graficas_barras",
        "columnas": COLUMNAS_CLASIFICACION_EDA
    },
    {
        "nombre": "Distribuciones numéricas",
        "tipo": "histogramas",
        "variables": VARIABLES_HISTOGRAMAS_EDA
    },
    {
        "nombre": "Relaciones entre variables",
        "tipo": "scatter",
        "graficas": SCATTER_PLOTS_EDA
    },
    {
        "nombre": "Correlación",
        "tipo": "matriz_correlacion",
        "variables": VARIABLES_CLUSTER_FINAL
    }
]