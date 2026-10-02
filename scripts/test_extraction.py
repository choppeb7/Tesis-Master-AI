from pathlib import Path
import sys
import traceback


# ============================================================
# RUTAS DEL PROYECTO
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FORECAST_APP_DIR = PROJECT_ROOT / "forecast_app"

if str(FORECAST_APP_DIR) not in sys.path:
    sys.path.insert(0, str(FORECAST_APP_DIR))


from pipeline.data_preparation.connections import crear_engine_sqlserver
from pipeline.data_preparation.date_config import construir_configuracion_fechas
from pipeline.data_preparation.manufacturer_params import (
    cargar_fabricantes_parametrizados,
    obtener_fabricantes_considerados,
    construir_condicion_fabricantes_sql
)
from pipeline.data_preparation.sap_queries import construir_query_oitm_ventas
from pipeline.data_preparation.extraction import (
    extraer_oitm_ventas,
    validar_dataframe_extraido,
    mostrar_resumen_dataframe
)


def main():
    print("=" * 80)
    print("PRUEBA EXTRACCIÓN COMPLETA df_OITM_Ventas")
    print("=" * 80)

    try:
        # ============================================================
        # 1. Crear conexión
        # ============================================================

        engine = crear_engine_sqlserver()

        print("Conexión SQL Server creada ✅")

        # ============================================================
        # 2. Configurar fechas
        # ============================================================

        config_fechas = construir_configuracion_fechas(
            fecha_fin=None,
            fecha_inicio_visual="2024-01-01",
            meses_historico=24
        )

        print("\nConfiguración fechas:")
        print(config_fechas)

        # ============================================================
        # 3. Cargar fabricantes
        # ============================================================

        ruta_fabricantes = (
            FORECAST_APP_DIR
            / "data"
            / "input"
            / "fabricantes_repuestos_cerosa.xlsx"
        )

        df_fabricantes = cargar_fabricantes_parametrizados(
            ruta_fabricantes=ruta_fabricantes
        )

        fabricantes_considerados = obtener_fabricantes_considerados(
            df_fabricantes=df_fabricantes
        )

        condiciones_fabricantes, params_fabricantes = construir_condicion_fabricantes_sql(
            fabricantes_considerados=fabricantes_considerados
        )

        print("\nFabricantes considerados:", len(fabricantes_considerados))
        print("Primeros fabricantes:", fabricantes_considerados[:5])

        # ============================================================
        # 4. Construir query
        # ============================================================

        query_oitm_ventas, params_query = construir_query_oitm_ventas(
            config_fechas=config_fechas,
            condiciones_fabricantes=condiciones_fabricantes,
            params_fabricantes=params_fabricantes,
            bodegas_consideradas=["11", "14"],
            listas_precio=[11, 12, 13, 14],
            incluir_solo_stock_positivo=True
        )

        print("\nQuery construido correctamente ✅")
        print("Longitud query:", len(query_oitm_ventas))
        print("Cantidad parámetros:", len(params_query))

        print("\nPrimeros parámetros:")
        primeros_params = dict(list(params_query.items())[:10])
        print(primeros_params)

        # ============================================================
        # 5. Ejecutar extracción
        # ============================================================

        df_OITM_Ventas = extraer_oitm_ventas(
            engine=engine,
            query_oitm_ventas=query_oitm_ventas,
            params_query=params_query
        )

        # ============================================================
        # 6. Validar resultado
        # ============================================================

        columnas_minimas = [
            "codigo_articulo",
            "descripcion_completa",
            "marca_fabricante",
            "stock_en_mano",
            "total_unidades_vendidas_24m"
        ]

        validar_dataframe_extraido(
            df=df_OITM_Ventas,
            columnas_minimas=columnas_minimas,
            nombre_dataframe="df_OITM_Ventas"
        )

        mostrar_resumen_dataframe(
            df=df_OITM_Ventas,
            nombre_dataframe="df_OITM_Ventas",
            max_columnas=30
        )

        # ============================================================
        # 7. Exportar muestra para revisión
        # ============================================================

        output_dir = FORECAST_APP_DIR / "data" / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        ruta_salida = output_dir / "test_df_OITM_Ventas.xlsx"

        df_OITM_Ventas.head(1000).to_excel(
            ruta_salida,
            index=False
        )

        print("\nMuestra exportada correctamente ✅")
        print("Ruta:", ruta_salida)

        print("\nExtracción completa finalizada correctamente ✅")

    except Exception as error:
        print("\nError en prueba de extracción completa ❌")
        print(type(error).__name__)
        print(error)

        print("\nDetalle técnico:")
        traceback.print_exc()


if __name__ == "__main__":
    main()