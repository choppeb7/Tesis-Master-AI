from datetime import date, timedelta
import unicodedata


MESES_ES = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}


def normalizar_texto_sql(texto):
    """
    Normaliza texto para nombres de columnas SQL.

    Ejemplo:
    'Marzo' -> 'marzo'
    'Septiembre' -> 'septiembre'
    'Diciembre' -> 'diciembre'

    También elimina tildes por seguridad.
    """

    texto = str(texto).lower().strip()

    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")

    texto = texto.replace(" ", "_")

    return texto


def sumar_un_mes(fecha):
    """
    Suma un mes a una fecha tipo date, devolviendo siempre día 1.

    Ejemplo:
    2024-01-01 -> 2024-02-01
    2024-12-01 -> 2025-01-01
    """

    if fecha.month == 12:
        return date(fecha.year + 1, 1, 1)

    return date(fecha.year, fecha.month + 1, 1)


def obtener_fecha_fin_exclusiva_sql(config_fechas):
    """
    Obtiene la fecha fin exclusiva.

    La fecha fin exclusiva es el día siguiente a fecha_fin.
    Sirve para usar filtros SQL de este tipo:

    DocDate < fecha_fin_exclusiva

    Esto incluye todo el día fecha_fin, incluso si DocDate tiene hora.
    """

    if hasattr(config_fechas, "fecha_fin_exclusiva_sql"):
        return config_fechas.fecha_fin_exclusiva_sql

    fecha_fin_exclusiva = config_fechas.fecha_fin + timedelta(days=1)

    return fecha_fin_exclusiva.strftime("%Y-%m-%d")


def construir_columnas_ventas_sql(config_fechas):
    """
    Construye las columnas dinámicas de ventas por mes y año.

    Retorna:
    - columnas_ventas_sql:
        Fragmento usado dentro del CTE VentasPivot.

    - columnas_ventas_finales_sql:
        Fragmento usado en el SELECT final con ISNULL.

    - nombres_columnas_ventas:
        Lista con los nombres de columnas generadas.

    Ejemplo de columnas:
    - venta_enero_2024
    - venta_febrero_2024
    - venta_total_2024
    """

    fecha_inicio_visual = config_fechas.fecha_inicio_visual
    fecha_fin = config_fechas.fecha_fin

    fecha_fin_exclusiva = fecha_fin + timedelta(days=1)

    columnas_ventas_sql = []
    columnas_ventas_finales = []
    nombres_columnas_ventas = []

    anio_inicio = fecha_inicio_visual.year
    anio_fin = fecha_fin.year

    for anio in range(anio_inicio, anio_fin + 1):

        # ============================================================
        # Columnas mensuales
        # ============================================================

        for mes in range(1, 13):

            fecha_inicio_mes = date(anio, mes, 1)

            # No generar meses antes de la fecha de inicio visual
            if fecha_inicio_mes < date(
                fecha_inicio_visual.year,
                fecha_inicio_visual.month,
                1
            ):
                continue

            # No generar meses posteriores a fecha_fin
            if fecha_inicio_mes > date(fecha_fin.year, fecha_fin.month, 1):
                break

            fecha_fin_mes_exclusiva = sumar_un_mes(fecha_inicio_mes)

            if fecha_fin_mes_exclusiva > fecha_fin_exclusiva:
                fecha_fin_mes_exclusiva = fecha_fin_exclusiva

            nombre_mes = normalizar_texto_sql(MESES_ES[mes])
            nombre_columna = f"venta_{nombre_mes}_{anio}"

            columna_sql = f"""
        SUM(
            CASE
                WHEN DocDate >= '{fecha_inicio_mes.strftime("%Y-%m-%d")}'
                 AND DocDate <  '{fecha_fin_mes_exclusiva.strftime("%Y-%m-%d")}'
                THEN CantidadNeta
                ELSE 0
            END
        ) AS [{nombre_columna}]
            """

            columnas_ventas_sql.append(columna_sql)

            columnas_ventas_finales.append(
                f"ISNULL(VP.[{nombre_columna}], 0) AS [{nombre_columna}]"
            )

            nombres_columnas_ventas.append(nombre_columna)

        # ============================================================
        # Columna total anual
        # ============================================================

        fecha_inicio_anio = date(anio, 1, 1)

        if fecha_inicio_anio < fecha_inicio_visual:
            fecha_inicio_anio = fecha_inicio_visual

        fecha_fin_anio_exclusiva = date(anio + 1, 1, 1)

        if fecha_fin_anio_exclusiva > fecha_fin_exclusiva:
            fecha_fin_anio_exclusiva = fecha_fin_exclusiva

        nombre_columna_anual = f"venta_total_{anio}"

        columna_anual_sql = f"""
        SUM(
            CASE
                WHEN DocDate >= '{fecha_inicio_anio.strftime("%Y-%m-%d")}'
                 AND DocDate <  '{fecha_fin_anio_exclusiva.strftime("%Y-%m-%d")}'
                THEN CantidadNeta
                ELSE 0
            END
        ) AS [{nombre_columna_anual}]
        """

        columnas_ventas_sql.append(columna_anual_sql)

        columnas_ventas_finales.append(
            f"ISNULL(VP.[{nombre_columna_anual}], 0) AS [{nombre_columna_anual}]"
        )

        nombres_columnas_ventas.append(nombre_columna_anual)

    return {
        "columnas_ventas_sql": ",\n".join(columnas_ventas_sql),
        "columnas_ventas_finales_sql": ",\n    ".join(columnas_ventas_finales),
        "nombres_columnas_ventas": nombres_columnas_ventas,
    }


def construir_condicion_in_sql(
    columna_sql,
    valores,
    prefijo_parametro
):
    """
    Construye una condición SQL tipo IN usando parámetros nombrados.

    Ejemplo:
    columna_sql = "WhsCode"
    valores = ["11", "14"]
    prefijo_parametro = "bodega"

    Retorna:
    condicion_sql:
        WhsCode IN (:bodega_0, :bodega_1)

    params:
        {
            "bodega_0": "11",
            "bodega_1": "14"
        }
    """

    if valores is None or len(valores) == 0:
        raise ValueError(
            f"La lista de valores para {columna_sql} está vacía."
        )

    placeholders = []
    params = {}

    for indice, valor in enumerate(valores):
        nombre_parametro = f"{prefijo_parametro}_{indice}"
        placeholders.append(f":{nombre_parametro}")
        params[nombre_parametro] = valor

    condicion_sql = f"{columna_sql} IN ({', '.join(placeholders)})"

    return condicion_sql, params


def construir_condicion_bodegas_sql(
    bodegas_consideradas=None,
    columna_sql="WhsCode"
):
    """
    Construye condición dinámica para bodegas.

    Por defecto usa bodegas 11 y 14, que son las usadas en el notebook.
    """

    if bodegas_consideradas is None:
        bodegas_consideradas = ["11", "14"]

    return construir_condicion_in_sql(
        columna_sql=columna_sql,
        valores=bodegas_consideradas,
        prefijo_parametro="bodega"
    )


def construir_condicion_listas_precio_sql(
    listas_precio=None,
    columna_sql="TP.PriceList"
):
    """
    Construye condición dinámica para listas de precio.

    Por defecto usa listas 11, 12, 13 y 14.
    """

    if listas_precio is None:
        listas_precio = [11, 12, 13, 14]

    return construir_condicion_in_sql(
        columna_sql=columna_sql,
        valores=listas_precio,
        prefijo_parametro="lista_precio"
    )


def construir_filtro_stock_sql(
    incluir_solo_stock_positivo=True,
    columna_sql="OnHand"
):
    """
    Construye el filtro de stock positivo.

    Si incluir_solo_stock_positivo=True:
        AND OnHand > 0

    Si False:
        no agrega filtro.
    """

    if incluir_solo_stock_positivo:
        return f"AND {columna_sql} > 0"

    return ""


def construir_parametros_base_query(config_fechas):
    """
    Construye parámetros base de fechas para el query principal.

    Estos parámetros se usarán después en extraction.py junto con
    los parámetros de fabricantes, bodegas y listas de precio.
    """

    fecha_fin_exclusiva_sql = obtener_fecha_fin_exclusiva_sql(config_fechas)

    return {
        "fecha_inicio_visual_sql": config_fechas.fecha_inicio_visual_sql,
        "fecha_inicio_historico_sql": config_fechas.fecha_inicio_historico_sql,
        "fecha_fin_sql": config_fechas.fecha_fin_sql,
        "fecha_fin_exclusiva_sql": fecha_fin_exclusiva_sql,
        "periodo_meses_historico": config_fechas.periodo_meses_historico,
    }


def main():
    """
    Prueba directa del módulo sap_queries.py.

    Esta prueba valida:
    - generación de columnas mensuales/anuales de venta
    - condición dinámica de bodegas
    - condición dinámica de listas de precio
    - filtro de stock positivo
    """

    from pathlib import Path
    import sys

    project_root = Path(__file__).resolve().parents[3]
    forecast_app_dir = project_root / "forecast_app"

    if str(forecast_app_dir) not in sys.path:
        sys.path.insert(0, str(forecast_app_dir))

    from pipeline.data_preparation.date_config import construir_configuracion_fechas

    config_fechas = construir_configuracion_fechas(
        fecha_fin="2026-09-22",
        fecha_inicio_visual="2024-01-01",
        meses_historico=24
    )

    resultado_columnas = construir_columnas_ventas_sql(
        config_fechas=config_fechas
    )

    condicion_bodegas, params_bodegas = construir_condicion_bodegas_sql(
        bodegas_consideradas=["11", "14"]
    )

    condicion_listas, params_listas = construir_condicion_listas_precio_sql(
        listas_precio=[11, 12, 13, 14]
    )

    filtro_stock = construir_filtro_stock_sql(
        incluir_solo_stock_positivo=True
    )

    params_base = construir_parametros_base_query(
        config_fechas=config_fechas
    )

    print("=" * 80)
    print("PRUEBA SAP QUERIES")
    print("=" * 80)

    print("\nColumnas de venta generadas:")
    print(len(resultado_columnas["nombres_columnas_ventas"]))

    print("\nPrimeras 10 columnas:")
    for columna in resultado_columnas["nombres_columnas_ventas"][:10]:
        print("-", columna)

    print("\nÚltimas 10 columnas:")
    for columna in resultado_columnas["nombres_columnas_ventas"][-10:]:
        print("-", columna)

    print("\nFragmento columnas_ventas_sql:")
    print(resultado_columnas["columnas_ventas_sql"][:1000])

    print("\nFragmento columnas_ventas_finales_sql:")
    print(resultado_columnas["columnas_ventas_finales_sql"][:1000])

    print("\nCondición bodegas:")
    print(condicion_bodegas)
    print(params_bodegas)

    print("\nCondición listas de precio:")
    print(condicion_listas)
    print(params_listas)

    print("\nFiltro stock:")
    print(filtro_stock)

    print("\nParámetros base:")
    print(params_base)


if __name__ == "__main__":
    main()