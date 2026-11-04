"""
PIPELINE 04 - PREPROCESAMIENTO DE VARIABLES PARA CLUSTERING
==========================================================

Secuencia basada en el notebook 04 del TFM:
    1. Diagnóstico estadístico original.
    2. Winsorización condicional por skewness / kurtosis e IQR.
    3. Transformación individual: log1p, Yeo-Johnson o ninguna.
    4. Escalado robusto (RobustScaler).

Entrada:
    X: DataFrame numérico de clustering_data_preparation.py.

Salidas:
    X_escalado, tablas de diagnóstico y parámetros aprendidos.

La clase conserva los límites, transformaciones y el escalador ajustados,
para poder aplicar exactamente las mismas reglas a nuevos datos.

NO lee archivos, NO modifica df_eda y NO entrena K-Means.
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import PowerTransformer, RobustScaler
from . import clustering_config as cfg

ETAPAS=(
    "original",
    "post_transformacion",
    "post_escalado",
)

"""
PIPELINE 04 - PREPROCESAMIENTO DE VARIABLES PARA CLUSTERING
==========================================================

Secuencia basada en el notebook 04 del TFM:
    1. Diagnóstico estadístico original.
    2. Winsorización condicional por skewness / kurtosis e IQR.
    3. Transformación individual: log1p, Yeo-Johnson o ninguna.
    4. Escalado robusto (RobustScaler).

Entrada:
    X: DataFrame numérico de clustering_data_preparation.py.

Salidas:
    X_escalado, tablas de diagnóstico y parámetros aprendidos.

La clase conserva los límites, transformaciones y el escalador ajustados,
para poder aplicar exactamente las mismas reglas a nuevos datos.

NO lee archivos, NO modifica df_eda y NO entrena K-Means.
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import PowerTransformer, RobustScaler

from . import clustering_config as cfg


# ============================================================
# 1. DIAGNÓSTICO ESTADÍSTICO
# ============================================================

ETAPAS = (
    "original",
    "post_winsorizacion",
    "post_transformacion",
    "post_escalado",
)


def diagnosticar_variable(serie):
    """Devuelve estadísticas descriptivas y de forma de una variable.

    Kurtosis de Pandas = curtosis en exceso (distribución normal ≈ 0).
    """
    serie = pd.Series(serie, dtype="float64")
    q1, q3 = serie.quantile([0.25, 0.75])

    return {
        "cantidad": int(serie.count()),
        "ceros_pct": float(100 * serie.eq(0).mean()),
        "media": float(serie.mean()),
        "mediana": float(serie.median()),
        "std": float(serie.std()),
        "min": float(serie.min()),
        "p01": float(serie.quantile(0.01)),
        "p05": float(serie.quantile(0.05)),
        "q1": float(q1),
        "q3": float(q3),
        "p95": float(serie.quantile(0.95)),
        "p97": float(serie.quantile(0.97)),
        "p99": float(serie.quantile(0.99)),
        "max": float(serie.max()),
        "iqr": float(q3 - q1),
        "skewness": float(serie.skew()),
        "kurtosis": float(serie.kurt()),
    }

def diagnosticar_matriz(X, etapa):
    """Una fila por variable para una etapa del preprocesamiento."""
    return pd.DataFrame([
        {"variable": columna, "etapa": etapa, **diagnosticar_variable(X[columna])}
        for columna in X.columns
    ])

def comparar_diagnosticos(df_diagnosticos):

    metricas=[
        "skewness", "kurtosis", "media", "mediana", "std",
                "min", "max", "q1", "q3", "iqr", "p95", "p99",
        ]
    tabla=df_diagnosticos.pivot(
        index="variable",
        columns="etapa",
        values="metricas"
    )
    tabla.columns=[
        f"{metrica}_{etapa}"
        for metrica, etapa in tabla.columns
    ]
    return tabla.reset_index()

#==============================================================
# 2. PREPROCESADOR REUTILIZABLE
#====================================================
def __init__(
       self,
        aplicar_winsor=cfg.APLICAR_WINSORIZACION,
        factor_iqr=cfg.FACTOR_IQR_WINSOR,
        umbral_skew_winsor=cfg.UMBRAL_SKEW_WINSOR,
        umbral_kurtosis_winsor=cfg.UMBRAL_KURTOSIS_WINSOR,
        umbral_skew_transform=cfg.UMBRAL_SKEW_TRANSFORMACION,
        umbral_kurtosis_transform=cfg.UMBRAL_KURTOSIS_TRANSFORMACION,
        variables_sin_transformacion=None,
    ):
        self.aplicar_winsor = aplicar_winsor
        self.factor_iqr = factor_iqr
        self.umbral_skew_winsor = umbral_skew_winsor
        self.umbral_kurtosis_winsor = umbral_kurtosis_winsor
        self.umbral_skew_transform = umbral_skew_transform
        self.umbral_kurtosis_transform = umbral_kurtosis_transform
        self.variables_sin_transformacion = list(
            cfg.VARIABLES_SIN_TRANSFORMACION
            if variables_sin_transformacion is None
            else variables_sin_transformacion
        )

def _validar_X(self, X, ajustar):
    """Valida columnas, tipos y finitud sin imputar ni cambiar X."""
    if not isinstance(X, pd.DataFrame):
         raise TypeError("X debe ser un dataframe")

    if X.empty or X.columns.duplicated().any():
         raise ValueError("X esta vacio o tiene nombres de columnas dulicados")

    if ajustar==False and hasattr(self, "columnas_")==False:
         raise ValueError("Primero debes ejecutar fit(X)")

    if ajustar==False and list(X.columns) != self.columnas_:
         raise ValueError(
              "Las columnas y su orden deben coincidir con las usadas en fit()"
         )

    datos=X.apply(pd.to_numeric, errors="raise").astype(float)
    if not np.isfinite(datos.to_numpy()).all():
         raise ValueError(" X contienen NaN o infinitos. Revisar datos")
    return datos

def fit(self, X):
    """Ajusta winsorizaciones, transformaciones y RobustScaler."""
    if self.factor_iqr <= 0:
        raise ValueError("factor_iqr debe ser positivo.")

    original = self._validar_X(X, ajustar=True)
    if len(original) < 4 or original.shape[1] < 2:
        raise ValueError("Se requieren al menos 4 artículos y 2 variables.")

    constantes = [
        nombre for nombre in original.columns
        if original[nombre].nunique() <= 1
        ]
    
    if constantes:
        raise ValueError(f"Variables constantes: {constantes}")
    
    self.columnas_ = list(original.columns)
    winsorizado = original.copy()
    transformado = original.copy()
    self.reglas_ = {}
    registros = []

    # ----------------------------------------------------
    # Regla específica para cada variable
    # ---------------------------------------------------- 
    for variable in self.columnas_: 
        diag= diagnosticar_variable(original[variable])  
        skew, kurt, iqr= diag["skewness"], diag["kurtosis"], diag["iqr"] 

        sesgo_fuerte=np.isfinite(skew) and abs(skew)> self.umbral_skew_winsor
        cola_pesada=np.isfinite(kurt) and kurt >= self.umbral_kurtosis_winsor
        aplicar=bool(self.aplicar_winsor and iqr>0 and (sesgo_fuerte or cola_pesada))

        limite_inf=np.nan
        limite_sup=np.nan
        motivo = "no_supera_umbrales"
        if not self.aplicar_winsor:
            motivo = "winsorizacion_desactivada"
        elif iqr<=0:
            motivo="iqr_cero_no_aplicable"
        elif aplicar:
            motivo="sesgo_y_curtosis" if sesgo_fuerte and cola_pesada else (
                  "sesgo_fuerte" if sesgo_fuerte else "curtosis_elevada"
                )
            limite_inf=diag["q1"]- self.factor_iqr*iqr
            limite_sup=diag["q3"]+ self.factor_iqr*iqr
            if diag["min"]>=0:
                limite_inf=max(0.0, limite_inf)
            winsorizado[variable]=original[variable].clip(
                lower=limite_inf, upper=limite_sup
            )
        #Diagnostico de la variable despues de winsorizar. 
        diag_w=diagnosticar_variable(winsorizado[variable])
        sesgo_w=diag_w["skewness"]
        kurt_w=diag_w["kurtosis"]
        sesgo_w_alto=(
            np.isfinite(sesgo_w) and
            abs(sesgo_w) >= self.umbral_skew_transform
        )
        kurt_w_alta=(
            np.isfinite(kurt_w)
            and kurt_w >= self.umbral_kurtosis_transform
        )

        tipo="sin_transformacion"
        if variable not in self.variables_sin_transformacion:
            if diag_w["min"] <0 and (sesgo_w_alto or  kurt_w_alta):
                tipo="yeo_johnson"
            elif diag_w["min"]>= 0 and ( 
                (np.isfinite(sesgo_w) and sesgo_w >= self.umbral_skew_transform)
                or kurt_w_alta
            ):
                tipo="log1p"

        pt= None

        if tipo=="log1p":
            transformado[variable]=np.log1p(winsorizado[variable])
        elif tipo == "yeo_johnson":
            pt=PowerTransformer(method="yeo-johnson", standardize=False)
            transformado[variable]=pt.fit_transform(winsorizado[[variable]]).ravel()
        else:
            transformado[variable]=winsorizado[variable]

        recortados=int(
            (original[variable]!= winsorizado[variable]).sum()
        )
        self.reglas_[variable]={
            "winsorizado": aplicar,
            "limite_inferior": limite_inf,
            "limite_superior": limite_sup,
            "transformacion": tipo,
            "power_transformer": pt,
        }
        registros.append({
            "variable": variable,
            "winsorizado": aplicar, 
            "motivo_winsor": motivo, 
            "limite_inferior": limite_inf,
            "limite_superior": limite_sup,
            "valores_recortados": recortados,
            "porcentaje_recortado": 100 * recortados/ len(original),
            "transformacion": tipo, 
            "lambda_yeo_johnson":(
                    float(pt.lambdas_[0]) if pt is not None else np.nan
                ),
        })

        # ----------------------------------------------------
        # Escalado común después de tratar todas las variables
        # ----------------------------------------------------
        #Escalar matriz post winsorizacion y post transformación
        self.scaler_ = RobustScaler()
        matriz_escalada = self.scaler_.fit_transform(transformado)
        escalado = pd.DataFrame(
            matriz_escalada, columns=self.columnas_, index=original.index
        )
        #Escalar matriz post winsorizacion y post transformación
        self.registro_ = pd.DataFrame(registros)

        #Parametro de escalado por variable
        self.parametros_scaler_ = pd.DataFrame({
            "variable": self.columnas_,
            "mediana_robust_scaler": self.scaler_.center_,
            "escala_robust_scaler": self.scaler_.scale_,
        })
        #diccionario de matrices original, post_wins, post_transf y post_escalado
        self.matrices_entrenamiento_ = {
            "original": original,
            "post_winsorizacion": winsorizado,
            "post_transformacion": transformado,
            "post_escalado": escalado,
        }

        #iteramos el diagnostico de matrices y concatenamos el resultado el diagnostico por cada matriz considera la iteracion por variable
        self.diagnosticos_ = pd.concat(
            [
                diagnosticar_matriz(self.matrices_entrenamiento_[etapa], etapa)
                for etapa in ETAPAS
            ],
            ignore_index=True,
        )
        #Con esto generamos una sola fila por variable para identifica la evolucion de las metricas respecto a las etapas
        self.comparativo_ = comparar_diagnosticos(self.diagnosticos_)

        #Todos los parametros aprendidos dentro de self han quedado definidos aprendidos
        return self

def transfrom(self, X):
    """Replica parámetros aprendidos sin reajustarlos"""
    datos=self._validar_X(X, ajustar=False)
    tratados=datos.copy()

    for variable in self.columnas_: 
        regla= self.reglas_[variable]
        if regla["winsorizado"]:
            tratados[variable]=tratados[variable].clip(
                lower=regla["limite_inferior"],
                upper=regla["limite_superior"],
            )
        if regla["transformacion"]=="log1p":
            if (tratados[variable]<-1).any():
                raise ValueError(
                    f"La variable '{variable}' contiene valores negativos fuera del dominio de log1p"
                )
            tratados[variable]=np.log1p(tratados[variable])
        elif regla["transformacion"]=="yeo_johnson":
            tratados[variable]=regla["power_transformer"].transform(
                tratados[[variable]]
            ).ravel()
    
    resultado=self.scaler_.transform(tratados)
    if not np.isfinite(resultado).all():
        raise ValueError(" El preprocesamiento produjo valores no finitos")
    return pd.DataFrame(
        resultado, columns=self.columnas_, index=X.index
    )

def fit_transform(self, X):
    """Ajusta y devuelve la matriz escalada sin modificar la original."""
    self.fit(X)
    return self.matrices_entrenamiento_["post_escalado"].copy()



