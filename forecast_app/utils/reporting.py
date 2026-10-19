from pathlib import Path
import re
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

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

def _serie_numerica_valida(df, columna):
    """Obtiene valores numéricos finitos sin modificar el DataFrame original."""
    if columna not in df.columns:
        raise ValueError(f"No existe la columna '{columna}'.")
    datos = pd.to_numeric(df[columna], errors="coerce")
    datos = datos.replace([np.inf, -np.inf], np.nan).dropna()
    if datos.empty:
        raise ValueError(f"La columna '{columna}' no tiene datos numéricos válidos.")
    return datos


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

def guardar_grafico_histograma(
    df, 
    columna, 
    directorio_salida, 
    titulo=None, 
    nombre_archivo=None,
    bins=30, 
    dpi=300, 
    figsize=(10, 6), 
    escala_x="lineal"
):
    """Histograma de una variable cuantitativa; anota n y porcentaje de ceros."""
    if titulo is None:
        titulo = f"Distribución de {columna}"

    if nombre_archivo is None:
        nombre_archivo = f"hist_{limpiar_nombre_archivo(columna)}.png"

    valores = _serie_numerica_valida(df, columna)
    directorio_salida = asegurar_directorio(directorio_salida)
    
    ruta_salida = directorio_salida / nombre_archivo

    fig, ax = plt.subplots(figsize=figsize)
    try:
        ax.hist(valores.to_numpy(), bins=bins, edgecolor="white")
        ax.set_title(titulo or f"Distribución de {columna}")
        ax.set_xlabel(columna)
        ax.set_ylabel("Cantidad de artículos")
        ax.grid(axis="y", alpha=0.25)
        if escala_x == "symlog":
            ax.set_xscale("symlog", linthresh=1)
        elif escala_x != "lineal":
            raise ValueError("escala_x debe ser 'lineal' o 'symlog'.")
        ceros = int((valores == 0).sum())
        ax.text(
            0.98, 0.96,
            f"n = {len(valores):,}\nCeros = {100 * ceros / len(valores):.1f}%",
            transform=ax.transAxes, ha="right", va="top",
            bbox={"facecolor": "white", "alpha": 0.85, "edgecolor": "lightgray"},
        )
        fig.tight_layout()
        fig.savefig(ruta_salida, dpi=dpi, bbox_inches="tight")
    finally:
        plt.close(fig)
    return ruta_salida

def guardar_grafico_boxplot(
    df, 
    columna, 
    directorio_salida, 
    titulo=None, 
    nombre_archivo=None,
    dpi=300, 
    figsize=(10, 3.5), 
    escala_x="lineal"
):
    """Boxplot horizontal con puntos fuera de los bigotes IQR × 1.5."""
    
    if titulo is None:
        titulo = f"Distribución de {columna}"

    if nombre_archivo is None:
        nombre_archivo = f"box_{limpiar_nombre_archivo(columna)}.png"

    valores = _serie_numerica_valida(df, columna)
    directorio_salida = asegurar_directorio(directorio_salida)
    
    ruta_salida = directorio_salida / nombre_archivo
    fig, ax = plt.subplots(figsize=figsize)

    try:
        ax.boxplot(valores.to_numpy(), vert=False, showfliers=True, whis=1.5)
        ax.set_title(titulo or f"Boxplot de {columna}")
        ax.set_xlabel(columna)
        ax.grid(axis="x", alpha=0.25)
        ax.set_yticks([])
        if escala_x == "symlog":
            ax.set_xscale("symlog", linthresh=1)
        elif escala_x != "lineal":
            raise ValueError("escala_x debe ser 'lineal' o 'symlog'.")
        fig.tight_layout()
        fig.savefig(ruta_salida, dpi=dpi, bbox_inches="tight")
    finally:
        plt.close(fig)
    return ruta_salida

def guardar_grafico_dispersion_variables(
    df, 
    columna_x, 
    columna_y, 
    directorio_salida,
    titulo=None, 
    nombre_archivo=None, 
    dpi=300,
    figsize=(9, 6), 
    escala_x="lineal", 
    escala_y="lineal"
):
    """Dispersión de dos columnas numéricas con Spearman calculado por pares."""

    if titulo is None:
        titulo = f"Dispersión de {columna_x} vs. {columna_y}"

    if nombre_archivo is None:
        nombre_archivo = f"scatter_{limpiar_nombre_archivo(columna_x)}_vs_{limpiar_nombre_archivo(columna_y)}.png"

    for columna in (columna_x, columna_y):
        if columna not in df.columns:
            raise ValueError(f"No existe la columna '{columna}'.")
    pares = pd.DataFrame({
        "x": pd.to_numeric(df[columna_x], errors="coerce"),
        "y": pd.to_numeric(df[columna_y], errors="coerce"),
    }).replace([np.inf, -np.inf], np.nan).dropna()
    if pares.empty:
        raise ValueError("No hay observaciones válidas para la dispersión.")
    directorio_salida = asegurar_directorio(directorio_salida)
    nombre_archivo = nombre_archivo or (
        f"scatter_{limpiar_nombre_archivo(columna_x)}"
        f"_vs_{limpiar_nombre_archivo(columna_y)}.png"
    )
    ruta_salida = directorio_salida / nombre_archivo

    rho = pares["x"].corr(pares["y"], method="spearman")#Coeficiente de correlación de Spearman

    texto_rho = f"{rho:.3f}" if pd.notna(rho) else "no definida"
    fig, ax = plt.subplots(figsize=figsize)
    try:
        ax.scatter(pares["x"], pares["y"], alpha=0.45, s=14)
        ax.set_title(titulo or f"{columna_y} vs. {columna_x}")
        ax.set_xlabel(columna_x)
        ax.set_ylabel(columna_y)
        ax.grid(alpha=0.2)
        for eje, escala in (("x", escala_x), ("y", escala_y)):
            if escala == "symlog":
                getattr(ax, f"set_{eje}scale")("symlog", linthresh=1)
            elif escala != "lineal":
                raise ValueError("Las escalas deben ser 'lineal' o 'symlog'.")
        ax.text(
            0.02, 0.98, f"n = {len(pares):,}\nSpearman ρ = {texto_rho}",
            transform=ax.transAxes, va="top",
            bbox={"facecolor": "white", "alpha": 0.85, "edgecolor": "lightgray"},
        )
        fig.tight_layout()
        fig.savefig(ruta_salida, dpi=dpi, bbox_inches="tight")
    finally:
        plt.close(fig)
    return ruta_salida


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
    # Rotar las etiquetas del eje X correctamente
    ax.tick_params(
    axis="x",
    labelrotation=rotacion_xticks
    )

    for etiqueta in ax.get_xticklabels():
        etiqueta.set_ha("right")

    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(ruta_salida, dpi=500, bbox_inches="tight")
    print(f"Gráfico de barras exportado correctamente ✅ Ruta: {ruta_salida}")
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
    print(f"Gráfico de pastel exportado correctamente ✅ Ruta: {ruta_salida}")
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


