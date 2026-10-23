from pathlib import Path
import numpy as np
import pandas as pd


def exportar_dataset_cluster(
    df_eda_final,
    resultado_correlacion,
    variables_candidatas,
    ruta_salida,
    columna_id="codigo_articulo"
):
    """
    Exporta un único Excel con el dataset preparado
    para clustering y los resultados del EDA.
    """

    ruta_salida = Path(ruta_salida)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------
    # 1. Obtener variables seleccionadas por correlación
    # --------------------------------------------------------

    variables_seleccionadas = list(dict.fromkeys(
        resultado_correlacion["seleccionadas"]
    ))

    variables_eliminadas = set(
        resultado_correlacion["eliminadas"]
    )

    variables_constantes = set(
        resultado_correlacion["constantes"]
    )

    if not variables_seleccionadas:
        raise ValueError(
            "No hay variables seleccionadas para clustering."
        )

    # --------------------------------------------------------
    # 2. Validar que todas las variables existan
    # --------------------------------------------------------

    columnas_requeridas = [
        columna_id
    ] + variables_seleccionadas

    columnas_faltantes = [
        columna
        for columna in columnas_requeridas
        if columna not in df_eda_final.columns
    ]

    if columnas_faltantes:
        raise ValueError(
            f"Columnas faltantes: {columnas_faltantes}"
        )

    if (
        df_eda_final[columna_id].isna().any()
        or not df_eda_final[columna_id].is_unique
    ):
        raise ValueError(
            "Los códigos de artículo deben ser únicos y no nulos."
        )

    # --------------------------------------------------------
    # 3. Construir dataset de entrada del clustering
    # --------------------------------------------------------

    df_cluster_input = df_eda_final[
        columnas_requeridas
    ].copy()

    datos_numericos = df_cluster_input[
        variables_seleccionadas
    ].apply(pd.to_numeric, errors="raise")

    if not np.isfinite(
        datos_numericos.to_numpy(dtype=float)
    ).all():
        raise ValueError(
            "Existen valores NaN o infinitos en el dataset."
        )

    df_cluster_input[variables_seleccionadas] = datos_numericos

    # --------------------------------------------------------
    # 4. Documentar selección de variables
    # --------------------------------------------------------

    def obtener_estado(variable):

        if variable in variables_seleccionadas:
            return "Seleccionada"

        if variable in variables_constantes:
            return "Constante"

        if variable in variables_eliminadas:
            return "Descartada por correlación"

        return "Revisar"

    df_seleccion = pd.DataFrame({
        "variable": variables_candidatas,
        "estado": [
            obtener_estado(variable)
            for variable in variables_candidatas
        ]
    })

    # --------------------------------------------------------
    # 5. Exportar Excel consolidado
    # --------------------------------------------------------

    with pd.ExcelWriter(
        ruta_salida,
        engine="openpyxl"
    ) as writer:

        df_cluster_input.to_excel(
            writer,
            sheet_name="cluster_input",
            index=False
        )

        df_eda_final.to_excel(
            writer,
            sheet_name="eda_completo",
            index=False
        )

        df_seleccion.to_excel(
            writer,
            sheet_name="seleccion_variables",
            index=False
        )

        resultado_correlacion["matriz"].to_excel(
            writer,
            sheet_name="matriz_correlacion"
        )

        resultado_correlacion["pares"].to_excel(
            writer,
            sheet_name="pares_correlacionados",
            index=False
        )

    print(f"Dataset clustering exportado: {ruta_salida}")

    return df_cluster_input