from pathlib import Path
import numpy as np
import pandas as pd


def exportar_dataset_cluster_ready(
    df_ventas,
    df_eda_final,
    resultados_correlacion,
    ruta_salida,
    columna_id="codigo_articulo"
):
    """
    Consolida la salida del Pipeline 03 en un Excel
    que servirá como entrada del Pipeline 04.
    """

    ruta_salida = Path(ruta_salida)

    # 1. Variables seleccionadas por correlación
    seleccionadas = list(dict.fromkeys(
        resultados_correlacion["seleccionadas"]
    ))

    if not seleccionadas:
        raise ValueError(
            "No existen variables seleccionadas para clustering."
        )

    # 2. Validar columnas e identificadores
    columnas_requeridas = [columna_id] + seleccionadas

    faltantes = [
        c for c in columnas_requeridas
        if c not in df_eda_final.columns
    ]

    if faltantes:
        raise ValueError(
            f"Faltan columnas para clustering: {faltantes}"
        )

    if (
        df_eda_final[columna_id].isna().any()
        or not df_eda_final[columna_id].is_unique
    ):
        raise ValueError(
            "Existen códigos de artículo nulos o duplicados."
        )

    # 3. Preparar entrada numérica del clustering
    df_cluster_input = df_eda_final[
        columnas_requeridas
    ].copy()

    df_cluster_input[seleccionadas] = (
        df_cluster_input[seleccionadas]
        .apply(pd.to_numeric, errors="raise")
    )

    if not np.isfinite(
        df_cluster_input[seleccionadas].to_numpy(dtype=float)
    ).all():
        raise ValueError(
            "Existen valores no finitos en el dataset de clustering."
        )

    # 4. Tabla de selección de variables
    descartadas = set(
        resultados_correlacion["eliminadas"]
    )
    constantes = set(
        resultados_correlacion["constantes"]
    )

    variables_evaluadas = list(dict.fromkeys(
        seleccionadas
        + list(descartadas)
        + list(constantes)
    ))

    df_seleccion = pd.DataFrame({
        "variable": variables_evaluadas,
        "estado": [
            "Seleccionada" if v in seleccionadas
            else "Constante" if v in constantes
            else "Descartada por correlación"
            for v in variables_evaluadas
        ]
    })

    # 5. Exportación consolidada
    ruta_salida.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with pd.ExcelWriter(
        ruta_salida,
        engine="openpyxl"
    ) as writer:
        
        df_ventas.reset_index().to_excel(
            writer,
            sheet_name="matriz_ventas",
            index=False
            )

        df_eda_final.to_excel(
            writer,
            sheet_name="matriz_ventas_con_feature_eng",
            index=False
        )

        df_cluster_input.to_excel(
            writer,
            sheet_name="cluster_input",
            index=False
        )


        df_seleccion.to_excel(
            writer,
            sheet_name="seleccion_variables",
            index=False
        )

        resultados_correlacion["matriz"].to_excel(
            writer,
            sheet_name="matriz_correlacion"
        )

        resultados_correlacion["pares"].to_excel(
            writer,
            sheet_name="pares_correlacionados",
            index=False
        )

    print(f"\nArchivo para clustering: {ruta_salida}")
    print(f"Artículos: {len(df_cluster_input)}")
    print(f"Variables seleccionadas: {len(seleccionadas)}")

    return df_cluster_input