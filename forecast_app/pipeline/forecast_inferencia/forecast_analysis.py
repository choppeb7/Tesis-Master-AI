def resumir_dummy_por_categoria_wape(df_best_model):
    """Resume las victorias del dummy dentro de cada categoría de WAPE."""
    gana_dummy = df_best_model["best_model"].str.startswith(
        "Dummy_promedio_", na=False
    )

    resumen = (
        df_best_model.assign(gana_dummy=gana_dummy)
        .groupby("WAPE_categoria", sort=False)["gana_dummy"]
        .agg(articulos="size", victorias_dummy="sum")
        .reset_index()
    )
    resumen["pct_dummy"] = (
        100 * resumen["victorias_dummy"] / resumen["articulos"]
    ).round(1)

    return resumen