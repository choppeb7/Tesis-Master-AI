from pathlib import Path
import pandas as pd
import sys
# ============================================================
# AJUSTE DE RUTA PARA PODER IMPORTAR pipeline
# ============================================================

FORECAST_APP_DIR = Path(__file__).resolve().parents[2]

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
from pipeline.data_preparation.commercial_rules import (
    aplicar_reglas_comerciales,
    mostrar_resumen_reglas_comerciales
)
from pipeline.data_preparation.inventory_rules import (
    aplicar_reglas_inventario,
    mostrar_resumen_reglas_inventario
)

from utils.reporting import guardar_grafico_barras_conteo, asegurar_directorio, limpiar_nombre_archivo, guardar_grafico_pastel_conteo, guardar_tabla_resumen_segmento

def resolver_ruta_fabricantes(ruta_fabricantes=None):
    """
    Resuelve la ruta del archivo de fabricantes.

    Si no se proporciona ruta, usa por defecto:

        forecast_app/data/input/fabricantes_repuestos_cerosa.xlsx
    """

    if ruta_fabricantes is not None:
        return Path(ruta_fabricantes)

    project_root = Path(__file__).resolve().parents[3]

    return (
        project_root
        / "forecast_app"
        / "data"
        / "input"
        / "fabricantes_repuestos_cerosa.xlsx"
    )


def resolver_directorio_output(directorio_output=None):
    """
    Resuelve la carpeta de salida.

    Si no se proporciona ruta, usa:

        forecast_app/data/output
    """

    if directorio_output is not None:
        return Path(directorio_output)

    project_root = Path(__file__).resolve().parents[3]

    return (
        project_root
        / "forecast_app"
        / "data"
        / "output"
    )

def resolver_directorio_figuras(directorio_figuras=None):
    if directorio_figuras is not None:
        return Path(directorio_figuras)

    project_root = Path(__file__).resolve().parents[3]

    return (
        project_root
        / "forecast_app"
        / "reports"
        / "figures"
        / "01_data_preprocesada"
    )

def ejecutar_preparacion_datos(
    ruta_fabricantes=None,
    directorio_output=None,
    nombre_archivo_salida="df_OITM_Ventas_preparado.xlsx",
    fecha_fin=None,
    fecha_inicio_visual="2024-01-01",
    meses_historico=24,
    bodegas_consideradas=None,
    listas_precio=None,
    incluir_solo_stock_positivo=True,
    #margen_bruto_objetivo=0.30,
    factor_seguridad_meses=0.5,
    umbral_revision_compra_meses=2,
    exportar_excel=True
):
    """
    Ejecuta el pipeline completo de preparación de datos.

    Flujo:
    1. Crear conexión SQL Server.
    2. Construir configuración de fechas.
    3. Cargar fabricantes parametrizados.
    4. Construir query SAP.
    5. Extraer df_OITM_Ventas.
    6. Aplicar reglas comerciales.
    7. Aplicar reglas de inventario.
    8. Exportar resultado final.
    """

    print("=" * 100)
    print("INICIO PIPELINE DATA PREPARATION")
    print("=" * 100)

    # ============================================================
    # 1. Rutas
    # ============================================================

    ruta_fabricantes = resolver_ruta_fabricantes(ruta_fabricantes)
    directorio_output = resolver_directorio_output(directorio_output)

    directorio_output.mkdir(parents=True, exist_ok=True)

    ruta_salida = directorio_output / nombre_archivo_salida

    print("\nRuta fabricantes:")
    print(ruta_fabricantes)

    print("\nDirectorio output:")
    print(directorio_output)

    # ============================================================
    # 2. Parámetros por defecto
    # ============================================================

    if bodegas_consideradas is None:
        bodegas_consideradas = ["11", "14"]

    if listas_precio is None:
        listas_precio = [11, 12, 13, 14]

    # ============================================================
    # 3. Conexión SQL Server
    # ============================================================

    print("\nCreando conexión SQL Server...")

    engine = crear_engine_sqlserver()

    print("Conexión SQL Server creada ✅")

    # ============================================================
    # 4. Configuración de fechas
    # ============================================================

    print("\nConstruyendo configuración de fechas...")

    config_fechas = construir_configuracion_fechas(
        fecha_fin=fecha_fin,
        fecha_inicio_visual=fecha_inicio_visual,
        meses_historico=meses_historico
    )

    print(config_fechas)

    # ============================================================
    # 5. Fabricantes
    # ============================================================

    print("\nCargando fabricantes parametrizados...")

    df_fabricantes = cargar_fabricantes_parametrizados(
        ruta_fabricantes=ruta_fabricantes
    )

    fabricantes_considerados = obtener_fabricantes_considerados(
        df_fabricantes=df_fabricantes
    )

    condiciones_fabricantes, params_fabricantes = construir_condicion_fabricantes_sql(
        fabricantes_considerados=fabricantes_considerados
    )

    print("Fabricantes considerados:", len(fabricantes_considerados))
    print("Primeros fabricantes:", fabricantes_considerados[:10])

    # ============================================================
    # 6. Construir query SAP
    # ============================================================

    print("\nConstruyendo query df_OITM_Ventas...")

    query_oitm_ventas, params_query = construir_query_oitm_ventas(
        config_fechas=config_fechas,
        condiciones_fabricantes=condiciones_fabricantes,
        params_fabricantes=params_fabricantes,
        bodegas_consideradas=bodegas_consideradas,
        listas_precio=listas_precio,
        incluir_solo_stock_positivo=incluir_solo_stock_positivo
    )

    print("Query construido correctamente ✅")
    print("Cantidad parámetros:", len(params_query))

    # ============================================================
    # 7. Extraer datos
    # ============================================================

    print("\nExtrayendo df_OITM_Ventas desde SAP...")

    df_oitm_ventas = extraer_oitm_ventas(
        engine=engine,
        query_oitm_ventas=query_oitm_ventas,
        params_query=params_query
    )

    validar_dataframe_extraido(
        df=df_oitm_ventas,
        columnas_minimas=[
            "codigo_articulo",
            "descripcion_completa",
            "marca_fabricante",
            "stock_en_mano",
            "total_unidades_vendidas_24m"
        ],
        nombre_dataframe="df_oitm_ventas"
    )

    mostrar_resumen_dataframe(
        df=df_oitm_ventas,
        nombre_dataframe="df_oitm_ventas",
        max_columnas=30
    )

    # ============================================================
    # 8. Reglas comerciales
    # ============================================================

    print("\nAplicando reglas comerciales...")

    df_commercial = aplicar_reglas_comerciales(
        df=df_oitm_ventas,
        config_fechas=config_fechas,
        meses_historico=meses_historico,
        #margen_bruto_objetivo=margen_bruto_objetivo
    )

    mostrar_resumen_reglas_comerciales(df_commercial)

    # ============================================================
    # 9. Reglas de inventario
    # ============================================================

    print("\nAplicando reglas de inventario...")

    df_final = aplicar_reglas_inventario(
        df=df_commercial,
        ruta_fabricantes=ruta_fabricantes,
        df_fabricantes=df_fabricantes,
        fecha_fin=config_fechas.fecha_fin,
        meses_historico=meses_historico,
        factor_seguridad_meses=factor_seguridad_meses,
        umbral_revision_compra_meses=umbral_revision_compra_meses
    )

    mostrar_resumen_reglas_inventario(df_final)

    # ============================================================
    # 10. Exportar resultado
    # ============================================================

    if exportar_excel:
        print("\nExportando resultado final...")

        df_final.to_excel(
            ruta_salida,
            index=False
        )

        print("Archivo exportado correctamente ✅")
        print("Ruta salida:", ruta_salida)

    print("\n" + "=" * 100)
    print("PIPELINE DATA PREPARATION FINALIZADO ✅")
    print("=" * 100)

    #============================================================
    #11. Exportar imagenes y tablas resumen 
    #============================================================

    directorio_figuras = resolver_directorio_figuras()
    directorio_figuras = Path(directorio_figuras)
    rutas_graficas = []
    print(f"Directorio de figuras para graficas resumen data preprocesada: {directorio_figuras}")

    rutas_graficas.append(guardar_grafico_barras_conteo(
        df=df_final,
        columna="criticidad_comercial",
        directorio_salida=directorio_figuras,
        titulo="Conteo de artículos por criticidad comercial",
        nombre_archivo="01_grafico_barras_criticidad_comercial.png"
    ))
    print(f"Gráfico de barras exportado correctamente ✅ Ruta: {rutas_graficas[-1]}")

    rutas_graficas.append(guardar_grafico_barras_conteo(
            df=df_final,
            columna="meses_con_venta_24m",
            directorio_salida=directorio_figuras,
            titulo="Conteo de artículos por meses con venta (24m)",
            nombre_archivo="02_grafico_barras_meses_con_venta_24m.png"
        ))
    print(f"Gráfico de barras exportado correctamente ✅ Ruta: {rutas_graficas[-1]}")


    return df_final


def main():
    """
    Prueba directa del pipeline completo.
    """

    df_final = ejecutar_preparacion_datos(
        fecha_fin=None,
        fecha_inicio_visual="2024-01-01",
        meses_historico=24,
        bodegas_consideradas=["11", "14"],
        listas_precio=[11, 12, 13, 14],
        incluir_solo_stock_positivo=True,
        #margen_bruto_objetivo=0.30,
        factor_seguridad_meses=0.5,
        umbral_revision_compra_meses=2,
        exportar_excel=True
    )

    print("\nVista rápida final:")
    print(df_final.head())


if __name__ == "__main__":
    main()