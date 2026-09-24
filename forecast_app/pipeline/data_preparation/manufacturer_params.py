from pathlib import Path
import pandas as pd


COLUMNAS_FABRICANTES_REQUERIDAS = [
    "codigo_fabricante",
    "marca_fabricante",
    "fabricante_stock",
    "meses_objetivo_cobertura"
]


def cargar_fabricantes_parametrizados(ruta_fabricantes):
    """
    Carga el archivo Excel de fabricantes parametrizados.

    El archivo debe contener como mínimo:
    - codigo_fabricante
    - marca_fabricante
    - fabricante_stock
    - meses_objetivo_cobertura

    Este archivo permite definir qué fabricantes se consideran de stock
    y cuántos meses de cobertura objetivo se desea manejar por marca.
    """

    ruta_fabricantes = Path(ruta_fabricantes)

    if not ruta_fabricantes.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo de fabricantes: {ruta_fabricantes}"
        )

    df_fabricantes = pd.read_excel(ruta_fabricantes)

    columnas_faltantes = [
        columna
        for columna in COLUMNAS_FABRICANTES_REQUERIDAS
        if columna not in df_fabricantes.columns
    ]

    if columnas_faltantes:
        raise ValueError(
            "Faltan columnas requeridas en el archivo de fabricantes: "
            + ", ".join(columnas_faltantes)
        )

    df_fabricantes = df_fabricantes.copy()

    df_fabricantes["marca_fabricante"] = (
        df_fabricantes["marca_fabricante"]
        .astype(str)
        .str.strip()
    )

    df_fabricantes["codigo_fabricante"] = pd.to_numeric(
        df_fabricantes["codigo_fabricante"],
        errors="coerce"
    )

    df_fabricantes["fabricante_stock"] = (
        df_fabricantes["fabricante_stock"]
        .astype(bool)
    )

    df_fabricantes["meses_objetivo_cobertura"] = pd.to_numeric(
        df_fabricantes["meses_objetivo_cobertura"],
        errors="coerce"
    )

    return df_fabricantes


def obtener_fabricantes_considerados(df_fabricantes):
    """
    Obtiene la lista de fabricantes marcados como fabricante_stock=True.

    Esta lista será usada para filtrar los artículos dentro del query SAP B1.
    """

    fabricantes_considerados = (
        df_fabricantes
        .loc[
            df_fabricantes["fabricante_stock"] == True,
            "marca_fabricante"
        ]
        .dropna()
        .astype(str)
        .str.strip()
    )

    fabricantes_considerados = fabricantes_considerados[
        fabricantes_considerados != ""
    ]

    return fabricantes_considerados.unique().tolist()


def construir_condicion_fabricantes_sql(
    fabricantes_considerados,
    columna_sql="TM.FirmName",
    usar_like=True
):
    """
    Construye la condición SQL dinámica para fabricantes.

    Retorna:
    - condiciones_fabricantes
    - params_fabricantes

    Ejemplo de salida:
    condiciones_fabricantes:
        TM.FirmName LIKE :fabricante_0 OR TM.FirmName LIKE :fabricante_1

    params_fabricantes:
        {
            "fabricante_0": "%NTN%",
            "fabricante_1": "%SIEMENS%"
        }

    Se usan parámetros nombrados para evitar insertar directamente valores
    dentro del SQL.
    """

    if not fabricantes_considerados:
        raise ValueError(
            "La lista de fabricantes considerados está vacía. "
            "Revisa el archivo de fabricantes y la columna fabricante_stock."
        )

    condiciones = []
    params = {}

    for indice, fabricante in enumerate(fabricantes_considerados):
        nombre_parametro = f"fabricante_{indice}"

        if usar_like:
            condiciones.append(
                f"{columna_sql} LIKE :{nombre_parametro}"
            )
            params[nombre_parametro] = f"%{fabricante}%"
        else:
            condiciones.append(
                f"{columna_sql} = :{nombre_parametro}"
            )
            params[nombre_parametro] = fabricante

    condiciones_fabricantes = " OR ".join(condiciones)

    return condiciones_fabricantes, params


def obtener_mapa_cobertura_por_fabricante(df_fabricantes):
    """
    Construye un diccionario:

    marca_fabricante -> meses_objetivo_cobertura

    Este mapa será útil más adelante para asignar meses de cobertura objetivo
    al dataframe final.
    """

    df_temp = df_fabricantes.dropna(
        subset=["meses_objetivo_cobertura"]
    ).copy()

    mapa_cobertura = dict(
        zip(
            df_temp["marca_fabricante"],
            df_temp["meses_objetivo_cobertura"]
        )
    )

    return mapa_cobertura


def main():
    """
    Prueba directa del módulo manufacturer_params.py.
    """

    project_root = Path(__file__).resolve().parents[3]

    ruta_fabricantes = (
        project_root
        / "forecast_app"
        / "data"
        / "input"
        / "fabricantes_repuestos_cerosa.xlsx"
    )

    print("=" * 80)
    print("PRUEBA MANUFACTURER PARAMS")
    print("=" * 80)

    print("Ruta fabricantes:", ruta_fabricantes)
    print("Existe archivo:", ruta_fabricantes.exists())

    df_fabricantes = cargar_fabricantes_parametrizados(
        ruta_fabricantes=ruta_fabricantes
    )

    fabricantes_considerados = obtener_fabricantes_considerados(
        df_fabricantes=df_fabricantes
    )

    condiciones_fabricantes, params_fabricantes = construir_condicion_fabricantes_sql(
        fabricantes_considerados=fabricantes_considerados
    )

    mapa_cobertura = obtener_mapa_cobertura_por_fabricante(
        df_fabricantes=df_fabricantes
    )

    print("\nArchivo cargado correctamente ✅")
    print("Filas fabricantes:", df_fabricantes.shape[0])
    print("Columnas fabricantes:", df_fabricantes.shape[1])

    print("\nFabricantes considerados stock:")
    print(len(fabricantes_considerados))

    print("\nPrimeros 10 fabricantes considerados:")
    for fabricante in fabricantes_considerados[:10]:
        print("-", fabricante)

    print("\nCondición SQL generada, primeros 500 caracteres:")
    print(condiciones_fabricantes[:500])

    print("\nPrimeros parámetros:")
    primeros_params = dict(list(params_fabricantes.items())[:5])
    print(primeros_params)

    print("\nFabricantes con meses objetivo de cobertura:")
    print(len(mapa_cobertura))


if __name__ == "__main__":
    main()