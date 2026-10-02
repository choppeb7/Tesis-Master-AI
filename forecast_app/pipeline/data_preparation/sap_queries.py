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
        AND OnHand >= 0

    Si False:
        no agrega filtro.
    """

    if incluir_solo_stock_positivo:
        return f"AND {columna_sql} >= 0"

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
def construir_query_oitm_ventas(
    config_fechas,
    condiciones_fabricantes,
    params_fabricantes,
    bodegas_consideradas=None,
    listas_precio=None,
    incluir_solo_stock_positivo=True
):
    """
    Construye el query principal de extracción de artículos, ventas,
    compras, inventario, precios, clientes y vendedores.

    Retorna:
    - query_oitm_ventas
    - params_query
    """

    # ============================================================
    # 1. Columnas dinámicas de ventas
    # ============================================================

    resultado_columnas = construir_columnas_ventas_sql(
        config_fechas=config_fechas
    )

    columnas_ventas_sql = resultado_columnas["columnas_ventas_sql"]
    columnas_ventas_finales_sql = resultado_columnas["columnas_ventas_finales_sql"]

    # ============================================================
    # 2. Fechas principales
    # ============================================================

    fecha_inicio_visual_sql = config_fechas.fecha_inicio_visual_sql
    fecha_inicio_historico_sql = config_fechas.fecha_inicio_historico_sql
    fecha_fin_exclusiva_sql = obtener_fecha_fin_exclusiva_sql(config_fechas)
    periodo_meses_historico = config_fechas.periodo_meses_historico

    # ============================================================
    # 3. Condición dinámica de bodegas
    # ============================================================

    condicion_bodegas, params_bodegas = construir_condicion_bodegas_sql(
        bodegas_consideradas=bodegas_consideradas,
        columna_sql="WhsCode"
    )

    # ============================================================
    # 4. Condición dinámica de listas de precio
    # ============================================================

    condicion_listas_precio, params_listas_precio = construir_condicion_listas_precio_sql(
        listas_precio=listas_precio,
        columna_sql="TP.PriceList"
    )

    # ============================================================
    # 5. Filtro dinámico de stock
    # ============================================================

    filtro_stock_sql = construir_filtro_stock_sql(
        incluir_solo_stock_positivo=incluir_solo_stock_positivo,
        columna_sql="OnHand"
    )

    # ============================================================
    # 6. Query principal
    # ============================================================
    # Aquí debes pegar el Query_OITM_Ventas de tu notebook.
    #
    # Reemplazos importantes:
    #
    # 1. Donde antes tenías:
    #    DATEADD(DAY, 1, CAST(GETDATE() AS date))
    #
    #    usa:
    #    '{fecha_fin_exclusiva_sql}'
    #
    # 2. Donde antes tenías:
    #    WhsCode IN ('11', '14')
    #
    #    usa:
    #    {condicion_bodegas}
    #
    # 3. Donde antes tenías:
    #    TP.PriceList IN (11, 12, 13, 14)
    #
    #    usa:
    #    {condicion_listas_precio}
    #
    # 4. Donde antes tenías:
    #    OnHand > 0
    #
    #    usa:
    #    {filtro_stock_sql}
    #
    # 5. Donde antes tenías:
    #    {condiciones_fabricantes}
    #
    #    déjalo igual porque viene desde manufacturer_params.py.

    query_oitm_ventas = f"""
    WITH VentasBase AS (

    /*=====================================================
       FACTURAS DE VENTA
    ===================================================== */

    SELECT
        L.ItemCode,
        H.DocEntry,
        H.DocNum,
        H.CardCode,
        H.CardName,
        H.SlpCode,
        S.SlpName,
        H.DocDate,
        L.Quantity AS CantidadNeta,
        H.DocNum AS DocumentoUnico,
        'Factura venta' AS TipoDocumento
    FROM OINV H
    INNER JOIN INV1 L
        ON H.DocEntry = L.DocEntry
    LEFT JOIN OSLP S
        ON H.SlpCode = S.SlpCode
    WHERE
        H.CANCELED = 'N'
        AND H.DocDate >= '{fecha_inicio_visual_sql}'
        AND H.DocDate < '{fecha_fin_exclusiva_sql}'

    UNION ALL

    /* =====================================================
       NOTAS DE CRÉDITO DE VENTA
       ===================================================== */

    SELECT
        L.ItemCode,
        H.DocEntry,
        H.DocNum,
        H.CardCode,
        H.CardName,
        H.SlpCode,
        S.SlpName,
        H.DocDate,
        L.Quantity * -1 AS CantidadNeta,
        H.DocNum AS DocumentoUnico,
        'Nota crédito venta' AS TipoDocumento
    FROM ORIN H
    INNER JOIN RIN1 L
        ON H.DocEntry = L.DocEntry
    LEFT JOIN OSLP S
        ON H.SlpCode = S.SlpCode
    WHERE
        H.CANCELED = 'N'
        AND H.DocDate >= '{fecha_inicio_visual_sql}'
        AND H.DocDate < '{fecha_fin_exclusiva_sql}'
),

VentasPivot AS (
    SELECT
        ItemCode,
        {columnas_ventas_sql}
    FROM VentasBase
    GROUP BY
        ItemCode
),

MetricasVentasArticulo AS (
    SELECT
        ItemCode,

        SUM(
            CASE
                WHEN DocDate >= '{fecha_inicio_historico_sql}'
                 AND DocDate < '{fecha_fin_exclusiva_sql}'
                THEN CantidadNeta
                ELSE 0
            END
        ) AS [ventas_netas_24m],

        SUM(
            CASE
                WHEN DocDate >= '{fecha_inicio_historico_sql}'
                 AND DocDate < '{fecha_fin_exclusiva_sql}'
                THEN CantidadNeta
                ELSE 0
            END
        ) / NULLIF({periodo_meses_historico}, 0) AS [venta_anual_promedio_24m],

        COUNT(DISTINCT CASE
            WHEN TipoDocumento = 'Factura venta'
             AND DocDate >= '{fecha_inicio_historico_sql}'
             AND DocDate < '{fecha_fin_exclusiva_sql}'
            THEN DocumentoUnico
        END)
        -
        COUNT(DISTINCT CASE
            WHEN TipoDocumento = 'Nota crédito venta'
             AND DocDate >= '{fecha_inicio_historico_sql}'
             AND DocDate < '{fecha_fin_exclusiva_sql}'
            THEN DocumentoUnico
        END) AS [conteo_facturas_24m],

        COUNT(DISTINCT CASE
            WHEN DocDate >= '{fecha_inicio_historico_sql}'
             AND DocDate < '{fecha_fin_exclusiva_sql}'
            THEN CardCode
        END) AS [cantidad_clientes_24m],

        CAST(
            COUNT(DISTINCT CASE
                WHEN TipoDocumento = 'Factura venta'
                 AND DocDate >= '{fecha_inicio_historico_sql}'
                 AND DocDate < '{fecha_fin_exclusiva_sql}'
                THEN DocumentoUnico
            END)
            -
            COUNT(DISTINCT CASE
                WHEN TipoDocumento = 'Nota crédito venta'
                 AND DocDate >= '{fecha_inicio_historico_sql}'
                 AND DocDate < '{fecha_fin_exclusiva_sql}'
                THEN DocumentoUnico
            END)
            AS decimal(18, 4)
        ) / NULLIF({periodo_meses_historico}, 0) AS [frecuencia_venta_mensual_24m]

    FROM VentasBase
    GROUP BY
        ItemCode
),

InventarioFiltrado AS (
    SELECT
        ItemCode,
        MAX(WhsCode) AS WhsCode,
        SUM(OnHand) AS OnHand,
        SUM(IsCommited) AS IsCommited,
        SUM(OnOrder) AS OnOrder,
        MAX(AvgPrice) AS AvgPrice,
        MAX(MinStock) AS MinStock,
        MAX(MaxStock) AS MaxStock
    FROM OITW
    WHERE
        {condicion_bodegas}
        {filtro_stock_sql}
    GROUP BY
        ItemCode
),

PreciosPivot AS (
    SELECT
        TP.ItemCode,
        MAX(CASE WHEN TP.PriceList = 11 THEN TP.Price END) AS [precio_lista_11_promociones_ecommerce],
        MAX(CASE WHEN TP.PriceList = 12 THEN TP.Price END) AS [precio_lista_12_b2b_vip],
        MAX(CASE WHEN TP.PriceList = 13 THEN TP.Price END) AS [precio_lista_13_b2c],
        MAX(CASE WHEN TP.PriceList = 14 THEN TP.Price END) AS [precio_lista_14_b2b_estandar]
    FROM ITM1 TP
    WHERE
        {condicion_listas_precio}
    GROUP BY
        TP.ItemCode
),

LeadTimeArticulo AS (

    /* =====================================================
       LEAD TIME PROMEDIO POR ARTÍCULO
       ===================================================== */

    SELECT
        LPO.ItemCode,

        COUNT(DISTINCT CONCAT('OPDN-', HGR.DocEntry))
            AS [cantidad_entradas_compra_con_oc],

        AVG(
            CAST(
                DATEDIFF(
                    DAY,
                    HPO.CreateDate,
                    HGR.DocDate
                ) AS decimal(18, 4)
            )
        ) AS [lead_time_promedio_dias],

        MIN(
            DATEDIFF(
                DAY,
                HPO.CreateDate,
                HGR.DocDate
            )
        ) AS [lead_time_min_dias],

        MAX(
            DATEDIFF(
                DAY,
                HPO.CreateDate,
                HGR.DocDate
            )
        ) AS [lead_time_max_dias],

        MAX(HGR.DocDate) AS [ultima_entrada_mercancia]

    FROM OPOR HPO

    INNER JOIN POR1 LPO
        ON HPO.DocEntry = LPO.DocEntry

    INNER JOIN PDN1 LGR
        ON LGR.BaseEntry = LPO.DocEntry
        AND LGR.BaseLine = LPO.LineNum
        AND LGR.BaseType = 22

    INNER JOIN OPDN HGR
        ON LGR.DocEntry = HGR.DocEntry

    WHERE
        HPO.CANCELED = 'N'
        AND HGR.CANCELED = 'N'
        AND HGR.DocDate >= '{fecha_inicio_historico_sql}'
        AND HGR.DocDate < '{fecha_fin_exclusiva_sql}'
        AND DATEDIFF(DAY, HPO.CreateDate, HGR.DocDate) >= 0

    GROUP BY
        LPO.ItemCode
)

SELECT
    T0.ItemCode AS [codigo_articulo],
    T0.ItemName AS [descripcion_completa],
    TG.ItmsGrpNam AS [grupo_articulo],

    T0.U_CI_CAT AS [categoria],
    T0.U_CI_SCAT AS [subcategoria],
    T0.U_CI_TIPO AS [tipo],

    T0.InvntryUom AS [unidad_medida_inventario],
    TM.FirmName AS [marca_fabricante],

    T0.LastPurDat AS [ultima_fecha_compra],
    T0.LastPurPrc AS [ultimo_precio_compra],

    INV.AvgPrice AS [costo_promedio],
    INV.WhsCode AS [codigo_bodega],
    INV.OnHand AS [stock_en_mano],
    INV.IsCommited AS [stock_comprometido],
    INV.OnOrder AS [stock_en_pedido_transito],

    ISNULL(MVA.[ventas_netas_24m], 0) AS [total_unidades_vendidas_24m],
    ISNULL(MVA.[venta_anual_promedio_24m], 0) AS [venta_anual_promedio_24m],
    ISNULL(MVA.[conteo_facturas_24m], 0) AS [conteo_facturas_24m],
    ISNULL(MVA.[cantidad_clientes_24m], 0) AS [cantidad_clientes_24m],
    ISNULL(MVA.[frecuencia_venta_mensual_24m], 0) AS [frecuencia_venta_mensual_24m],

    /* =====================================================
       LEAD TIME DE COMPRA
       ===================================================== */

    ISNULL(LTA.[cantidad_entradas_compra_con_oc], 0) AS [cantidad_entradas_compra_con_oc],
    LTA.[lead_time_promedio_dias] AS [lead_time_promedio_dias],
    LTA.[lead_time_min_dias] AS [lead_time_min_dias],
    LTA.[lead_time_max_dias] AS [lead_time_max_dias],
    LTA.[ultima_entrada_mercancia] AS [ultima_entrada_mercancia],

    T0.MinOrdrQty AS [cantidad_minima_compra],
    INV.MinStock AS [stock_minimo],
    INV.MaxStock AS [stock_maximo],

    PP.[precio_lista_11_promociones_ecommerce],
    PP.[precio_lista_12_b2b_vip],
    PP.[precio_lista_13_b2c],
    PP.[precio_lista_14_b2b_estandar],

    {columnas_ventas_finales_sql}

FROM OITM T0

LEFT JOIN OITB TG
    ON T0.ItmsGrpCod = TG.ItmsGrpCod

LEFT JOIN OMRC TM
    ON T0.FirmCode = TM.FirmCode

INNER JOIN InventarioFiltrado INV
    ON T0.ItemCode = INV.ItemCode

LEFT JOIN MetricasVentasArticulo MVA
    ON T0.ItemCode = MVA.ItemCode

LEFT JOIN VentasPivot VP
    ON T0.ItemCode = VP.ItemCode

LEFT JOIN PreciosPivot PP
    ON T0.ItemCode = PP.ItemCode

LEFT JOIN LeadTimeArticulo LTA
    ON T0.ItemCode = LTA.ItemCode

WHERE
    T0.SellItem = 'Y'
    AND T0.PrchseItem = 'Y'
    AND T0.InvntItem = 'Y'
    AND T0.validFor = 'Y'
    AND T0.frozenFor = 'N'
    AND TM.FirmName IS NOT NULL
    AND LTRIM(RTRIM(TM.FirmName)) <> ''
    AND (
        {condiciones_fabricantes}
    )

ORDER BY
    TM.FirmName,
    T0.ItemCode;
"""

    # ============================================================
    # 7. Unificar parámetros
    # ============================================================

    params_query = {}

    if params_fabricantes is not None:
        params_query.update(params_fabricantes)

    params_query.update(params_bodegas)
    params_query.update(params_listas_precio)

    return query_oitm_ventas, params_query

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