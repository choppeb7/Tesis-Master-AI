"""
PIPELINE 04 - GRAFICAS DE EVALUACION Y PERFILADO DE CLUSTERS
==========================================================

Objetivo:
    Visualizar los resultados ya calculados por los modulos anteriores.
    Este archivo NO entrena K-Means ni recalcula sus metricas.

Entradas principales:
    df_metricas          : salida de evaluar_modelos_kmeans().
    df_detalle_ari       : segunda salida de evaluar_estabilidad().
    df_cluster_tamanos   : salida de generar_perfiles_clusters().
    df_cluster_comparativo: salida de generar_perfiles_clusters().
    df_clusterizado      : codigo_articulo + variables originales + cluster.
    X_scaled             : matriz preprocesada usada para entrenar K-Means.
    etiquetas            : array de etiquetas del modelo definitivo.

Cada funcion devuelve una figura de Matplotlib (fig).
main_forecast_clustering.py decidira donde y cuando guardarla.
"""

from pathlib import path 

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

from . import clustering_confi as cfg

# ============================================================
# 1. GRAFICAS PARA ELEGIR EL NUMERO DE CLUSTERS (K)
# ============================================================
def graficar_codo(df_metricas, k_optimo, k_codo=None):
    """Grafica inercia Vs. K ymarca el codo estimado y el K elegido"""

    tabla=df_metricas.sort_values("k")

    fig, ax=plt.subplots(figsize=(8,5))
    ax.plot(tabla["k"], tabla["inercia"], marker="o")

    ax.axvline(k_optimo, linestyle="--", color="tab:green",
               label=f"K seleccionado:{k_optimo}")
    ax.set_title("Metodo del codo - K-Means")
    ax.set_xlabel("Numero de clusters (K)")
    ax.set_ylabel("Inercia")
    ax.set_xticks(tabla["k"])
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tighout_layout()
    return fig

def _graficar_metrica(df_metricas, columna, titulo, etiqueta_y, k_optimo)

    tabla=df_metricas.sort_values(by="k")
    x=tabla["k"]
    y=tabla[columna]
    fig, ax= plt.subplots(figsize=(8,5))
    ax.plot(x, y, marker="o")
    
    ax.axvline(k_optimo, linestyle="--", color="tab:green",
               label=f"K seleccionado:{k_optimo}")
    ax.set_title(titulo)
    ax.set_xlabel("Numero de clusters (K)")
    ax.set_ylabel(etiqueta_y)
    ax.set_xticks(tabla["k"])
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tighout_layout()
    return fig

def graficar_silhouette(df_metricas, k_optimo):
    """Silhouette alto indica, en general, grupos mejor separados."""
    return _graficar_metrica(df_metricas, "silhouette_score", 
                             "Silhouette Score vs. K Silhouette (mayor es mejor)",
                             k_optimo
                             )

def graficar_davies_bouldin(df_metricas, k_optimo):
    """Davies-Bouldin bajo indica, en general, grupos mas compactos."""
    return _graficar_metrica(
        df_metricas, "davies_bouldin_score", "Davies-Bouldin vs. K",
        "Davies-Bouldin (menor es mejor)", k_optimo,
    )

def graficar_calinski_harabasz(df_metricas, k_optimo):
    """Calinski-Harabasz alto indica mayor separacion relativa entre grupos."""
    return _graficar_metrica(
        df_metricas, "calinski_harabasz_score", "Calinski-Harabasz vs. K",
        "Calinski-Harabasz (mayor es mejor)", k_optimo,
    )

# ============================================================
# 2. GRAFICA DE ESTABILIDAD ENTRE SEMILLAS (ARI)
# ============================================================
def graficar_estabilidad_ari(df_detalle_ari):
    """Muestra el ARI obtenido para cada pareja de semillas evaluadas."""

    if df_detalle_ari.empty:
        raise ValueError("la tabla de estabilidad ARI esta vacia.")

    # Convertir cada pareja de semillas en un texto para el eje X.
    etiquetas_parejas=(df_detalle_ari["semilla_a"].astype(str)+ "-"
                      + df_detalle_ari["semilla_b"].astype(str))
    fig, ax=plt.subplot(figsize=(max(9, len(df_detalle_ari)*0.75),5 ))
    ax.bar(etiquetas_parejas, df_detalle_ari["ari"])
    ax.axhline(df_detalle_ari["ari"].mean(), color="tab:orange",
               linestyle="--", label="ARI promedio")
    ax.set_title("Estabilidad de K-Means entre semillas (ARI)")
    ax.set_xlabel("Pareja de semillas")
    ax.set_ylabel("Adjusted Rand Index (ARI)")
    ax.set_ylim(-1.05, 1.05)
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    return fig

# ============================================================
# 3. GRAFICAS PARA INTERPRETAR LOS CLUSTERS
# ============================================================
def graficar_distribucion_clusters(df_cluster_tamanos):
    """Cantidad de articulos por cluster, con su porcentaje del inventario."""

    clusters=df_cluster_tamanos[cfg.COLUMNA_CLUSTER]
    cantidades=df_cluster_tamanos["n_articulos"]
    porcentajes=df_cluster_tamanos["porcentaje_articulos"]

    fig, ax= plt.subplots(figsize=(8,5))
    barras= ax.bar([str(c) for c in clusters], cantidades)

    # Escribir cantidad y porcentaje sobre cada barra.
    for barra, cantidad, porcentaje in zip(barras, cantidades, porcentajes):
        ax.annotate(
            f"{int(cantidad):,} ({porcentaje:.1f}%)",
            xy=(barra.get_x() + barra.get_width() / 2, barra.get_height()),
            xytext=(0, 4), textcoords="offset points",
            ha="center", va="bottom", fontsize=9,
        )
        
    ax.set_title("Distribucion de articulos por cluster")
    ax.set_xlabel("Cluster")
    ax.set_ylabel("Numero de articulos")
    ax.set_ylim(0, max(cantidades) * 1.18)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    return fig

def graficar_heatmap_perfiles(df_)
