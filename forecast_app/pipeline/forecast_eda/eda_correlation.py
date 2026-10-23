import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
import sys
# ============================================================
# AJUSTE DE RUTA PARA IMPORTAR forecast_app
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FORECAST_APP_DIR = PROJECT_ROOT / "forecast_app"

if str(FORECAST_APP_DIR) not in sys.path:
    sys.path.insert(0, str(FORECAST_APP_DIR))

forecast_app_dir = Path(__file__).resolve().parents[3] / "forecast_app"
reports_figures_dir = forecast_app_dir / "reports" / "figures" / "03_forecast_eda"
reports_tables_dir = forecast_app_dir / "reports" / "tables" / "03_forecast_eda"


def analizar_correlaciones_eda(
    df,
    variables,
    umbral=0.85,
    metodo="spearman",
    ruta_salida=None
):

    if ruta_salida is None:
        ruta_salida_imagenes = reports_figures_dir 
        ruta_salida_tablas = reports_tables_dir 

    # 1. Validar variables disponibles
    columnas = [c for c in dict.fromkeys(variables) if c in df.columns]
    X = df[columnas].select_dtypes(include="number").copy()

    # Excluir variables sin variabilidad
    constantes = X.columns[X.nunique(dropna=True) <= 1].tolist()
    X = X.drop(columns=constantes)

    # 2. Calcular matriz de correlación
    matriz = X.corr(method=metodo)
    matriz.to_csv(ruta_salida_tablas / "matriz_correlacion.csv")

    # 3. Generar heatmap
    plt.figure(figsize=(16, 13))
    sns.heatmap(
        matriz,
        cmap="coolwarm",
        center=0,
        vmin=-1,
        vmax=1,
        annot=True,
        fmt=".2f",
        square=True
    )
    plt.title(f"Matriz de correlación - {metodo.capitalize()}")
    plt.tight_layout()
    plt.savefig(ruta_salida_imagenes / "heatmap_correlacion.png", dpi=300)
    plt.close()

    # 4. Identificar pares con alta correlación
    pares = []
    columnas_matriz = matriz.columns.tolist()

    for i in range(len(columnas_matriz)):
        for j in range(i + 1, len(columnas_matriz)):
            valor = matriz.iloc[i, j]

            if pd.notna(valor) and abs(valor) >= umbral:
                pares.append({
                    "variable_1": columnas_matriz[i],
                    "variable_2": columnas_matriz[j],
                    "correlacion": valor,
                    "correlacion_abs": abs(valor)
                })

    df_pares = pd.DataFrame(
        pares,
        columns=[
            "variable_1", "variable_2",
            "correlacion", "correlacion_abs"
        ]
    )

    df_pares = df_pares.sort_values(
        "correlacion_abs", ascending=False
    )
    df_pares.to_csv(
        ruta_salida_tablas / "pares_alta_correlacion.csv",
        index=False
    )

    # 5. Selección preliminar de variables
    # Se priorizan las variables que aparecen primero
    # en la lista recibida.
    seleccionadas = []

    for variable in columnas_matriz:
        redundante = any(
            pd.notna(matriz.loc[variable, previa])
            and abs(matriz.loc[variable, previa]) >= umbral
            for previa in seleccionadas
        )

        if not redundante:
            seleccionadas.append(variable)

    eliminadas = [
        c for c in columnas_matriz
        if c not in seleccionadas
    ]

    pd.DataFrame({
        "variable": columnas_matriz,
        "seleccionada": [
            c in seleccionadas for c in columnas_matriz
        ]
    }).to_csv(
        ruta_salida_tablas / "seleccion_variables_para_cluster.csv",
        index=False
    )

    print(f"Variables originales: {len(columnas)}")
    print(f"Variables constantes: {len(constantes)}")
    print(f"Variables seleccionadas: {len(seleccionadas)}")
    print(f"Variables descartadas por correlación: {len(eliminadas)}")

    return {
        "matriz": matriz,
        "pares": df_pares,
        "seleccionadas": seleccionadas,
        "eliminadas": eliminadas,
        "constantes": constantes
    }