"""
PIPELINE 04 - EVALUACION Y SELECCION DE K-MEANS
==============================================

Entrada: X_scaled, DataFrame numerico ya procesado por PreprocesadorDemanda.

Objetivos:
    1. Probar varios numeros de clusters (k).
    2. Calcular inercia, Silhouette, Davies-Bouldin y Calinski-Harabasz.
    3. Estimar el codo de la curva de inercia y proponer un k practico.
    4. Comprobar estabilidad entre semillas usando ARI.
    5. Entrenar el modelo K-Means definitivo.

IMPORTANTE:
    - El Silhouette Score se calcula con TODOS los articulos.
    - No hay muestreo, indices aleatorios ni np.flatnonzero().
    - No se leen archivos ni se modifica df_eda.
    - Las etiquetas que devolvemos conservan el orden de filas de X_scaled.
"""

import numpy as np
import pandas as pd

from sklearn.cluster import KMeans
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)

from . import clustering_config as cfg


# ============================================================
# 1. VALIDACION DE LA MATRIZ ESCALADA
# ============================================================

def _validar_X_scaled(X_scaled):
    """Comprueba que los datos sean validos antes de entrenar K-Means."""

    if not isinstance(X_scaled, pd.DataFrame):
        raise TypeError("X_scaled debe ser un DataFrame de Pandas.")

    if X_scaled.empty:
        raise ValueError("X_scaled esta vacio.")

    if X_scaled.columns.duplicated().any():
        raise ValueError("X_scaled tiene nombres de columnas duplicados.")

    # Rechazar texto, nulos e infinitos. No rellenamos valores automaticamente.
    try:
        datos = X_scaled.apply(pd.to_numeric, errors="raise").astype(float)
    except (TypeError, ValueError) as error:
        raise ValueError("Todas las variables deben ser numericas.") from error

    if not np.isfinite(datos.to_numpy()).all():
        raise ValueError("X_scaled contiene valores nulos o infinitos.")

    if len(datos) < 3:
        raise ValueError("Se necesitan al menos 3 articulos.")

    if len(datos.drop_duplicates()) < 2:
        raise ValueError("Todos los articulos tienen el mismo perfil matematico.")

    return datos


# ============================================================
# 2. EVALUAR DIFERENTES VALORES DE K
# ============================================================

def evaluar_modelos_kmeans(
    X_scaled,
    k_min=cfg.K_EVALUACION_MIN,
    k_max=cfg.K_EVALUACION_MAX,
):
    """Devuelve una tabla con la calidad de K-Means para cada k evaluado."""

    datos = _validar_X_scaled(X_scaled)
    n_articulos = len(datos)
    n_perfiles_distintos = len(datos.drop_duplicates())

    if k_min < 2 or k_max < k_min:
        raise ValueError("El rango debe cumplir: 2 <= k_min <= k_max.")

    # No podemos formar mas clusters que perfiles diferentes.
    # Ademas, Silhouette requiere menos clusters que articulos.
    k_max_permitido = min(k_max, n_perfiles_distintos, n_articulos - 1)

    if k_max_permitido < k_min:
        raise ValueError("No hay valores de k validos para estos datos.")

    # Un cluster menor al 1% genera una alerta para revisar su perfil.
    # No se descarta automaticamente del analisis.
    umbral_pequeno = getattr(cfg, "UMBRAL_CLUSTER_PEQUENO_PCT", 1.0)

    resultados = []

    for k in range(k_min, k_max_permitido + 1):

        # A. Entrenar sobre TODOS los articulos para este valor de k.
        modelo = KMeans(
            n_clusters=k,
            random_state=cfg.RANDOM_STATE,
            n_init=cfg.N_INIT_KMEANS,
        )
        etiquetas = modelo.fit_predict(datos)

        # B. Comprobar que realmente se formaron k grupos no vacios.
        grupos_reales = len(np.unique(etiquetas))
        if grupos_reales != k:
            raise ValueError(
                f"Para k={k}, K-Means formo solo {grupos_reales} grupos. "
                "Revisa los perfiles duplicados o el rango de k."
            )

        # C. Calcular las metricas de calidad (sin muestreo).
        inercia = modelo.inertia_
        silueta = silhouette_score(datos, etiquetas)
        davies_bouldin = davies_bouldin_score(datos, etiquetas)
        calinski_harabasz = calinski_harabasz_score(datos, etiquetas)

        # D. Calcular cuantos articulos tiene cada cluster.
        tamanos = np.bincount(etiquetas)
        cluster_min = int(tamanos.min())
        cluster_max = int(tamanos.max())
        cluster_min_pct = 100 * cluster_min / n_articulos

        # E. Registrar una fila por cada valor de k.
        resultados.append({
            "k": k,
            "inercia": float(inercia),
            "silhouette_score": float(silueta),
            "davies_bouldin_score": float(davies_bouldin),
            "calinski_harabasz_score": float(calinski_harabasz),
            "n_articulos": n_articulos,
            "n_clusters_efectivos": grupos_reales,
            "cluster_min_articulos": cluster_min,
            "cluster_max_articulos": cluster_max,
            "cluster_min_pct": cluster_min_pct,
            "alerta_cluster_pequeno": cluster_min_pct < umbral_pequeno,
            "n_muestra_silueta": n_articulos,
            "silueta_aproximada": False,
        })

    return pd.DataFrame(resultados)


# ============================================================
# 3. ESTIMAR EL CODO DE LA CURVA DE INERCIA
# ============================================================

def detectar_codo(df_metricas):
    """Estima el k del codo; devuelve None si no se aprecia uno claro.

    Idea: normalizar la curva de inercia y buscar el punto que mas se
    separa de la recta que une el primer y el ultimo valor evaluado.
    """

    tabla = df_metricas.sort_values("k")

    if len(tabla) < 3:
        return None

    k = tabla["k"].to_numpy(dtype=float)
    inercia = tabla["inercia"].to_numpy(dtype=float)

    if k.max() == k.min() or inercia.max() == inercia.min():
        return None

    # Convertir ambos ejes a una escala entre 0 y 1.
    k_normalizado = (k - k.min()) / (k.max() - k.min())
    inercia_normalizada = (inercia - inercia.min()) / (inercia.max() - inercia.min())

    # Cuanto mas positiva es la separacion, mas marcada es la caida inicial.
    separacion = (1 - k_normalizado) - inercia_normalizada
    posicion_codo = int(np.argmax(separacion))

    if separacion[posicion_codo] <= 1e-8:
        return None

    return int(k[posicion_codo])


# ============================================================
# 4. ELEGIR EL NUMERO DE CLUSTERS
# ============================================================

def seleccionar_k_optimo(
    df_metricas,
    k_forzado=cfg.K_FORZADO,
    k_practico_max=cfg.K_PRACTICO_MAX,
    tolerancia=cfg.TOLERANCIA_SILUETA,
):
    """Devuelve (k_optimo, k_codo, criterio, tabla_de_seleccion).

    Regla: considerar k pequenos, conservar los de buena silueta y,
    entre ellos, preferir el mas cercano al codo.
    """

    columnas_requeridas = {"k", "inercia", "silhouette_score"}
    if df_metricas.empty or not columnas_requeridas.issubset(df_metricas.columns):
        raise ValueError("La tabla no contiene las metricas necesarias.")

    if df_metricas["k"].duplicated().any() or tolerancia < 0:
        raise ValueError("Existen valores de k repetidos o una tolerancia negativa.")

    tabla = df_metricas.sort_values("k").reset_index(drop=True).copy()
    k_codo = detectar_codo(tabla)

    # A. Identificar los k que consideramos faciles de interpretar.
    tabla["k_codo_estimado"] = k_codo
    tabla["candidato_practico"] = tabla["k"] <= k_practico_max
    practicos = tabla[tabla["candidato_practico"]]

    if practicos.empty:
        raise ValueError("Ningun k cumple el limite practico.")

    # B. Considerar buenos los k cuya silueta esta cerca de la mejor.
    mejor_silueta = practicos["silhouette_score"].max()
    tabla["silueta_cerca_del_maximo"] = (
        tabla["candidato_practico"]
        & (tabla["silhouette_score"] >= mejor_silueta - tolerancia)
    )

    # C. Calcular la distancia de cada k al codo estimado.
    if k_codo is None:
        tabla["distancia_al_codo"] = np.nan
    else:
        tabla["distancia_al_codo"] = abs(tabla["k"] - k_codo)

    # D. Respetar k_forzado, si lo especificamos manualmente.
    if k_forzado is not None:
        if k_forzado not in tabla["k"].values:
            raise ValueError("K_FORZADO no esta dentro de los k evaluados.")

        k_optimo = int(k_forzado)
        criterio = "k_forzado_por_configuracion"

    else:
        # Seleccionar solo las opciones con buena silueta.
        opciones = tabla[tabla["silueta_cerca_del_maximo"]].copy()

        if k_codo is not None:
            # Primero el mas cercano al codo; luego mejor silueta y menor k.
            opciones = opciones.sort_values(
                ["distancia_al_codo", "silhouette_score", "k"],
                ascending=[True, False, True],
            )
            criterio = "silueta_cerca_del_maximo_y_proximidad_al_codo"
        else:
            # Si no hay codo, seleccionar mejor silueta; luego menor k.
            opciones = opciones.sort_values(
                ["silhouette_score", "k"],
                ascending=[False, True],
            )
            criterio = "silueta_dentro_de_tolerancia_sin_codo_detectable"

        k_optimo = int(opciones.iloc[0]["k"])

    tabla["seleccionado"] = tabla["k"] == k_optimo
    return k_optimo, k_codo, criterio, tabla


# ============================================================
# 5. COMPROBAR ESTABILIDAD MEDIANTE ARI
# ============================================================

def evaluar_estabilidad(X_scaled, k, semillas=None):
    """Compara agrupaciones creadas con diferentes semillas aleatorias.

    ARI cerca de 1: las ejecuciones agrupan articulos de manera similar.
    ARI cerca de 0: la coincidencia no supera lo esperable por azar.
    """

    datos = _validar_X_scaled(X_scaled)
    n_perfiles = len(datos.drop_duplicates())

    if not 2 <= k <= min(len(datos) - 1, n_perfiles):
        raise ValueError("k no es valido para los datos recibidos.")

    if semillas is None:
        semillas = cfg.SEMILLAS_ESTABILIDAD

    if len(semillas) < 2 or len(set(semillas)) != len(semillas):
        raise ValueError("Se necesitan al menos 2 semillas diferentes.")

    # A. Entrenar un modelo por cada semilla y guardar sus etiquetas.
    etiquetas_por_semilla = {}

    for semilla in semillas:
        modelo = KMeans(
            n_clusters=k,
            random_state=semilla,
            n_init=cfg.N_INIT_KMEANS,
        )
        etiquetas_por_semilla[semilla] = modelo.fit_predict(datos)

    # B. Comparar cada pareja de semillas una sola vez.
    comparaciones = []

    for posicion, semilla_a in enumerate(semillas):
        for semilla_b in semillas[posicion + 1:]:
            ari = adjusted_rand_score(
                etiquetas_por_semilla[semilla_a],
                etiquetas_por_semilla[semilla_b],
            )
            comparaciones.append({
                "k": k,
                "semilla_a": semilla_a,
                "semilla_b": semilla_b,
                "ari": float(ari),
            })

    df_detalle = pd.DataFrame(comparaciones)

    # C. Resumir las 10 comparaciones (si usamos cinco semillas).
    df_resumen = pd.DataFrame([{
        "k": k,
        "n_semillas": len(semillas),
        "n_comparaciones": len(df_detalle),
        "ari_promedio": df_detalle["ari"].mean(),
        "ari_minimo": df_detalle["ari"].min(),
        "ari_maximo": df_detalle["ari"].max(),
        "ari_std": df_detalle["ari"].std(ddof=0),
    }])

    return df_resumen, df_detalle


# ============================================================
# 6. ENTRENAR EL MODELO DEFINITIVO
# ============================================================

def entrenar_modelo_final(X_scaled, k_optimo):
    """Entrena K-Means con el k elegido y devuelve modelo + etiquetas."""

    datos = _validar_X_scaled(X_scaled)
    n_perfiles = len(datos.drop_duplicates())

    if not 2 <= k_optimo <= min(len(datos) - 1, n_perfiles):
        raise ValueError("k_optimo no es valido para estos datos.")

    modelo = KMeans(
        n_clusters=k_optimo,
        random_state=cfg.RANDOM_STATE,
        n_init=cfg.N_INIT_KMEANS,
    )

    etiquetas = modelo.fit_predict(datos)

    if len(np.unique(etiquetas)) != k_optimo:
        raise ValueError("K-Means no formo el numero solicitado de clusters.")

    # etiquetas[i] corresponde al articulo en la fila i de X_scaled.
    return modelo, etiquetas