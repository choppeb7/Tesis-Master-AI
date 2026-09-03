# ============================================================
# Ejecutar pipeline completo de forecast desde terminal
# ============================================================

from pathlib import Path
import argparse

from pipeline.main_pipeline import ejecutar_pipeline_forecast


def convertir_none(valor):
    """
    Convierte el texto 'none' en None real de Python.
    Útil para argumentos enviados desde terminal.
    """
    if valor is None:
        return None

    if str(valor).lower() == "none":
        return None

    return valor


def parse_args():
    parser = argparse.ArgumentParser(
        description="Ejecutar pipeline de forecast de artículos."
    )

    parser.add_argument(
        "--archivo-input",
        type=str,
        default="df_matriz_ventas_articulos_forecast.xlsx",
        help="Nombre del archivo Excel dentro de data/input."
    )

    parser.add_argument(
        "--archivo-output",
        type=str,
        default="resultado_forecast_compra_sugerida.xlsx",
        help="Nombre del archivo Excel que se guardará en data/output."
    )

    parser.add_argument(
        "--meses-evaluacion",
        type=int,
        default=6,
        help="Cantidad de meses usados para evaluar los modelos."
    )

    parser.add_argument(
        "--meses-forecast-futuro",
        type=int,
        default=6,
        help="Cantidad de meses futuros a pronosticar."
    )

    parser.add_argument(
        "--ventana-modelo-dummy",
        type=int,
        default=24,
        help="Cantidad de meses usados para calcular el promedio del modelo dummy."
    )

    parser.add_argument(
        "--redondeo-evaluacion",
        type=str,
        default="ceil",
        choices=["none", "ceil", "round"],
        help="Redondeo usado para evaluar modelos. Recomendado: none."
    )

    parser.add_argument(
        "--redondeo-operativo",
        type=str,
        default="ceil",
        choices=["none", "ceil", "round"],
        help="Redondeo usado para compra sugerida. Recomendado: ceil."
    )

    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 80)
    print("INICIANDO PIPELINE DE FORECAST")
    print("=" * 80)

    BASE_DIR = Path(__file__).resolve().parent

    ruta_excel = (
        BASE_DIR
        / "data"
        / "input"
        / args.archivo_input
    )

    ruta_exportacion = (
        BASE_DIR
        / "data"
        / "output"
        / args.archivo_output
    )

    redondeo_evaluacion = convertir_none(args.redondeo_evaluacion)
    redondeo_operativo = convertir_none(args.redondeo_operativo)

    print("\nParámetros de ejecución:")
    print(f"Archivo input: {ruta_excel}")
    print(f"Archivo output: {ruta_exportacion}")
    print(f"Meses evaluación: {args.meses_evaluacion}")
    print(f"Meses forecast futuro: {args.meses_forecast_futuro}")
    print(f"Ventana dummy: {args.ventana_modelo_dummy}")
    print(f"Redondeo evaluación: {redondeo_evaluacion}")
    print(f"Redondeo operativo: {redondeo_operativo}")

    if not ruta_excel.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo de entrada: {ruta_excel}"
        )

    resultados = ejecutar_pipeline_forecast(
        ruta_excel=ruta_excel,
        meses_evaluacion=args.meses_evaluacion,
        meses_forecast_futuro=args.meses_forecast_futuro,
        ventana_dummy=args.ventana_modelo_dummy,
        redondeo_evaluacion=redondeo_evaluacion,
        redondeo_operativo=redondeo_operativo,
        ruta_exportacion=ruta_exportacion
    )

    print("\nPipeline ejecutado correctamente.")
    print("=" * 80)

    print("\nDimensiones principales:")
    print("df_original:", resultados["df_original"].shape)
    print("df_inferencia:", resultados["df_inferencia"].shape)
    print("df_train:", resultados["df_train"].shape)
    print("df_test:", resultados["df_test"].shape)
    print("df_eval_long:", resultados["df_eval_long"].shape)
    print("df_metricas:", resultados["df_metricas"].shape)
    print("df_best_model:", resultados["df_best_model"].shape)
    print("df_forecast_visual:", resultados["df_forecast_visual"].shape)
    print("df_resultado_final:", resultados["df_resultado_final"].shape)

    print("\nColumnas forecast generadas:")
    print(resultados["columnas_forecast"])

    print("\nArchivo exportado en:")
    print(resultados["ruta_archivo_exportado"])

    print("\nResumen modelos ganadores:")
    print(resultados["df_best_model"]["best_model"].value_counts())

    print("\nProceso finalizado.")


if __name__ == "__main__":
    main()