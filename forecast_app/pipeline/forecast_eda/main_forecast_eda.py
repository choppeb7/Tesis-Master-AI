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
from pipeline.forecast_eda.eda_feature_engineering import (
    agregar_feature_engineering_a_dataframe,
    generar_resumen_variables_eda
)
from pipeline.forecast_eda.eda_config import (
    RUTA_INPUT_FORECAST_FILTER,
    RUTA_OUTPUT_FORECAST_EDA,
    COLUMNAS_CONTEXTO_EDA,
    MESES_HISTORICO_EDA,
    COLUMNA_FILTRO_SEGMENTO_FORECAST,
    VALOR_FILTRO_SEGMENTO_FORECAST,
    VARIABLES_CALCULADAS_EDA
)

from pipeline.forecast_eda.eda_matrix_preparation import (
    preparar_base_y_matriz_eda
)
from pipeline.forecast_eda.eda_classification_rules import (
    aplicar_clasificaciones_eda,
    validar_columnas_clasificacion_generadas,
    generar_resumen_clasificaciones_eda,
    generar_resumen_cruzado_clasificaciones,
    generar_resumen_clasificaciones_por_columna
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

def ejecutar_eda(
    ruta_input=RUTA_INPUT_FORECAST_FILTER,
    ruta_output=RUTA_OUTPUT_FORECAST_EDA,
    columna_filtro=COLUMNA_FILTRO_SEGMENTO_FORECAST,
    valor_filtro=VALOR_FILTRO_SEGMENTO_FORECAST,
    columnas_contexto=COLUMNAS_CONTEXTO_EDA,
    meses_historico=MESES_HISTORICO_EDA,
    exportar_muestra=True,
    columna_id="codigo_articulo",
    exportar_excel=True,
    exportar_validacion=True
):
    """
    Ejecuta una validación inicial del pipeline 03.

    Esta función todavía no calcula variables EDA.
    Su objetivo es probar que preparar_base_y_matriz_eda funciona correctamente.

    Flujo:
    1. Lee el archivo generado por pipeline 02.
    2. Filtra artículos según columna_filtro y valor_filtro.
    3. Detecta columnas mensuales de venta.
    4. Prepara la matriz de ventas de los últimos N meses.
    5. Valida consistencia entre df_eda y ventas_24m.
    6. Exporta una muestra opcional para revisión manual.
    """

    print("=" * 100)
    print("PIPELINE 03 - FORECAST EDA")
    print("=" * 100)

    # ========================================================
    # 1. CARGA DE DATOS
    # ========================================================
    ruta_input = Path(ruta_input)
    ruta_output = Path(ruta_output)

    print("\nArchivo input:")
    print(ruta_input)

    print("\nFiltro aplicado:")
    print(f"{columna_filtro} == {valor_filtro}")

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

    if columna_filtro not in df.columns:
        raise ValueError(
            f"La columna de filtro '{columna_filtro}' no existe en el archivo input."
        )

    print("\nDistribución de la columna de filtro antes de filtrar:")
    print(df[columna_filtro].value_counts(dropna=False).head(20))

    # ============================================================
    # 2. Preparar base y matriz EDA
    # ============================================================

    print("\nPreparando base EDA y matriz de ventas...")

    df_eda_base, ventas_24m, columnas_venta_24m = preparar_base_y_matriz_eda(
        df=df,
        meses_historico=meses_historico,
        columna_filtro=columna_filtro,
        valor_filtro=valor_filtro,
        columnas_contexto=columnas_contexto,
        incluir_columnas_venta_en_df_eda=True,
        ignorar_columnas_faltantes=True
    )

    print("Preparación ejecutada correctamente ✅")

    # ============================================================
    # 3. Validar resultados despues de la preparación
    # ============================================================

    validar_salida_matriz_eda(
        df_eda=df_eda_base,
        ventas_24m=ventas_24m,
        columnas_venta_24m=columnas_venta_24m,
        columna_id=columna_id
    )

    print("Validación estructural correcta ✅")

    # ============================================================
    #  Mostrar resumen
    # ============================================================

    print("\nResumen df_eda:")
    print("Filas df_eda:", df_eda_base.shape[0])
    print("Columnas df_eda:", df_eda_base.shape[1])

    print("\nResumen matriz ventas_24m:")
    print("Filas ventas_24m:", ventas_24m.shape[0])
    print("Columnas ventas_24m:", ventas_24m.shape[1])

    print("\nColumnas de venta detectadas:")
    print("Cantidad:", len(columnas_venta_24m))
    print("Primera columna:", columnas_venta_24m[0])
    print("Última columna:", columnas_venta_24m[-1])

    print("\nPrimeras columnas de df_eda:")
    print(df_eda_base.columns.tolist()[:30])

    print("\nColumnas de contexto solicitadas que sí quedaron en df_eda:")
    columnas_contexto_presentes = [
        columna for columna in columnas_contexto
        if columna in df_eda_base.columns
    ]
    print(columnas_contexto_presentes)

    print("\nColumnas de contexto solicitadas que no existen en df_eda:")
    columnas_contexto_faltantes = [
        columna for columna in columnas_contexto
        if columna not in df_eda_base.columns
    ]
    print(columnas_contexto_faltantes)

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
        if columna in df_eda_base.columns
    ]

    print(df_eda_base[columnas_vista].head())

    print("\nVista rápida ventas_24m:")
    print(ventas_24m.head())

    # ========================================================
    # 3. FEATURE ENGINEERING
    # ========================================================

    print("\n[2/2] Calculando variables matemáticas EDA...")

    df_eda_features = agregar_feature_engineering_a_dataframe(
        df_eda=df_eda_base,
        ventas_24m=ventas_24m,
        columna_id=columna_id
    )

    resumen_variables = generar_resumen_variables_eda(
        df_eda=df_eda_features
    )
    df_resumen_variables = pd.DataFrame([resumen_variables])

    print("Feature Engineering ejecutado correctamente ✅")

    print(
        "Cantidad de variables calculadas:",
        resumen_variables["cantidad_variables_calculadas"]
    )

    print(
        "Cantidad de artículos:",
        resumen_variables["cantidad_articulos"]
    )

    

    
    # ========================================================
    # 5. Aplicar reglas de clasificación EDA 
    # ========================================================
    df_eda_final = aplicar_clasificaciones_eda(df_eda=df_eda_features).copy()
    

    # ========================================================
    # 6. EXPORTACIÓN OFICIAL
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
    # 7. EXPORTACIÓN DE VALIDACIÓN
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

            df_eda_base.to_excel(
                writer,
                sheet_name="eda_base",
                index=False
            )

            ventas_24m.reset_index().to_excel(
                writer,
                sheet_name="matriz_ventas",
                index=False
            )

            df_eda_final.to_excel(
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


def main():
    """
    Ejecuta validación inicial del pipeline 03.
    """

    ejecutar_eda(
        ruta_input=RUTA_INPUT_FORECAST_FILTER,
        ruta_output=RUTA_OUTPUT_FORECAST_EDA,
        columna_filtro=COLUMNA_FILTRO_SEGMENTO_FORECAST,
        valor_filtro=VALOR_FILTRO_SEGMENTO_FORECAST,
        columnas_contexto=COLUMNAS_CONTEXTO_EDA,
        meses_historico=MESES_HISTORICO_EDA,
        exportar_muestra=True,
        columna_id="codigo_articulo",
        exportar_excel=True,
        exportar_validacion=True
    )


if __name__ == "__main__":
    main()