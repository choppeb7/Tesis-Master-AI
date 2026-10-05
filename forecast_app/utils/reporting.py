from pathlib import Path
import re
import pandas as pd
import matplotlib.pyplot as plt


def limpiar_nombre_archivo(texto):
    """
    Limpia texto para usarlo como nombre de archivo.
    """

    texto = str(texto).strip().lower()
    texto = re.sub(r"[^a-zA-Z0-9_áéíóúñÁÉÍÓÚÑ-]+", "_", texto)
    texto = texto.replace("__", "_")

    return texto


def asegurar_directorio(ruta):
    """
    Crea un directorio si no existe.
    """

    ruta = Path(ruta)
    ruta.mkdir(parents=True, exist_ok=True)

    return ruta




def preparar_resumen_conteo(df, columna, top_n=None):
    """
    Genera una tabla resumen con:
    - categoria
    - cantidad
    - porcentaje
    """

    serie = df[columna].fillna("Sin dato").astype(str).str.strip()

    conteo = serie.value_counts(dropna=False)

    if top_n is not None:
        conteo = conteo.head(top_n)

    df_resumen = conteo.reset_index()
    df_resumen.columns = [columna, "cantidad"]

    total = df_resumen["cantidad"].sum()

    df_resumen["porcentaje"] = (
        df_resumen["cantidad"] / total * 100
    ).round(2)

    return df_resumen


def guardar_grafico_barras_conteo(
    df,
    columna,
    directorio_salida,
    titulo=None,
    nombre_archivo=None,
    top_n=None,
    mostrar_porcentaje=True,
    color_barras="#4C78A8",
    figsize=(10, 6),
    rotacion_xticks=45,
    fontsize_etiqueta=10
):
    """
    Guarda un gráfico de barras con el conteo de una columna categórica.
    Muestra arriba de cada barra:
    - cantidad
    - porcentaje
    """

    directorio_salida = asegurar_directorio(directorio_salida)

    df_resumen = preparar_resumen_conteo(
        df=df,
        columna=columna,
        top_n=top_n
    )

    if titulo is None:
        titulo = f"Distribución de {columna}"

    if nombre_archivo is None:
        nombre_archivo = f"barras_{limpiar_nombre_archivo(columna)}.png"

    ruta_salida = directorio_salida / nombre_archivo

    fig, ax = plt.subplots(figsize=figsize)

    bars = ax.bar(
        df_resumen[columna],
        df_resumen["cantidad"],
        color=color_barras
    )

    # ------------------------------------------------------------
    # Etiquetas sobre cada barra
    # ------------------------------------------------------------
    max_y = df_resumen["cantidad"].max()

    for bar, cantidad, porcentaje in zip(
        bars,
        df_resumen["cantidad"],
        df_resumen["porcentaje"]
    ):
        x = bar.get_x() + bar.get_width() / 2
        y = bar.get_height()

        if mostrar_porcentaje:
            etiqueta = f"{cantidad}\n({porcentaje:.1f}%)"
        else:
            etiqueta = f"{cantidad}"

        ax.text(
            x,
            y + max_y * 0.01,
            etiqueta,
            ha="center",
            va="bottom",
            fontsize=fontsize_etiqueta
        )

    ax.set_title(titulo)
    ax.set_xlabel(columna)
    ax.set_ylabel("Cantidad de artículos")
    ax.set_xticklabels(df_resumen[columna], rotation=45, ha="right")
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(ruta_salida, dpi=500, bbox_inches="tight")
    plt.close()

    return ruta_salida


def guardar_grafico_pastel_conteo(
    df,
    columna,
    directorio_salida,
    titulo=None,
    nombre_archivo=None,
    top_n=None,
    figsize=(8, 8),
    startangle=90,
    mostrar_leyenda=True,
    usar_etiquetas_externas=False
):
    """
    Guarda un gráfico de pastel con:
    - porcentaje
    - cantidad

    Puede mostrar:
    - texto dentro del segmento
    - o leyenda lateral con categoría, cantidad y porcentaje
    """

    directorio_salida = asegurar_directorio(directorio_salida)

    df_resumen = preparar_resumen_conteo(
        df=df,
        columna=columna,
        top_n=top_n
    )

    if titulo is None:
        titulo = f"Distribución porcentual de {columna}"

    if nombre_archivo is None:
        nombre_archivo = f"pastel_{limpiar_nombre_archivo(columna)}.png"

    ruta_salida = directorio_salida / nombre_archivo

    valores = df_resumen["cantidad"]
    categorias = df_resumen[columna]

    def autopct_personalizado(pct):
        total = valores.sum()
        cantidad = int(round(pct * total / 100.0))
        return f"{pct:.1f}%\n({cantidad})"

    fig, ax = plt.subplots(figsize=figsize)

    if usar_etiquetas_externas:
        wedges, texts, autotexts = ax.pie(
            valores,
            labels=categorias,
            autopct=autopct_personalizado,
            startangle=startangle
        )
    else:
        wedges, texts, autotexts = ax.pie(
            valores,
            autopct=autopct_personalizado,
            startangle=startangle
        )

    ax.set_title(titulo)
    ax.axis("equal")

    # ------------------------------------------------------------
    # Leyenda con detalle completo
    # ------------------------------------------------------------
    if mostrar_leyenda:
        etiquetas_leyenda = [
            f"{cat} | {cant} ({pct:.1f}%)"
            for cat, cant, pct in zip(
                df_resumen[columna],
                df_resumen["cantidad"],
                df_resumen["porcentaje"]
            )
        ]

        ax.legend(
            wedges,
            etiquetas_leyenda,
            title=columna,
            loc="center left",
            bbox_to_anchor=(1, 0.5)
        )

    plt.tight_layout()
    plt.savefig(ruta_salida, dpi=500, bbox_inches="tight")
    plt.close()
# 

    return ruta_salida


def guardar_tabla_resumen_segmento(
    df,
    columna_segmento,
    directorio_salida,
    nombre_archivo="resumen_segmento_forecast.xlsx"
):
    """
    Guarda una tabla resumen por segmento.
    """

    directorio_salida = asegurar_directorio(directorio_salida)

    columnas_metricas = [
        "total_unidades_vendidas_24m",
        "venta_promedio_mensual_24m",
        "meses_con_venta_24m",
        "frecuencia_venta_24m_pct",
        "conteo_facturas_24m",
        "alcance_inventario_24m"
    ]

    columnas_metricas = [
        col for col in columnas_metricas
        if col in df.columns
    ]

    resumen = (
        df
        .groupby(columna_segmento, dropna=False)
        .agg(
            cantidad_articulos=(columna_segmento, "size"),
            **{
                f"promedio_{col}": (col, "mean")
                for col in columnas_metricas
            }
        )
        .reset_index()
    )

    total_articulos = resumen["cantidad_articulos"].sum()

    resumen["participacion_pct"] = (
        resumen["cantidad_articulos"] / total_articulos * 100
    ).round(2)

    ruta_salida = directorio_salida / nombre_archivo

    resumen.to_excel(ruta_salida, index=False)

    return ruta_salida


