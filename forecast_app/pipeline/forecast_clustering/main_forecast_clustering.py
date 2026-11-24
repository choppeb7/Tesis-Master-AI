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
import re

from . import clustering_config as cfg
from .clustering_data_preparation import cargar_dataset_cluster
from .clustering_preprocessing import PreprocesadorDemanda
from .clustering_model_selection import (
    evaluar_modelos_kmeans,
    seleccionar_k_optimo,
    evaluar_estabilidad,
    entrenar_modelo_final,
)


from .clustering_unit_segmentation import segmentar_por_unidad

from . clustering_profiling import (
    crear_dataframe_clusterizado,
    generar_perfiles_clusters,
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


def _nombre_seguro(nombre_grupo):
    """Evita rutas inválidas o separadores de directorio en el nombre del grupo."""
    nombre = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(nombre_grupo)).strip("_")
    if not nombre:
        raise ValueError("nombre_grupo debe contener caracteres válidos")
    return nombre.lower()


def _rutas_grupo(nombre_grupo):
    """Carpetas independientes sin modificar las constantes globales de cfg."""
    grupo = _nombre_seguro(nombre_grupo)
    rutas = {
        "tablas": Path(cfg.TABLES_DIR) / grupo,
        "figuras": Path(cfg.FIGURES_DIR) / grupo,
        "modelos": Path(cfg.MODELS_DIR) / grupo,
        "dataset": Path(cfg.RUTA_OUTPUT_CLUSTERIZADO).parent / grupo,
    }
    for ruta in rutas.values():
        ruta.mkdir(parents=True, exist_ok=True)
    return rutas


def _guardar_tabla_grupo(df, nombre, nombre_grupo, rutas):
    ruta = rutas["tablas"] / f"{_nombre_seguro(nombre_grupo)}_{nombre}"
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
    id_col=cfg.COLUMNA_ID
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

def _guardar_graficas(nombre_grupo, rutas, df_metricas, k_optimo, k_codo, df_detalle_ari,
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

    rutas_figuras = []
    for nombre_archivo, crear in tareas:
        nombre_final = f"{_nombre_seguro(nombre_grupo)}_{nombre_archivo}"
        print(f"[{nombre_grupo}] Generando figura: {nombre_final}")
        figura = crear()
        if figura is None:
            raise ValueError(f"La función gráfica no devolvió una Figure: {nombre_final}")
        # Sin duplicar el título particular de cada gráfica.
        figura.suptitle(f"Grupo de inventario: {nombre_grupo}", fontsize=12, fontweight="bold")
        ruta = guardar_figura(figura, nombre_final, carpeta=rutas["figuras"])
        rutas_figuras.append(ruta)

    return rutas_figuras


def ejecutar_clustering_grupo(nombre_grupo, df_input, df_eda, X, variables):
    prefijo = f"[{nombre_grupo}]"
    print(f"\n========== PIPELINE 04 | {nombre_grupo.upper()} ==========")
    rutas = _rutas_grupo(nombre_grupo)
    # ETAPA 2 - PREPROCESAMIENTO MATEMATICO
    print(f"{prefijo} [2/7] Winsorización, transformaciones y RobustScaler...")
    # Experimento de sensibilidad
    variables_excluir = [
    "pendiente_tendencia_24m",
    "total_unidades_vendidas_24m",
    ]

    X_experimento = X.drop(columns=variables_excluir)
    # Actualizar lista de variables del experimento
    variables_experimento = X_experimento.columns.tolist()
    preprocesador = PreprocesadorDemanda()

    X_scaled = preprocesador.fit_transform(X_experimento)
    
    # Validar utilizando las variables del experimento
    _validar_alineacion(
        df_input,
        X_experimento,
        X_scaled,
        variables_experimento,
    )
    
    # ETAPA 3 - COMPARAR K Y ELEGIR LA SOLUCION
    print(f"{prefijo} [3/7] Evaluando modelos KMeans para distintos K...")
    df_metricas=evaluar_modelos_kmeans(X_scaled, cfg.K_EVALUACION_MIN, cfg.K_EVALUACION_MAX)
    print(f"{prefijo} resultados de metricas de KMeans: {df_metricas.head(5).to_string()}")
    k_optimo, k_codo, criterio, df_seleccion = seleccionar_k_optimo(df_metricas)
    print(f"{prefijo} K seleccionado: {k_optimo} | Codo: {k_codo} | Criterio: {criterio}")
    
    # ETAPA 4 - ESTABILIDAD Y MODELO DEFINITIVO
    print(f"{prefijo} [4/7] Evaluando estabilidad ARI y entrenando el modelo final...")
    df_ari_resumen, df_ari_detalle = evaluar_estabilidad(X_scaled, k_optimo, cfg.SEMILLAS_ESTABILIDAD)
    modelo, etiquetas = entrenar_modelo_final(X_scaled, k_optimo)
    
    if len(etiquetas) != len(df_input):
        raise ValueError("El modelo final no produjo etiquetas para todos los articulos.")
    
    # ETAPA 5 - PERFIL MATEMATICO EN UNIDADES ORIGINALES
    print(f"{prefijo} [5/7] Calculando perfiles de cluster en unidades originales...")
    df_clusterizado = crear_dataframe_clusterizado(df_input, etiquetas)
    (
    df_cluster_tamanos,
    df_cluster_estadisticas,
    df_cluster_comparativo, 
    df_cluster_perfiles,
    df_articulos_clusterizados
                )= generar_perfiles_clusters(df_clusterizado)
    
    # Consolidar EDA solamente al final; unir por identificador, no por posicion.
    df_final = _consolidar_eda(df_eda, df_articulos_clusterizados)
    
    # ETAPA 6 - EXPORTAR TABLAS Y DATASETS
    print(f"{prefijo} [6/7] Exportando tablas, dataset, modelo y metadatos...")
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
    rutas_tablas = [_guardar_tabla_grupo(df, nombre, nombre_grupo, rutas) for nombre, df in tablas.items()]
    
    if cfg.EXPORTAR_MATRICES_INTERMEDIAS:
        for etapa, matriz in preprocesador.matrices_entrenamiento_.items():
            # Incluir codigo_articulo por posicion, conservando el orden de X.
            tabla = matriz.copy()
            tabla.insert(0, cfg.COLUMNA_ID, df_input[cfg.COLUMNA_ID].to_numpy())
            rutas_tablas.append(_guardar_tabla_grupo(tabla, f"matriz_{etapa}.xlsx", nombre_grupo, rutas))

    
    nombre_base = Path(cfg.RUTA_OUTPUT_CLUSTERIZADO)
    ruta_dataset = rutas["dataset"] / f"{_nombre_seguro(nombre_grupo)}_{nombre_base.name}"
    # El archvio final de salida es el dataset de EDA con la columna de cluster.
    with pd.ExcelWriter(ruta_dataset, engine='openpyxl') as libro:
        df_final.to_excel(libro, sheet_name=cfg.HOJA_EDA_COMPLETO, index=False)
        df_clusterizado.to_excel(libro, sheet_name="cluster_input_etiquetado", index=False)
        df_cluster_perfiles.to_excel(libro, sheet_name="cluster_perfiles", index=False)
    
    #persistir modelo y preprocesador para usarlo.
    ruta_modelo = rutas["modelos"] / f"{_nombre_seguro(nombre_grupo)}_{cfg.NOMBRE_MODELO_KMEANS}"
    joblib.dump({
                    "preprocesador": preprocesador,
                    "kmeans":modelo,
                    "variables": list(variables),
                    "columna_id": cfg.COLUMNA_ID,
                    "fecha": datetime.now(timezone.utc).isoformat(),
                    "columna_cluster": cfg.COLUMNA_CLUSTER
                    }, ruta_modelo)
    
    
    metadata={
                    "pipeline": "04_forecast_clustering",
                    "fecha_utc": datetime.now(timezone.utc).isoformat(),
                    "archivo_entrada": str(cfg.RUTA_INPUT_CLUSTER_READY),
                    "archivo_salida": str(ruta_dataset),
                    "n_articulos": len(df_final),
                    "n_variables": len(variables),
                    "variables": list(variables),
                    "k_optimo": k_optimo,
                    "k_codo": int(k_codo) if k_codo is not None else None,
                    "criterion_selection": criterio,
                    "semillas_estabilidad": cfg.SEMILLAS_ESTABILIDAD,
                    "ari_promedio": df_ari_resumen["ari_promedio"].iloc[0],
                    "silhouette_final": df_metricas.loc[df_metricas["k"]==k_optimo, "silhouette_score"].iloc[0],
                    "davies_bouldin_final": df_metricas.loc[df_metricas["k"]==k_optimo, "davies_bouldin_score"].iloc[0],
                    "calinski_harabasz_final": df_metricas.loc[df_metricas["k"]==k_optimo, "calinski_harabasz_score"].iloc[0],
                    "inercia_final": float(modelo.inertia_),
                    "modelo_path": str(ruta_modelo)
                }
    ruta_metadata = rutas["modelos"] / f"{_nombre_seguro(nombre_grupo)}_{cfg.NOMBRE_METADATA_MODELO}"
    ruta_metadata.write_text(
                    json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
                    )
    
    # ETAPA 7 - GRÁFICAS INDEPENDIENTES
    print(f"{prefijo} [7/7] Generando y guardando gráficas...")
    rutas_figuras = _guardar_graficas(
        nombre_grupo, rutas, df_metricas, k_optimo, k_codo, df_ari_detalle,
        df_cluster_tamanos, df_cluster_comparativo, df_clusterizado,
        X_scaled, etiquetas, variables
    )
    print(f"{prefijo} Completado | artículos={len(df_final)} | K={k_optimo} | figuras={len(rutas_figuras)}")
    
    print("\nPipeline 04 - Resumen de resultados:")
    print(f"    Dataset final: {ruta_dataset}")
    print(f"    Modelo KMeans: {ruta_modelo}")
    print(f"  Variables: {len(variables)}")
    print(f"  K final: {k_optimo}")
    print(f"  Graficas: {len(rutas_figuras)} | Tablas: {len(rutas_tablas)}")
    
    return {
            "k_optimo": k_optimo,
            "k_codo": k_codo,
            "criterio": criterio,
            "df_final": df_final,
            "df_metricas": df_metricas,
            "df_cluster_perfiles": df_cluster_perfiles,
            "ruta_dataset": ruta_dataset,
            "ruta_modelo": ruta_modelo,
            "ruta_metadata": ruta_metadata,
            "rutas_tablas": rutas_tablas,
            "rutas_figuras": rutas_figuras,
        }

# ============================================================
# 2. FUNCION PRINCIPAL DEL PIPELINE 04
# ============================================================

def ejecutar_pipeline_clustering():
    """Ejecutar las etapas y devolver un resumen de los resultados."""
    print("\n========== PIPELINE 04: CLUSTERIZACION ==========")
    # ETAPA 1 - DATOS ORIGINALES
    print("\n[1/7] Cargando dataset de Pipeline 03...")
    df_input, df_eda, X, variables = cargar_dataset_cluster()
    
    grupos = segmentar_por_unidad(
        df_input=df_input,
        df_eda=df_eda,
        X=X,
        variables=variables,
        columna_id=cfg.COLUMNA_ID,
        columna_unidad=cfg.COLUMNA_UNIDAD_INVENTARIO,
    )

    resultados={}

    for nombre_grupo, datos in grupos.items():
        print(f"\nProcesando grupo: {nombre_grupo}")

        resultados[nombre_grupo] =ejecutar_clustering_grupo(nombre_grupo=nombre_grupo, **datos)
    print("\n========== PIPELINE 04 COMPLETADO EN TODOS LOS GRUPOS ==========")

    for grupo, resultado in resultados.items():
        print(f"[{grupo}] K={resultado['k_optimo']} | Dataset={resultado['ruta_dataset']} | "
              f"Figuras={len(resultado['rutas_figuras'])} | Tablas={len(resultado['rutas_tablas'])}")
    return resultados
