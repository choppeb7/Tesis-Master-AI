from pathlib import Path
import sys
import pandas as pd


# ============================================================
# AJUSTE DE RUTA PARA IMPORTAR forecast_app
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FORECAST_APP_DIR = PROJECT_ROOT / "forecast_app"

if str(FORECAST_APP_DIR) not in sys.path:
    sys.path.insert(0, str(FORECAST_APP_DIR))


# ============================================================
# IMPORTS DEL PIPELINE 03
# ============================================================

from pipeline.forecast_eda.eda_config import (
    RUTA_INPUT_FORECAST_FILTER,
    RUTA_OUTPUT_EDA,
    COLUMNAS_CONTEXTO_EDA,
    MESES_HISTORICO_EDA
)

from pipeline.forecast_eda.eda_matrix_preparation import (
    preparar_base_y_matriz_eda
)


# ============================================================
# VALIDACIÓN DE PREPARACIÓN BASE Y MATRIZ
# ============================================================

def validar_salida_preparacion_eda(
    df_eda,
    ventas_24m,
    columnas_venta_24m
):
    """
    Valida que la función preparar_base_y_matriz_eda haya generado
    resultados consistentes.
    """

    errores = []

    if df_eda.empty:
        errores.append("df_eda está vacío.")

    if ventas_24m.empty:
        errores.append("ventas_24m está vacío.")

    if len(columnas_venta_24m) == 0:
        errores.append("No se detectaron columnas de venta mensual.")

    if df_eda.shape[0] != ventas_24m.shape[0]:
        errores.append(
            "La cantidad de filas de df_eda no coincide con la matriz ventas_24m."
        )

    if ventas_24m.shape[1] != len(columnas_venta_24m):
        errores.append(
            "La cantidad de columnas de ventas_24m no coincide con columnas_venta_24m."
        )

    columnas_minimas = [
        "codigo_articulo",
        "descripcion_completa"
    ]

    for columna in columnas_minimas:
        if columna not in df_eda.columns:
            errores.append(f"Falta columna mínima en df_eda: {columna}")

    if errores:
        mensaje_error = "\n".join(errores)
        raise ValueError(
            "Errores detectados en la preparación EDA:\n"
            + mensaje_error
        )

    return True


def ejecutar_validacion_preparacion_base_matriz(
    ruta_input=RUTA_INPUT_FORECAST_FILTER,
    exportar_muestra=True
):
    """
    Ejecuta una validación inicial del pipeline 03.

    Esta función todavía no calcula variables EDA.
    Su objetivo es probar que preparar_base_y_matriz_eda funciona correctamente.

    Flujo:
    1. Lee el archivo generado por pipeline 02.
    2. Filtra artículos con aplica_forecast_automatico == True.
    3. Detecta columnas mensuales de venta.
    4. Prepara la matriz de ventas de los últimos 24 meses.
    5. Valida consistencia entre df_eda y ventas_24m.
    6. Exporta una muestra opcional para revisión manual.
    """

    print("=" * 100)
    print("PIPELINE 03 - VALIDACIÓN PREPARACIÓN BASE Y MATRIZ EDA")
    print("=" * 100)

    ruta_input = Path(ruta_input)

    print("\nArchivo input:")
    print(ruta_input)

    if not ruta_input.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo input: {ruta_input}"
        )

    # ============================================================
    # 1. Leer archivo del pipeline 02
    # ============================================================

    print("\nLeyendo archivo forecast filter...")

    df = pd.read_excel(ruta_input)

    print("Archivo leído correctamente ✅")
    print("Filas input:", df.shape[0])
    print("Columnas input:", df.shape[1])

    # ============================================================
    # 2. Preparar base y matriz EDA
    # ============================================================

    print("\nPreparando base EDA y matriz de ventas...")

    df_eda, ventas_24m, columnas_venta_24m = preparar_base_y_matriz_eda(
        df=df,
        meses_historico=MESES_HISTORICO_EDA,
        columnas_contexto=COLUMNAS_CONTEXTO_EDA,
        incluir_columnas_venta_en_df_eda=True,
        ignorar_columnas_faltantes=True
    )

    print("Preparación ejecutada correctamente ✅")

    # ============================================================
    # 3. Validar resultados
    # ============================================================

    validar_salida_preparacion_eda(
        df_eda=df_eda,
        ventas_24m=ventas_24m,
        columnas_venta_24m=columnas_venta_24m
    )

    print("Validación estructural correcta ✅")

    # ============================================================
    # 4. Mostrar resumen
    # ============================================================

    print("\nResumen df_eda:")
    print("Filas df_eda:", df_eda.shape[0])
    print("Columnas df_eda:", df_eda.shape[1])

    print("\nResumen matriz ventas_24m:")
    print("Filas ventas_24m:", ventas_24m.shape[0])
    print("Columnas ventas_24m:", ventas_24m.shape[1])

    print("\nColumnas de venta detectadas:")
    print("Cantidad:", len(columnas_venta_24m))
    print("Primera columna:", columnas_venta_24m[0])
    print("Última columna:", columnas_venta_24m[-1])

    print("\nPrimeras columnas de df_eda:")
    print(df_eda.columns.tolist()[:20])

    print("\nVista rápida df_eda:")
    columnas_vista = [
        columna for columna in [
            "codigo_articulo",
            "descripcion_completa",
            "marca_fabricante",
            "tipo_abastecimiento",
            "criticidad_comercial",
            "segmento_forecast",
            "aplica_forecast_automatico"
        ]
        if columna in df_eda.columns
    ]

    print(df_eda[columnas_vista].head())

    print("\nVista rápida ventas_24m:")
    print(ventas_24m.head())

    # ============================================================
    # 5. Exportar muestra de validación
    # ============================================================

    if exportar_muestra:
        ruta_muestra = (
            RUTA_OUTPUT_EDA.parent
            / "validacion_03_preparacion_base_matriz_eda.xlsx"
        )

        with pd.ExcelWriter(ruta_muestra, engine="openpyxl") as writer:
            df_eda.head(100).to_excel(
                writer,
                sheet_name="muestra_df_eda",
                index=False
            )

            ventas_24m.head(100).to_excel(
                writer,
                sheet_name="muestra_ventas_24m",
                index=False
            )

            pd.DataFrame(
                {
                    "columnas_venta_24m": columnas_venta_24m
                }
            ).to_excel(
                writer,
                sheet_name="columnas_venta",
                index=False
            )

        print("\nMuestra de validación exportada ✅")
        print(ruta_muestra)

    print("\n" + "=" * 100)
    print("VALIDACIÓN DE PREPARACIÓN BASE Y MATRIZ FINALIZADA ✅")
    print("=" * 100)

    return df_eda, ventas_24m, columnas_venta_24m


def main():
    """
    Ejecuta validación inicial del pipeline 03.
    """

    ejecutar_validacion_preparacion_base_matriz(
        exportar_muestra=True
    )


if __name__ == "__main__":
    main()