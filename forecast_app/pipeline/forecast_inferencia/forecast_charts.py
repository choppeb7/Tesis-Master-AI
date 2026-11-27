
from pathlib import Path
import sys
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FORECAST_APP_DIR = PROJECT_ROOT / "forecast_app"

if str(FORECAST_APP_DIR) not in sys.path:
    sys.path.insert(0, str(FORECAST_APP_DIR))

REPORTS_DIR = FORECAST_APP_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures" / "05_forecast_inferencia"
TABLES_DIR = REPORTS_DIR / "tables" / "05_forecast_inferencia"

import pipeline.forecast_inferencia.forecast_config as cfg


from utils.reporting import (
    guardar_grafico_barras_conteo,
    guardar_grafico_histograma,
    guardar_grafico_pastel_conteo,
)

import matplotlib.pyplot as plt
def guardar_graficos_forecast(resultados):
    df_best_model = resultados["df_best_model"]

    guardar_grafico_barras_conteo(
        df=df_best_model,
        columna="best_model",
        titulo="Distribución de mejores modelos por artículo",
        directorio_salida=FIGURES_DIR,
        nombre_archivo="mejores_modelos_por_articulo_barras.png",
    )
    guardar_grafico_pastel_conteo(
        df=df_best_model,
        columna="best_model",
        titulo="Distribución de mejores modelos por artículo",
        directorio_salida=FIGURES_DIR,
        nombre_archivo="mejores_modelos_por_articulo_pastel.png",
    )

#==============================================================
#3.GENERAMOS HISTOGRAMA DE WAPE_RANKING DEL MODELO GANADOR POR ARTICULO
#==============================================================

    wape = pd.to_numeric(
        df_best_model["WAPE_ranking"],
        errors="coerce",
    ).astype("float64")

    mascara_finitos = np.isfinite(wape)
    df_wape_finitos = df_best_model.loc[mascara_finitos].copy()
    df_wape_finitos["WAPE_ranking"] = wape.loc[mascara_finitos]

    total = len(wape)
    cantidad_inf = int(np.isinf(wape).sum())
    porcentaje_inf = 100 * cantidad_inf / total if total else 0

    if not df_wape_finitos.empty:
        guardar_grafico_histograma(
            df_wape_finitos,
            columna="WAPE_ranking",
            directorio_salida=FIGURES_DIR,
            titulo=(
                "Distribución de WAPE_ranking de los modelos ganadores\n"
                f"Infinitos: {cantidad_inf:,} de {total:,} artículos "
                f"({porcentaje_inf:.1f} %)"
            ),
            nombre_archivo="03_distribucion_wape_ranking.png",
        )
#==============================================================
#4.GENERAMOS DISTRIBUCION CATEGORICA DE WAPE_RANKING DEL MODELO GANADOR POR ARTICULO
#==============================================================
    
    guardar_grafico_barras_conteo(
        df=df_best_model,
        columna="WAPE_categoria",
        directorio_salida=FIGURES_DIR,
        titulo="Modelos ganadores por rango de WAPE_ranking",
        nombre_archivo="04_wape_ranking_por_categoria.png",
    )
#==============================================================
#5.GENERAMOS DISTRIBUCION DEL SESGO ABSOLUTO DE LOS MODELOS GANADORES
#==============================================================
    guardar_grafico_histograma(
        df=df_best_model,
        columna="bias_total_abs_periodo_evaluacion",
        directorio_salida=FIGURES_DIR,
        titulo="Distribución del sesgo absoluto de los modelos ganadores",
        nombre_archivo="05_distribucion_sesgo_absoluto.png",
    )

    guardar_modelos_ganadores_por_cluster(resultados)
    guardar_dummy_por_categoria_wape(resultados["df_dummy_por_categoria_wape"])

#==============================================================
#6.GENERAMOS DISTRIBUCION DE MODELOS GANADORES POR CLUSTER GLOBAL
#==============================================================
def guardar_modelos_ganadores_por_cluster(resultados):
    df_modelos = resultados["df_best_model"][["unique_id", "best_model"]]
    df_clusters = resultados["df_resultado_final"][
        ["codigo_articulo", "cluster_global"]
    ].rename(columns={"codigo_articulo": "unique_id"})

    df_modelo_cluster = df_modelos.merge(
        df_clusters,
        on="unique_id",
        how="left",
        validate="one_to_one",
    ).dropna(subset=["cluster_global", "best_model"])

    if df_modelo_cluster.empty:
        return

    conteos = pd.crosstab(
        df_modelo_cluster["cluster_global"],
        df_modelo_cluster["best_model"],
    ).sort_index()
    totales = conteos.sum(axis=1)
    porcentajes = conteos.div(totales, axis=0).mul(100)

    fig, ax = plt.subplots(figsize=(11, 6))
    try:
        paleta = plt.get_cmap("tab20")
        colores = {
            modelo: paleta(i % paleta.N)
            for i, modelo in enumerate(porcentajes.columns)
        }
        barras_por_modelo = {}

        for posicion, (_, fila) in enumerate(porcentajes.iterrows()):
            participaciones = fila[fila > 0].sort_values(
                ascending=False, kind="stable"
            )
            base = 0.0

            for modelo, porcentaje in participaciones.items():
                barra = ax.bar(
                    posicion,
                    porcentaje,
                    bottom=base,
                    color=colores[modelo],
                )
                barras_por_modelo[modelo] = barra
                ax.text(
                    posicion,
                    base + porcentaje / 2,
                    f"{porcentaje:.1f} %",
                    ha="center",
                    va="center",
                    fontsize=8,
                    bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "none", "pad": 1},
                )
                base += porcentaje

        ax.set_xticks(range(len(porcentajes)))
        ax.set_title("Modelos ganadores por cluster global")
        ax.set_xlabel("Cluster global")
        ax.set_ylabel("Artículos dentro del cluster (%)")
        ax.set_ylim(0, 100)
        ax.set_xticklabels([
            f"{cluster:g}\nn = {total:,}"
            for cluster, total in totales.items()
        ])
        ax.legend(
            handles=[barras_por_modelo[modelo] for modelo in porcentajes.columns],
            labels=porcentajes.columns.tolist(),
            title="Modelo ganador",
            bbox_to_anchor=(1.02, 1),
            loc="upper left",
        )

        FIGURES_DIR.mkdir(parents=True, exist_ok=True)
        fig.savefig(
            FIGURES_DIR / "06_modelos_ganadores_por_cluster_global.png",
            dpi=300,
            bbox_inches="tight",
        )
    finally:
        plt.close(fig)

#==============================================================
#6.GENERAMOS participacion de modelo dummy por categoria de WAPE
#==============================================================
def guardar_dummy_por_categoria_wape(resumen):
    if resumen.empty:
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    try:
        barras = ax.bar(resumen["WAPE_categoria"], resumen["pct_dummy"])
        etiquetas = [
            f"{pct:.1f} % ({victorias}/{total})"
            for pct, victorias, total in zip(
                resumen["pct_dummy"],
                resumen["victorias_dummy"],
                resumen["articulos"],
            )
        ]
        ax.bar_label(barras, labels=etiquetas, padding=3)
        ax.set_title("Tasa de victoria del modelo dummy por categoría de WAPE")
        ax.set_xlabel("Categoría de WAPE_ranking")
        ax.set_ylabel("Artículos donde ganó el dummy (%)")
        ax.set_yticks(range(0, 101, 20))
        ax.set_ylim(0, 110)
        ax.tick_params(axis="x", labelrotation=25)

        FIGURES_DIR.mkdir(parents=True, exist_ok=True)
        fig.savefig(
            FIGURES_DIR / "07_dummy_por_categoria_wape.png",
            dpi=200,
            bbox_inches="tight",
        )
    finally:
        plt.close(fig)