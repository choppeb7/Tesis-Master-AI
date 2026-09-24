import pandas as pd
from sqlalchemy import text


def extraer_dataframe_sql(
    engine,
    query,
    params=None,
    nombre_dataframe="dataframe"
):
    """
    Ejecuta un query SQL usando SQLAlchemy y devuelve un dataframe de pandas.

    Parámetros:
    - engine:
        Engine SQLAlchemy creado previamente en connections.py.

    - query:
        Query SQL en formato string.

    - params:
        Diccionario de parámetros para el query.
        Puede ser None si el query no tiene parámetros.

    - nombre_dataframe:
        Nombre descriptivo usado solo para mensajes de error.

    Retorna:
    - DataFrame de pandas.
    """

    if params is None:
        params = {}

    if engine is None:
        raise ValueError("El engine recibido es None. Revisa la conexión SQL Server.")

    if query is None or str(query).strip() == "":
        raise ValueError(f"El query para {nombre_dataframe} está vacío.")

    try:
        df = pd.read_sql(
            sql=text(query),
            con=engine,
            params=params
        )

    except Exception as error:
        raise RuntimeError(
            f"Error ejecutando query para {nombre_dataframe}: {error}"
        ) from error

    return df


def extraer_oitm_ventas(
    engine,
    query_oitm_ventas,
    params_query=None
):
    """
    Ejecuta el query principal de artículos, ventas, compras e inventario.

    Retorna:
    - df_OITM_Ventas
    """

    df_OITM_Ventas = extraer_dataframe_sql(
        engine=engine,
        query=query_oitm_ventas,
        params=params_query,
        nombre_dataframe="df_OITM_Ventas"
    )

    return df_OITM_Ventas


def validar_dataframe_extraido(
    df,
    columnas_minimas=None,
    nombre_dataframe="dataframe"
):
    """
    Valida que el dataframe extraído tenga datos y columnas esperadas.

    No transforma el dataframe; solamente revisa estructura básica.
    """

    if df is None:
        raise ValueError(f"{nombre_dataframe} es None.")

    if df.empty:
        print(f"Advertencia: {nombre_dataframe} fue extraído, pero está vacío.")
        return False

    if columnas_minimas is not None:
        columnas_faltantes = [
            columna
            for columna in columnas_minimas
            if columna not in df.columns
        ]

        if columnas_faltantes:
            raise ValueError(
                f"{nombre_dataframe} no contiene columnas mínimas esperadas: "
                + ", ".join(columnas_faltantes)
            )

    return True


def mostrar_resumen_dataframe(
    df,
    nombre_dataframe="dataframe",
    max_columnas=20
):
    """
    Imprime un resumen simple del dataframe extraído.
    """

    print("=" * 80)
    print(f"RESUMEN {nombre_dataframe}")
    print("=" * 80)

    print(f"Filas: {df.shape[0]:,}")
    print(f"Columnas: {df.shape[1]:,}")

    print("\nPrimeras columnas:")
    for columna in list(df.columns[:max_columnas]):
        print("-", columna)

    if df.shape[1] > max_columnas:
        print(f"... {df.shape[1] - max_columnas} columnas adicionales")

    print("\nTipos de datos principales:")
    print(df.dtypes.head(max_columnas))


def main():
    """
    Prueba simple de extraction.py.

    Esta prueba no ejecuta todavía el query grande.
    Solo valida que extraction.py puede ejecutar un query pequeño
    usando el engine de SQL Server.
    """

    from pathlib import Path
    import sys

    project_root = Path(__file__).resolve().parents[3]
    forecast_app_dir = project_root / "forecast_app"

    if str(forecast_app_dir) not in sys.path:
        sys.path.insert(0, str(forecast_app_dir))

    from pipeline.data_preparation.connections import crear_engine_sqlserver

    print("=" * 80)
    print("PRUEBA EXTRACTION.PY")
    print("=" * 80)

    engine = crear_engine_sqlserver()

    query_prueba = """
    SELECT TOP 10
        ItemCode,
        ItemName,
        FirmCode
    FROM OITM
    """

    df_prueba = extraer_dataframe_sql(
        engine=engine,
        query=query_prueba,
        params=None,
        nombre_dataframe="df_prueba_oitm"
    )

    validar_dataframe_extraido(
        df=df_prueba,
        columnas_minimas=["ItemCode", "ItemName", "FirmCode"],
        nombre_dataframe="df_prueba_oitm"
    )

    mostrar_resumen_dataframe(
        df=df_prueba,
        nombre_dataframe="df_prueba_oitm"
    )

    print("\nExtracción de prueba completada correctamente ✅")


if __name__ == "__main__":
    main()