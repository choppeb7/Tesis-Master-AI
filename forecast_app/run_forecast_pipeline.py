# ============================================================
# Ejecutar pipeline completo de forecast
# ============================================================

from pathlib import Path

from pipeline.main_pipeline import ejecutar_pipeline_forecast


def main():
    print("=" * 80)
    print("INICIANDO PIPELINE DE FORECAST")
    print("=" * 80)

    # ------------------------------------------------------------
    # Definir rutas base
    # ------------------------------------------------------------

    BASE_DIR = Path(__file__).resolve().parent

    ruta_excel = (
        BASE_DIR
        / "data"
        / "input"
        / "df_matriz_ventas_articulos_forecast.xlsx"
    )

    ruta_exportacion = (
        BASE_DIR
        / "data"
        / "output"
        / "resultado_forecast_compra_sugerida.xlsx"
    )

    print("\nRuta base:")
    print(BASE_DIR)

    print("\nRuta archivo entrada:")
    print(ruta_excel)

    print("\nRuta archivo salida:")
    print(ruta_exportacion)

    # ------------------------------------------------------------
    # Validar existencia del archivo de entrada
    # ------------------------------------------------------------

    if not ruta_excel.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo de entrada: {ruta_excel}"
        )

    print("\nArchivo de entrada encontrado correctamente.")

    # ------------------------------------------------------------
    # Ejecutar pipeline
    # ------------------------------------------------------------

    print("\nEjecutando pipeline...")
    print("Esto puede tardar algunos minutos dependiendo de la cantidad de artículos.")

    resultados = ejecutar_pipeline_forecast(
        ruta_excel=ruta_excel,
        meses_evaluacion=6,
        meses_forecast_futuro=6,
        ventana_dummy=24,
        redondeo_evaluacion=None,
        redondeo_operativo="ceil",
        ruta_exportacion=ruta_exportacion
    ):
    # ------------------------------------------------------------
    # 1. Cargar dataframe original
    # ------------------------------------------------------------
    ##ruta_excel_matriz = "./Datos/df_matriz_ventas_articulos_forecast.xlsx"
    df = cargar_matriz_ventas(ruta_excel)

        # ------------------------------------------------------------
        # 2. Preparar formato forecast y metadata desde df original
        # ------------------------------------------------------------
        # Esta función toma el dataframe original en formato ancho:
        #
        # codigo_articulo | descripcion | venta_2024_01 | ... | venta_2026_07
        #
        # y genera:
        #
        # df_inferencia: unique_id | ds | y
        # df_metadata_articulos
        # metadata_por_articulo
        # mapa_fechas
        # columnas_venta
        # ------------------------------------------------------------

        (df_inferencia, df_metadata_articulos, metadata_por_articulo, mapa_fechas, columnas_venta) = preparar_formato_forecast_y_metadata(df_ventas=df, columna_codigo="codigo_articulo")

        # ------------------------------------------------------------
        # 3. Separar train/test temporal
        # ------------------------------------------------------------

        df_train, df_test, info_split = separar_train_test_df_inferencia(
            df_inferencia=df_inferencia,
            meses_evaluacion=meses_evaluacion,
            meses_entrenamiento=None
        )

        # ------------------------------------------------------------
        # 4. Generar df_eval_long
        # ------------------------------------------------------------
        # Este dataframe queda con formato:
        #
        # unique_id | ds | y | modelo | y_pred
        #
        # y sirve como input directo para calcular métricas.
        # ------------------------------------------------------------

        df_eval_long, df_eval_wide, columnas_modelos_evaluar = generar_df_eval_long(
            df_train=df_train,
            df_test=df_test,
            freq="ME",
            incluir_modelos_stats=True,
            incluir_dummy=True,
            ventana_dummy=ventana_dummy,
            redondeo=redondeo_evaluacion
        )

        # ------------------------------------------------------------
        # 5. Calcular métricas por artículo y modelo
        # ------------------------------------------------------------

        df_metricas = evaluando_metricas_por_articulo_modelo(
            df_eval_long
        )

        # ------------------------------------------------------------
        # 6. Seleccionar mejor modelo por artículo
        # ------------------------------------------------------------

        df_best_model = mejor_modelo_por_articulo(
            df_metricas
        )

        # ------------------------------------------------------------
        # 7. Enriquecer metadata con mejor modelo
        # ------------------------------------------------------------

        df_metadata_articulos = df_metadata_articulos.merge(
            df_best_model[
                [
                    "unique_id",
                    "best_model",
                    "WAPE_ranking",
                    "bias_total_abs_periodo_evaluacion",
                    "sesgo"
                ]
            ],
            on="unique_id",
            how="left",
            validate="one_to_one"
        )

        metadata_por_articulo = (
            df_metadata_articulos
            .set_index("unique_id")
            .to_dict(orient="index")
        )

        # ------------------------------------------------------------
        # 8. Construir dataframe visual
        # ------------------------------------------------------------

        df_forecast_visual, info_visual = construir_df_forecast_visualizacion(
            df_inferencia=df_inferencia,
            df_best_model=df_best_model[["unique_id", "best_model"]],
            meses_evaluacion=meses_evaluacion,
            meses_forecast_futuro=meses_forecast_futuro,
            freq="ME",
            redondeo=redondeo_operativo
        )

        # ------------------------------------------------------------
        # 9. Agregar forecast futuro y compra sugerida al df original
        # ------------------------------------------------------------

        df_resultado_final, df_forecast_wide, columnas_forecast = agregar_forecast_todos_los_articulos(
            df=df,
            df_forecast=df_forecast_visual,
            columna_codigo_df="codigo_articulo",
            columna_id_forecast="unique_id",
            columna_fecha="ds",
            columna_prediccion="y_pred",
            columna_periodo="periodo",
            valor_periodo_forecast="Forecast futuro",
            redondeo=redondeo_operativo
        )

        # ------------------------------------------------------------
        # 10. Exportar resultado final si se define ruta
        # ------------------------------------------------------------



        if ruta_exportacion is not None:
            print("exportando archivo")
            ruta_archivo_exportado = exportar_dataframe_excel(
                df_exportar=df_resultado_final,
                ruta_exportacion=ruta_exportacion,
                nombre_hoja="resultado_forecast",
                index=False
            )


        # #return {
        #     "df_original": df,
        #     "df_inferencia": df_inferencia,
        #     "df_train": df_train,
        #     "df_test": df_test,
        #     "df_eval_long": df_eval_long,
        #     "df_eval_wide": df_eval_wide,
        #     "df_metricas": df_metricas,
        #     "df_best_model": df_best_model,
        #     "df_metadata_articulos": df_metadata_articulos,
        #     "metadata_por_articulo": metadata_por_articulo,
        #     "df_forecast_visual": df_forecast_visual,
        #     "df_forecast_wide": df_forecast_wide,
        #     "df_resultado_final": df_resultado_final,
        #     "columnas_modelos_evaluar": columnas_modelos_evaluar,
        #     "columnas_forecast": columnas_forecast,
        #     "mapa_fechas": mapa_fechas,
        #     "columnas_venta": columnas_venta,
        #     "info_split": info_visual
        # }