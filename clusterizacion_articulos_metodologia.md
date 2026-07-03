# Clusterización de artículos aplicables a forecast

Una vez identificados los artículos que cumplen las condiciones mínimas para ser considerados dentro del proceso de forecast, el siguiente paso consiste en agruparlos según su comportamiento histórico de venta. Esta etapa es importante porque no todos los artículos presentan el mismo patrón de demanda, frecuencia de venta, variabilidad o estabilidad en el tiempo.

El objetivo de esta sección es definir las variables que serán utilizadas para clusterizar los artículos en grupos homogéneos. Posteriormente, sobre cada grupo se podrán comparar distintos modelos matemáticos de predicción, con el fin de identificar cuál algoritmo ofrece mejor desempeño para cada tipo de comportamiento de demanda.

---

## Objetivo de la clusterización

La clusterización tiene como finalidad clasificar los artículos aplicables a forecast en grupos con características similares de venta histórica. Esto permitirá evitar la aplicación indiscriminada de un único modelo predictivo sobre todo el catálogo y, en su lugar, seleccionar modelos de forecast más adecuados según el comportamiento de cada grupo.

En otras palabras, se busca responder preguntas como:

* ¿Qué artículos tienen demanda frecuente y estable?
* ¿Qué artículos presentan demanda intermitente?
* ¿Qué artículos tienen alta variabilidad en sus ventas?
* ¿Qué artículos muestran posible estacionalidad?
* ¿Qué artículos tienen bajo volumen pero comportamiento repetitivo?
* ¿Qué artículos requieren modelos simples y cuáles podrían beneficiarse de modelos más avanzados?

---

## Enfoque metodológico

El procedimiento propuesto consiste en:

1. Partir únicamente de los artículos previamente clasificados como aplicables a forecast.
2. Seleccionar variables que describan el comportamiento histórico de venta de cada artículo.
3. Estandarizar las variables para evitar que las magnitudes dominen el proceso de clusterización.
4. Aplicar algoritmos de agrupamiento no supervisado.
5. Evaluar la calidad de los clusters generados.
6. Interpretar cada cluster desde una perspectiva de negocio.
7. Comparar modelos de forecast dentro de cada cluster.
8. Seleccionar el modelo ganador por grupo de artículos.

Este enfoque permite construir una metodología más eficiente, ya que el sistema no dependerá de entrenar y evaluar múltiples modelos de manera individual para cada artículo, sino que podrá identificar patrones comunes entre grupos de productos.

---

## Variables propuestas para la clusterización

Para agrupar los artículos se utilizarán variables calculadas a partir del historial de ventas, con énfasis en métricas que describan frecuencia, volumen, variabilidad, estabilidad y comportamiento temporal de la demanda.

### 1. Volumen de demanda histórica

Estas variables permiten identificar el nivel de movimiento comercial del artículo.

* `total_unidades_vendidas_24m`: cantidad total vendida en los últimos 24 meses.
* `venta_anual_promedio_24m`: venta promedio anual estimada con base en los últimos 24 meses.
* `promedio_venta_mensual_24m`: promedio mensual de unidades vendidas.
* `max_venta_mensual_24m`: venta máxima registrada en un mes.
* `mediana_venta_mensual_24m`: valor mediano de venta mensual.

Estas métricas permiten diferenciar artículos de alta, media y baja rotación.

---

### 2. Frecuencia de venta

Estas variables ayudan a medir qué tan constante es la demanda del artículo.

* `meses_con_venta_24m`: cantidad de meses con venta mayor a cero.
* `frecuencia_venta_24m_pct`: porcentaje de meses con venta sobre el total de meses analizados.
* `frecuencia_venta_mensual_24m`: frecuencia promedio mensual de venta.
* `meses_sin_venta_24m`: cantidad de meses sin movimiento de venta.

Estas métricas son especialmente importantes para distinguir artículos con demanda continua frente a artículos con demanda intermitente.

---

### 3. Intermitencia de la demanda

En repuestos industriales, muchos artículos no presentan ventas todos los meses. Por ello, es necesario incluir variables que permitan identificar patrones de demanda irregular.

* `porcentaje_meses_sin_venta_24m`: proporción de meses sin venta.
* `intervalo_promedio_entre_ventas`: tiempo promedio entre meses con venta.
* `max_meses_consecutivos_sin_venta`: mayor cantidad de meses consecutivos sin venta.
* `coeficiente_intermitencia`: indicador del grado de separación entre eventos de demanda.

Estas variables permiten identificar artículos que podrían requerir modelos específicos para demanda intermitente, como Croston, SBA o TSB.

---

### 4. Variabilidad de la demanda

Estas variables permiten medir qué tan estable o irregular es el comportamiento de venta mensual.

* `desviacion_estandar_venta_mensual_24m`: dispersión de la venta mensual.
* `coeficiente_variacion_venta_24m`: relación entre la desviación estándar y el promedio mensual.
* `rango_venta_mensual_24m`: diferencia entre la venta máxima y mínima.
* `iqr_venta_mensual_24m`: rango intercuartílico de la venta mensual.

El coeficiente de variación es especialmente útil porque permite comparar la variabilidad entre artículos con diferentes niveles de venta.

---

### 5. Tendencia de venta

Estas variables permiten analizar si el comportamiento del artículo muestra crecimiento, estabilidad o decrecimiento.

* `venta_ultimos_6m`: unidades vendidas en los últimos 6 meses.
* `venta_6m_previos`: unidades vendidas entre los meses 7 y 12 hacia atrás.
* `variacion_venta_6m_vs_6m_previos_pct`: variación porcentual entre ambos períodos.
* `pendiente_tendencia_24m`: pendiente de una regresión lineal simple sobre las ventas mensuales.
* `direccion_tendencia`: clasificación de tendencia creciente, estable o decreciente.

Estas variables permiten identificar artículos que, aunque tengan historial suficiente, podrían estar cambiando su comportamiento recientemente.

---

### 6. Estacionalidad potencial

Estas variables permiten detectar si existen patrones repetitivos en ciertos períodos del año.

* `venta_promedio_por_mes_calendario`: promedio histórico por mes calendario.
* `indice_estacionalidad`: diferencia relativa entre meses de alta y baja demanda.
* `meses_pico_demanda`: meses donde históricamente se concentra mayor venta.
* `concentracion_ventas_top_3_meses`: proporción de venta acumulada en los tres meses de mayor demanda.

Estas variables ayudan a identificar artículos que podrían beneficiarse de modelos con componentes estacionales, como SARIMA, ETS estacional o Prophet.

---

### 7. Recencia de la demanda

Estas variables permiten evaluar qué tan reciente ha sido el movimiento comercial del artículo.

* `meses_desde_ultima_venta`: cantidad de meses transcurridos desde la última venta.
* `venta_ultimos_3m`: unidades vendidas en los últimos 3 meses.
* `venta_ultimos_6m`: unidades vendidas en los últimos 6 meses.
* `participacion_venta_reciente`: proporción de la venta total que ocurrió en los últimos meses.

Estas métricas son útiles para identificar artículos que históricamente se movieron, pero que podrían estar perdiendo relevancia.

---

## Variables iniciales recomendadas

Para una primera etapa de clusterización, se recomienda iniciar con un conjunto controlado de variables que describan el comportamiento de venta sin sobrecargar el modelo.

Variables sugeridas:

* `total_unidades_vendidas_24m`
* `promedio_venta_mensual_24m`
* `meses_con_venta_24m`
* `frecuencia_venta_24m_pct`
* `porcentaje_meses_sin_venta_24m`
* `coeficiente_variacion_venta_24m`
* `max_meses_consecutivos_sin_venta`
* `meses_desde_ultima_venta`
* `variacion_venta_6m_vs_6m_previos_pct`
* `pendiente_tendencia_24m`

Este conjunto permite capturar las principales dimensiones del comportamiento histórico: volumen, frecuencia, intermitencia, variabilidad, recencia y tendencia.

---

## Justificación de las variables seleccionadas

Las variables seleccionadas no se basan únicamente en el volumen total vendido, ya que un artículo puede vender muchas unidades en pocos eventos aislados o pocas unidades de manera constante. Por esta razón, el análisis debe considerar tanto la cantidad vendida como la frecuencia, regularidad y variabilidad de la demanda.

La clusterización basada en estas métricas permitirá separar artículos con comportamientos distintos, por ejemplo:

* Artículos de alta rotación y demanda estable.
* Artículos de venta frecuente pero variable.
* Artículos de baja rotación con demanda repetitiva.
* Artículos de demanda intermitente.
* Artículos con posible estacionalidad.
* Artículos con señales recientes de crecimiento o caída.

Esta clasificación es fundamental para seleccionar posteriormente el modelo de forecast más adecuado para cada grupo.

---

## Modelos de clusterización a evaluar

Para agrupar los artículos se podrán comparar distintos algoritmos de aprendizaje no supervisado, entre ellos:

* `K-Means`: útil para formar grupos compactos y comparables.
* `Gaussian Mixture Models`: permite asignaciones probabilísticas a cada cluster.
* `Agglomerative Clustering`: útil para explorar estructuras jerárquicas.
* `DBSCAN`: útil para detectar artículos atípicos o comportamientos fuera de patrón.

Inicialmente se recomienda utilizar `K-Means` como modelo base por su facilidad de interpretación y eficiencia computacional. Posteriormente, los resultados podrán compararse con otros métodos para validar si existe una estructura de agrupamiento más adecuada.

---

## Evaluación de la calidad de los clusters

La calidad de los clusters será evaluada mediante métricas internas y análisis de interpretación de negocio.

Métricas recomendadas:

* `Silhouette Score`: mide qué tan bien separado está cada cluster.
* `Davies-Bouldin Index`: evalúa la separación y compactación de los grupos.
* `Calinski-Harabasz Index`: mide la relación entre dispersión interna y separación externa.
* Método del codo para definir número óptimo de clusters.
* Análisis visual mediante PCA o reducción de dimensionalidad.

Además de las métricas matemáticas, será necesario interpretar los clusters desde el punto de vista del negocio. Un buen cluster no solo debe ser estadísticamente válido, sino también útil para tomar decisiones de reabastecimiento.

---

## Interpretación esperada de los clusters

Después de aplicar la clusterización, cada grupo deberá ser interpretado de acuerdo con las características promedio de sus artículos. Por ejemplo:

* Cluster 1: demanda frecuente y estable.
* Cluster 2: demanda frecuente pero altamente variable.
* Cluster 3: demanda intermitente.
* Cluster 4: baja rotación con ventas ocasionales.
* Cluster 5: posible comportamiento estacional.
* Cluster 6: artículos con tendencia reciente creciente o decreciente.

Esta interpretación permitirá asignar familias de modelos de forecast más adecuadas para cada grupo.

---

## Comparación de modelos por cluster

Una vez definidos los clusters, se procederá a comparar distintos modelos de predicción dentro de cada grupo. Esto permitirá identificar el modelo con mejor desempeño para cada tipo de comportamiento de demanda.

Modelos candidatos:

* Naive Forecast.
* Moving Average.
* Seasonal Naive.
* ETS / Exponential Smoothing.
* AutoARIMA.
* Croston.
* SBA.
* TSB.
* Prophet.
* XGBoost o LightGBM.

La comparación se realizará por cluster y no necesariamente por artículo individual, con el objetivo de mejorar la eficiencia del proceso y establecer una lógica escalable para la herramienta.

---

## Métricas para seleccionar el modelo ganador

Para seleccionar el modelo ganador por cluster, se utilizará una evaluación multicriterio que considere precisión, sesgo e impacto operativo.

Métricas sugeridas:

* `WAPE`: error absoluto porcentual ponderado.
* `MAE`: error absoluto medio en unidades.
* `RMSE`: penalización de errores grandes.
* `Bias`: tendencia del modelo a sobreestimar o subestimar.
* `Tracking Signal`: detección de sesgo sistemático.
* Riesgo estimado de quiebre de stock.
* Exceso estimado de inventario.

El modelo ganador será aquel que ofrezca el mejor equilibrio entre precisión estadística y utilidad operativa para la toma de decisiones de reabastecimiento.

---

## Resultado esperado

El resultado esperado de esta etapa es obtener una clasificación de artículos en grupos homogéneos según su comportamiento histórico de venta. Cada cluster deberá contar con una descripción clara, una interpretación de negocio y una recomendación de modelos de forecast candidatos.

Posteriormente, la herramienta podrá utilizar esta clasificación para aplicar de forma más eficiente el modelo predictivo más adecuado a cada grupo, facilitando el cálculo de necesidades de reabastecimiento y la priorización de artículos para revisión semanal de stock.


