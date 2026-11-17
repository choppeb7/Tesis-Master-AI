"""
PIPELINE 04 - ORQUESTADOR DE CLUSTERIZACION PARA FORECAST
======================================================
Coordina los modulos existentes sin repetir calculos matematicos.

Entrada:
    Excel producido por Pipeline 03 (cluster_input + eda_completo).
Salida:
    Dataset enriquecido, tablas, figuras, modelo, preprocesador y metadatos.

Ejecutar desde el proyecto mediante la futura entrada
scripts/run_04_forecast_clustering.py
"""

from datetime import datetime, timezone
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from . import clustering_config as cfg
from .clustering_data_preparation import cargar_dataset_cluster
from .clustering_preprocessing import PreprocesadorDemanda
from .clustering_model_selection import (
    evaluar_modelos_kmeans,
    seleccionar_k_optimo,
    evaluar_estabilidad,
    entrenar_modelo_final,
)

from .clustering_charts import (
    crear_datafram_clusterizado,
    generar_perfiles_cluster,
)

from . clustering_charts import (
    graficar_codo,
    graficar_silhouette,
    graficar_davies_bouldin,
    graficar_calinski_harabasz,
    graficar_estabilidad_ari,
    graficar_distribucion_clusters,
    graficar_heatmap_perfiles,
    graficar_boxplots_variables,
    graficar_pca_clusters,
    guardar_figura,
)

# ============================================================
# 1. FUNCIONES AUXILIARES DE EXPORTACION
# ============================================================

def _preparar_directorios():
    """Crear las carpetas de salida configuradas en clustering_config.py."""
    for carpeta in (cfg.TABLES_DIR, cfg.FIGURES_DIR, cfg.MODELS_DIR,
                    cfg.RUTA_OUTPUT_CLUSTERIZADO.parent):
        Path(carpeta).mkdir(parents=True, exist_ok=True)

def _guardar_tabla(df, nombre):
    """Guardar cada tabla para consulta y documentacion del TFM."""
    ruta = cfg.TABLES_DIR / nombre
    df.to_excel(ruta, index=False)
    return ruta

def _validar_alineacion(df_input, X, X_scaled, variables):
    """Verificar que las filas y columnas sigan en el orden de entrenamiento."""
    if not (len(df_input) == len(X) == len(X_scaled)):
        raise ValueError("Los articulos no coinciden entre df_input, X y X_scaled.")
    if list(X.columns) != list(variables) or list(X_scaled.columns) != list(variables):
        raise ValueError("Las variables o su orden cambiaron durante el preprocesamiento.")
    if not df_input.index.equals(X.index) or not X.index.equals(X_scaled.index):
        raise ValueError("Los indices de df_input, X y X_scaled ya no coinciden.")
    # Una comprobacion adicional de los valores originales evita errores de orden.
    if not np.allclose(
        df_input[variables].to_numpy(dtype=float),
        X.to_numpy(dtype=float), rtol=0, atol=0
    ):
        raise ValueError("X y df_input no conservan los mismos valores por posicion.")

def _consolidar_eda(df_eda, df_clusterizado):
    """Agregar la columna de cluster al dataset de EDA para exportacion."""
    id_col=cfg.COLUMNA_ID_ARTICULO
    cluster_col=cfg.COLUMNA_CLUSTER

    if cluster_col in df_eda.columns:
        raise ValueError(f"La columna {cluster_col} ya existe en el dataset de EDA.")

    etiquetas_por_articulo = df_clusterizado[[id_col, cluster_col]].copy()
    consolidado = df_eda.merge(
        etiquetas_por_articulo, on=id_col, how="left", validate="1:1", sort=False
    )
    if consolidado[cluster_col].isna().any() or len(consolidado) != len(df_eda):
        raise ValueError("No se pudieron asignar todas las etiquetas a eda_completo.")
    return consolidado

def _guardar_graficas(df_metricas, k_optimo, k_codo, df_detalle_ari,
                      df_cluster_tamanos, df_cluster_comparativo,
                      df_clusterizado, X_scaled, etiquetas, variables):
    """Crear nueve figuras a partir de los resultados ya calculados."""
    tareas = [
        ("01_elbow_kmeans.png", lambda: graficar_codo(df_metricas, k_optimo, k_codo)),
        ("02_silhouette_kmeans.png", lambda: graficar_silhouette(df_metricas, k_optimo)),
        ("03_davies_bouldin.png", lambda: graficar_davies_bouldin(df_metricas, k_optimo)),
        ("04_calinski_harabasz.png", lambda: graficar_calinski_harabasz(df_metricas, k_optimo)),
        ("05_estabilidad_ari.png", lambda: graficar_estabilidad_ari(df_detalle_ari)),
        ("06_distribucion_clusters.png", lambda: graficar_distribucion_clusters(df_cluster_tamanos)),
        ("07_heatmap_perfiles.png", lambda: graficar_heatmap_perfiles(df_cluster_comparativo)),
        ("08_boxplots_variables.png", lambda: graficar_boxplots_variables(df_clusterizado, variables)),
        ("09_pca_clusters.png", lambda: graficar_pca_clusters(X_scaled, etiquetas)),
    ]

    rutas = []
    for nombre, crear in tareas:
        figura = crear()
        rutas.append(guardar_figura(figura, nombre))
    return rutas

# ============================================================
# 2. FUNCION PRINCIPAL DEL PIPELINE 04
# ============================================================

def ejecutar_pipeline_clustering():
    """Ejecutar las etapas y devolver un resumen de los resultados."""
    print("\n========== PIPELINE 04: CLUSTERIZACION ==========")
    # ETAPA 1 - DATOS ORIGINALES
    print("\n[1/7] Cargando dataset de Pipeline 03...")
    df_input, df_eda, X, variables = cargar_dataset_cluster()

    # ETAPA 2 - PREPROCESAMIENTO MATEMATICO
    print("[2/7] Aplicando winsorizacion, transformaciones y RobustScaler...")
    preprocesador = PreprocesadorDemanda()

    X_scaled = preprocesador.fit_transform(X)
    _validar_alineacion(df_input, X, X_scaled, variables)

    # ETAPA 3 - COMPARAR K Y ELEGIR LA SOLUCION
    print("[3/7] Evaluando modelos KMeans para distintos K...")
    df_metricas=evaluar_modelos_kmeans(X_scaled, cfg.K_EVALUACION_MIN, cfg.K_EVALUACION_MAX)
    k_optimo, k_codo, criterio, df_seleccion = seleccionar_k_optimo(df_metricas, cfg.K_PRACTICO_MAX, cfg.TOLERANCIA_SILUETA)
    print (f"    K seleccionado: {k_optimo} | Codo: {k_codo} | Criterio: {criterio}")

    # ETAPA 4 - ESTABILIDAD Y MODELO DEFINITIVO
    print("[4/7] Evaluando estabilidad ARI y entrenando el modelo final...")
    df_ari_resumen, df_ari_detalle = evaluar_estabilidad(X_scaled, k_optimo, cfg.SEMILLAS_ESTABILIDAD)
    modelo, etiquetas = entrenar_modelo_final(X_scaled, k_optimo, cfg.N_INIT_KMEANS)

    if len(etiquetas) != len(df_input):
        raise ValueError("El modelo final no produjo etiquetas para todos los articulos.")

    # ETAPA 5 - PERFIL MATEMATICO EN UNIDADES ORIGINALES
    print("[5/7] Calculando perfiles de cluster en unidades originales...")
    df_clusterizado = crear_datafram_clusterizado(df_input, etiquetas)

    (
        df_cluster_tamanos,
        df_cluster_estadisticas,
        df_cluster_comparativo, 
        df_cluster_perfiles,
        df_articulos_clusterizados
    )= generar_perfiles_cluster(df_clusterizado)

    # Consolidar EDA solamente al final; unir por identificador, no por posicion.
    df_final = _consolidar_eda(df_eda, df_articulos_clusterizados)

    # ETAPA 6 - EXPORTAR TABLAS Y DATASETS
    print("[6/7] Exportando tablas, dataset, modelo y metadatos...")
    _preparar_directorios()   

    tablas={
        "01_diagnosticos_preprocesamiento.xlsx": preprocesador.diagnosticos_,
        "02_comparativo_diagnosticos.xlsx": preprocesador.comparativo_,
        "03_reglas_preprocesamiento.xlsx": preprocesador.registro_,
        "04_parametros_robust_scaler.xlsx": preprocesador.parametros_scaler_,
        "05_metricas_kmeans.xlsx": df_metricas,
        "06_seleccion_k.xlsx": df_seleccion,
        "07_ari_resumen.xlsx": df_ari_resumen,
        "08_ari_detalle.xlsx": df_ari_detalle,
        "09_cluster_tamanos.xlsx": df_cluster_tamanos,
        "10_cluster_estadisticas.xlsx": df_cluster_estadisticas,
        "11_cluster_comparativo.xlsx": df_cluster_comparativo,
        "12_cluster_perfiles.xlsx": df_cluster_perfiles,
        "13_articulos_clusterizados.xlsx": df_articulos_clusterizados
    }
    rutas_tablas = [_guardar_tabla(df, nombre) for nombre, df in tablas.items()]

    if cfg.EXPORTAR_MATRICES_INTERMEDIAS:
        for etapa, matriz in preprocesador.matrices_entrenamiento_.items():
            # Incluir codigo_articulo por posicion, conservando el orden de X.
            tabla = matriz.copy()
            tabla.insert(0, cfg.COLUMNA_ID, df_input[cfg.COLUMNA_ID].to_numpy())
            rutas_tablas.append(_guardar_tabla(tabla, f"matriz_{etapa}.xlsx"))    
