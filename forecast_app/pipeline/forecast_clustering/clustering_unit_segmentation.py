
"""
PIPELINE 04 - SEGMENTACION POR UNIDAD DE INVENTARIO
===================================================
Separa los artículos antes del preprocesamiento.

Grupo A: artículos por unidad.
Grupo B: artículos por longitud o superficie.
"""

import pandas as pd


def segmentar_por_unidad(
    df_input,
    df_eda,
    X,
    variables,
    columna_id="codigo_articulo",
    columna_unidad="unidad_medida_inventario",
):
    """Genera dos grupos conservando el orden de los artículos."""

    # Normalizar unidades a partir del EDA completo.
    unidades = df_eda[[columna_id, columna_unidad]].copy()

    unidades[columna_unidad] = (
        unidades[columna_unidad]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    mapa_unidades = {
        "UNI": "unidades",
        "UND": "unidades",
        "UNIDAD": "unidades",
        "CM": "dimensionales",
        "CM2": "dimensionales",
        #"CM²": "dimensionales",
        "MM": "dimensionales",
        "COSTI": "dimensionales",
        "PIE": "dimensionales",
        "MT": "dimensionales"
    }

    unidades["grupo_unidad"] = unidades[columna_unidad].map(
        mapa_unidades
    )

    # No asignar silenciosamente unidades desconocidas.
    sin_clasificar = unidades["grupo_unidad"].isna()

    if sin_clasificar.any():
        raise ValueError(
            "Existen unidades de inventario sin clasificar: "
            f"{unidades.loc[sin_clasificar, columna_unidad].unique().tolist()}"
        )

    # Añadir grupo al dataset de entrada, por código de artículo.
    base = df_input[[columna_id]].merge(
        unidades[[columna_id, "grupo_unidad"]],
        on=columna_id,
        how="left",
        validate="one_to_one",
        sort=False,
    )

    grupos = {}

    for nombre_grupo in ["unidades", "dimensionales"]:

        mascara = base["grupo_unidad"].eq(nombre_grupo).to_numpy()

        df_grupo = df_input.loc[mascara].reset_index(drop=True)
        X_grupo = X.loc[mascara].reset_index(drop=True)

        codigos = df_grupo[[columna_id]]

        eda_grupo = codigos.merge(
            df_eda,
            on=columna_id,
            how="left",
            validate="one_to_one",
            sort=False,
        )

        grupos[nombre_grupo] = {
            "df_input": df_grupo,
            "df_eda": eda_grupo,
            "X": X_grupo,
            "variables": list(variables),
        }

        print(
            f"Grupo {nombre_grupo}: "
            f"{len(df_grupo)} artículos"
        )

    return grupos
