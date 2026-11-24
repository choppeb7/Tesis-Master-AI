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

from pathlib import Path 

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

from . import clustering_config as cfg

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
    fig.tight_layout()
    return fig

def _graficar_metrica(df_metricas, columna, titulo, etiqueta_y, k_optimo):

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
    fig.tight_layout()
    return fig

def graficar_silhouette(df_metricas, k_optimo):
    """Silhouette alto indica, en general, grupos mejor separados."""
    return _graficar_metrica(df_metricas, "silhouette_score", 
                             "Silhouette Score vs. K Silhouette (mayor es mejor)", "silhouette_score",
                             k_optimo
                             )

def graficar_davies_bouldin(df_metricas, k_optimo):
    """Davies-Bouldin bajo indica, en general, grupos mas compactos."""
    return _graficar_metrica(
        df_metricas, "davies_bouldin_score", "Davies-Bouldin vs. K",
        "Davies-Bouldin (menor es mejor)", k_optimo
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
    fig, ax=plt.subplots(figsize=(max(9, len(df_detalle_ari)*0.75),5 ))
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

def graficar_heatmap_perfiles(df_cluster_comparativo):
    """Compara las medias de los clusters con la media general, en desv. est.
    
        Positivo: media del cluster superior a la media general.
        Negativo: media del cluster inferior a la media general.
        No disponible: la desviacion estandar general era cero.
        """
    # Filas: variables matematicas. Columnas: clusters.
    print(df_cluster_comparativo.columns.tolist())
    print(df_cluster_comparativo.shape)
    print(df_cluster_comparativo.head())
    matriz = df_cluster_comparativo.pivot(
        index="variable",
        columns="nombre_cluster",
        values="diferencia_estandarizada"
    )

    valores=matriz.to_numpy(dtype=float)
    

    limite=max(1.0, np.max(np.abs(valores))) if valores.size else 1.0

    fig, ax = plt.subplots(figsize=(max(7, 1.1 * len(matriz.columns) + 3),
                                     max(5, 0.5 * len(matriz.index) + 2)))

    #Enmascarar celdas que no tiene valor estadistico calculable.

    imagen=ax.imshow(np.ma.masked_invalid(valores), cmap="RdBu_r",
                     vmin=-limite, vmax=limite, aspect="auto")
    ax.set_xticks(range(len(matriz.columns)))
    ax.set_xticklabels([str(c) for c in matriz.columns])
    ax.set_yticks(range(len(matriz.index)))
    ax.set_yticklabels(matriz.index)
    ax.set_xlabel("Cluster")
    ax.set_ylabel("Variable matematica")
    ax.set_title("Perfil de cada cluster frente al inventario completo")
    
    # Mostrar los valores de cada celda para facilitar su lectura.
    for i in range(len(matriz.index)):
        for j in range(len(matriz.columns)):
            valor = valores[i, j]
            texto = f"{valor:+.2f}" if np.isfinite(valor) else "N/D"
            color = "white" if np.isfinite(valor) and abs(valor) > limite * 0.6 else "black"
            ax.text(j, i, texto, ha="center", va="center", color=color, fontsize=9)

    fig.colorbar(imagen, ax=ax, label="Diferencia de medias (desv. est. general)")
    fig.tight_layout()
    return fig

def graficar_boxplots_variables(df_clusterizado, variables=None):
    """Compara las variables ORIGINALES entre clusters mediante boxplots.

    variables=None: se muestran todas las variables matematicas disponibles.
    Para limitar la cantidad de graficos, pasar una lista de variables.
    Los valores atipicos se ocultan visualmente para facilitar la lectura;
    NO se eliminan de los datos ni de los calculos estadisticos.
    """

    columna_cluster = cfg.COLUMNA_CLUSTER

    if variables is None:
        variables = [
            columna for columna in df_clusterizado.columns
            if columna not in [cfg.COLUMNA_ID, columna_cluster]
        ]

    if not variables:
        raise ValueError("No hay variables para dibujar boxplots.")

    faltantes = [v for v in variables if v not in df_clusterizado.columns]
    if faltantes:
        raise ValueError(f"Variables no encontradas: {faltantes}")

    clusters = sorted(df_clusterizado[columna_cluster].unique())
    n_columnas = 2
    n_filas = int(np.ceil(len(variables) / n_columnas))
    fig, ejes = plt.subplots(n_filas, n_columnas,
                             figsize=(13, 4 * n_filas), squeeze=False)

    for posicion, variable in enumerate(variables):
        ax = ejes.flat[posicion]

        # Crear una serie de valores por cada cluster.
        series = [
            df_clusterizado.loc[
                df_clusterizado[columna_cluster] == cluster, variable
            ].to_numpy(dtype=float)
            for cluster in clusters
        ]

        ax.boxplot(series, showfliers=False)
        ax.set_xticks(range(1, len(clusters) + 1))
        ax.set_xticklabels([str(c) for c in clusters])
        ax.set_title(variable)
        ax.set_xlabel("Cluster")
        ax.set_ylabel("Valor original")
        ax.grid(axis="y", alpha=0.25)

    # Si el numero de variables es impar, ocultar el ultimo cuadro vacio.
    for posicion in range(len(variables), len(ejes.flat)):
        ejes.flat[posicion].set_visible(False)

    fig.suptitle("Distribucion de variables originales por cluster")
    fig.tight_layout()
    return fig

# ============================================================
# 4. VISUALIZAR LA ESTRUCTURA DE CLUSTERS MEDIANTE PCA
# ============================================================

def graficar_pca_clusters(X_scaled, etiquetas):
    """Reduce la dimensionalidad de los datos a 2D y dibuja los clusters."""

    if X_scaled.shape[0] != len(etiquetas):
        raise ValueError(
            "El numero de filas de X_scaled no coincide con el numero de etiquetas."
        )

    pca = PCA(n_components=3)
    X_pca = pca.fit_transform(X_scaled)

    fig, ax = plt.subplots(figsize=(8, 6), subplot_kw=dict(projection="3d"))
    scatter = ax.scatter(X_pca[:, 0], X_pca[:, 1], X_pca[:, 2], c=etiquetas, cmap="tab10", alpha=0.7)
    legend1 = ax.legend(*scatter.legend_elements(), title="Clusters")
    ax.add_artist(legend1)
    ax.set_title("Visualizacion PCA de clusters")
    ax.set_xlabel("Componente principal 1")
    ax.set_ylabel("Componente principal 2")
    ax.set_zlabel("Componente principal 3")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    return fig

# ============================================================
# 5. GUARDADO DE FIGURAS (USADO POR EL ORQUESTADOR)
# ============================================================

def guardar_figura(figura, nombre_archivo, carpeta=cfg.FIGURES_DIR):
    """Guarda la figura PNG y cierra el objeto para liberar memoria.

    El orquestador decide cuando llamar esta funcion.
    Devuelve la ruta del archivo generado.
    """

    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta_archivo= carpeta / nombre_archivo
    figura.savefig(
            ruta_archivo,
            dpi=cfg.DPI_FIGURAS,
            bbox_inches="tight",
            facecolor="white"
        )

    print(f"Figura guardada correctamente: {ruta_archivo}")