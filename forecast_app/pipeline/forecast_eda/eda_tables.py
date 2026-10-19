from pathlib import Path
import sys
import pandas as pd


# ============================================================
# RUTAS DEL PROYECTO
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FORECAST_APP_DIR = PROJECT_ROOT / "forecast_app"

if str(FORECAST_APP_DIR) not in sys.path:
    sys.path.insert(0, str(FORECAST_APP_DIR))


# ============================================================
# CONFIGURACIÓN
# ============================================================

from pipeline.forecast_eda.eda_config import (
    RUTA_INPUT_FORECAST_FILTER,
    RUTA_OUTPUT_FORECAST_EDA,
    COLUMNAS_CONTEXTO_EDA,
    VARIABLES_BASE_DEMANDA,
    VARIABLES_CALCULADAS_EDA,
    MESES_HISTORICO_EDA,
    COLUMNA_FILTRO_SEGMENTO_FORECAST,
    VALOR_FILTRO_SEGMENTO_FORECAST
)


# ============================================================
# MÓDULOS DEL PIPELINE
# ============================================================

from pipeline.forecast_eda.eda_matrix_preparation import (
    preparar_base_y_matriz_eda
)

from pipeline.forecast_eda.eda_feature_engineering import (
    agregar_feature_engineering_a_dataframe,
    generar_resumen_variables_eda
)


# ============================================================
# VALIDACIÓN DE MATRIZ POR CÓDIGO DE ARTÍCULO
# ============================================================

def validar_salida_matriz_eda(
    df_eda,
    ventas_24m,
    columnas_venta_24m,
    columna_id="codigo_articulo"
):

    if df_eda.empty or ventas_24m.empty:
        raise ValueError("La base EDA o la matriz de ventas está vacía.")

    if columna_id not in df_eda.columns:
        raise ValueError(f"Falta la columna {columna_id} en df_eda.")

    if df_eda[columna_id].isna().any():
        raise ValueError("Existen códigos de artículo nulos.")

    if not df_eda[columna_id].is_unique:
        raise ValueError("Existen códigos duplicados en df_eda.")

    if ventas_24m.index.name != columna_id:
        raise ValueError(
            f"La matriz debe utilizar {columna_id} como índice."
        )

    if not ventas_24m.index.is_unique:
        raise ValueError("Existen códigos duplicados en ventas_24m.")

    codigos_base = set(df_eda[columna_id].astype(str))
    codigos_matriz = set(ventas_24m.index.astype(str))

    if codigos_base != codigos_matriz:
        raise ValueError(
            "Los artículos de df_eda no coinciden con los de ventas_24m."
        )

    if list(ventas_24m.columns) != list(columnas_venta_24m):
        raise ValueError(
            "Las columnas mensuales de la matriz no coinciden."
        )

    return True


# ============================================================
# FUNCIÓN PRINCIPAL DEL PIPELINE 03
# ============================================================

def ejecutar_forecast_eda(
    ruta_input=RUTA_INPUT_FORECAST_FILTER,
    ruta_output=RUTA_OUTPUT_FORECAST_EDA,
    columna_filtro=COLUMNA_FILTRO_SEGMENTO_FORECAST,
    valor_filtro=VALOR_FILTRO_SEGMENTO_FORECAST,
    columnas_contexto=COLUMNAS_CONTEXTO_EDA,
    meses_historico=MESES_HISTORICO_EDA,
    columna_id="codigo_articulo",
    exportar_excel=True,
    exportar_validacion=True
):

    ruta_input = Path(ruta_input)
    ruta_output = Path(ruta_output)

    print("\n" + "=" * 80)
    print("PIPELINE 03 - FORECAST EDA")
    print("=" * 80)

    # ========================================================
    # 1. CARGA DE DATOS
    # ========================================================

    if not ruta_input.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo: {ruta_input}"
        )

    df = pd.read_excel(
        ruta_input,
        dtype={columna_id: str}
    )

    print(f"\nArchivo cargado: {ruta_input.name}")
    print(f"Artículos de entrada: {len(df)}")

    # Conservar también las variables base de demanda
    columnas_contexto_eda = list(dict.fromkeys(
        list(columnas_contexto) + VARIABLES_BASE_DEMANDA
    ))

    variables_base_faltantes = [
        columna
        for columna in VARIABLES_BASE_DEMANDA
        if columna not in df.columns
    ]

    if variables_base_faltantes:
        print(
            "\nADVERTENCIA - Variables base no disponibles:",
            variables_base_faltantes
        )

    # ========================================================
    # 2. MATRIX PREPARATION
    # ========================================================

    print("\n[1/2] Preparando matriz EDA...")

    df_eda_base, ventas_24m, columnas_venta_24m = (
        preparar_base_y_matriz_eda(
            df=df,
            columna_filtro=columna_filtro,
            valor_filtro=valor_filtro,
            meses_historico=meses_historico,
            columna_id=columna_id,
            columnas_contexto=columnas_contexto_eda,
            incluir_columnas_venta_en_df_eda=True,
            ignorar_columnas_faltantes=True
        )
    )

    validar_salida_matriz_eda(
        df_eda=df_eda_base,
        ventas_24m=ventas_24m,
        columnas_venta_24m=columnas_venta_24m,
        columna_id=columna_id
    )

    if len(columnas_venta_24m) != meses_historico:
        raise ValueError(
            f"Se esperaban {meses_historico} meses de ventas, "
            f"pero se detectaron {len(columnas_venta_24m)}."
        )

    print("Matriz validada correctamente.")
    print(f"Artículos seleccionados: {len(df_eda_base)}")
    print(f"Meses analizados: {len(columnas_venta_24m)}")

    # ========================================================
    # 3. FEATURE ENGINEERING
    # ========================================================

    print("\n[2/2] Calculando variables matemáticas EDA...")

    df_eda_features = agregar_feature_engineering_a_dataframe(
        df_eda=df_eda_base,
        ventas_24m=ventas_24m,
        columna_id=columna_id
    )

    variables_faltantes = [
        variable
        for variable in VARIABLES_CALCULADAS_EDA
        if variable not in df_eda_features.columns
    ]

    if variables_faltantes:
        raise ValueError(
            "No se generaron las siguientes variables EDA: "
            + ", ".join(variables_faltantes)
        )

    if len(df_eda_features) != len(df_eda_base):
        raise ValueError(
            "El Feature Engineering modificó la cantidad de artículos."
        )

    if (
        set(df_eda_features[columna_id].astype(str))
        != set(df_eda_base[columna_id].astype(str))
    ):
        raise ValueError(
            "El Feature Engineering modificó los códigos de artículo."
        )

    resumen_variables = generar_resumen_variables_eda(
        df_eda=df_eda_features
    )

    print("Feature Engineering finalizado correctamente.")
    print(
        "Variables calculadas:",
        resumen_variables["cantidad_variables_calculadas"]
    )

    # ========================================================
    # 4. RESULTADO ACTUAL
    # ========================================================
    # Próximamente:
    #
    # df_eda_final = aplicar_clasificaciones_eda(
    #     df_eda=df_eda_features
    # )
    #
    # Por ahora, el resultado final es Feature Engineering.
    # ========================================================

    df_eda_final = df_eda_features

    # ========================================================
    # 5. EXPORTACIÓN OFICIAL
    # ========================================================

    if exportar_excel:

        ruta_output.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        df_eda_final.to_excel(
            ruta_output,
            index=False
        )

        print(f"\nArchivo oficial exportado: {ruta_output}")

    # ========================================================
    # 6. EXPORTACIÓN DE VALIDACIÓN
    # ========================================================

    if exportar_validacion:

        ruta_validacion = (
            ruta_output.parent
            / "validacion_03_forecast_eda.xlsx"
        )

        with pd.ExcelWriter(
            ruta_validacion,
            engine="openpyxl"
        ) as writer:

            df_eda_base.head(100).to_excel(
                writer,
                sheet_name="eda_base",
                index=False
            )

            ventas_24m.head(100).reset_index().to_excel(
                writer,
                sheet_name="matriz_ventas",
                index=False
            )

            df_eda_final.head(100).to_excel(
                writer,
                sheet_name="feature_engineering",
                index=False
            )

            pd.DataFrame({
                "variable": VARIABLES_CALCULADAS_EDA,
                "presente": [
                    variable in df_eda_final.columns
                    for variable in VARIABLES_CALCULADAS_EDA
                ]
            }).to_excel(
                writer,
                sheet_name="validacion_variables",
                index=False
            )

        print(f"Archivo de validación: {ruta_validacion}")

    print("\nPIPELINE 03 FINALIZADO CORRECTAMENTE")

    return df_eda_final, ventas_24m, columnas_venta_24m


# ============================================================
# PUNTO DE ENTRADA
# ============================================================

def main():

    ejecutar_forecast_eda(
        exportar_excel=True,
        exportar_validacion=True
    )


if __name__ == "__main__":
    main()