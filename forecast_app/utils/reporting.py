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




def guardar_grafico_barras_conteo(
    df,
    columna,
    directorio_salida,
    titulo=None,
    nombre_archivo=None,
    top_n=None
):
    """
    Guarda un gráfico de barras con el conteo de una columna categórica.
    """

    directorio_salida = asegurar_directorio(directorio_salida)

    conteo = df[columna].value_counts(dropna=False)

    if top_n is not None:
        conteo = conteo.head(top_n)

    if titulo is None:
        titulo = f"Distribución de {columna}"

    if nombre_archivo is None:
        nombre_archivo = f"barras_{limpiar_nombre_archivo(columna)}.png"

    ruta_salida = directorio_salida / nombre_archivo

    plt.figure(figsize=(10, 6))
    conteo.plot(kind="bar")

    plt.title(titulo)
    plt.xlabel(columna)
    plt.ylabel("Cantidad de artículos")
    plt.xticks(rotation=45, ha="right")
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
    top_n=None
):
    """
    Guarda un gráfico de pastel con el conteo porcentual de una columna categórica.
    Recomendado para columnas con pocas categorías.
    """

    directorio_salida = asegurar_directorio(directorio_salida)

    conteo = df[columna].value_counts(dropna=False)

    if top_n is not None:
        conteo = conteo.head(top_n)

    if titulo is None:
        titulo = f"Distribución porcentual de {columna}"

    if nombre_archivo is None:
        nombre_archivo = f"pastel_{limpiar_nombre_archivo(columna)}.png"

    ruta_salida = directorio_salida / nombre_archivo

    plt.figure(figsize=(8, 8))
    conteo.plot(kind="pie", autopct="%1.1f%%", startangle=90)

    plt.title(titulo)
    plt.ylabel("")
    plt.tight_layout()

    plt.savefig(ruta_salida, dpi=500, bbox_inches="tight")
    plt.close()

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


