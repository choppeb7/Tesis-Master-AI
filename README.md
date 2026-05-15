# Herramienta de Predicción de Reabastecimiento de Repuestos Industriales

## Introducción

Este proyecto forma parte del Trabajo Fin de Máster en Inteligencia Artificial y tiene como objetivo desarrollar una herramienta de predicción de reabastecimiento para inventarios de repuestos industriales, utilizando técnicas de análisis de datos, series temporales, clusterización y modelos predictivos.

El contexto del proyecto parte de una problemática común en empresas distribuidoras de repuestos industriales: la dificultad de definir niveles adecuados de inventario debido a la variabilidad en el comportamiento de la demanda. A diferencia de productos de consumo masivo, los repuestos industriales no necesariamente presentan ventas constantes o patrones de demanda fácilmente predecibles. Muchos artículos son altamente especializados, pertenecen a distintos fabricantes, tienen diferentes lead times, diferentes niveles de rotación y pueden presentar ventas esporádicas o intermitentes.

Por esta razón, el proyecto no se limita únicamente a aplicar un algoritmo de predicción sobre todo el inventario. En su lugar, busca primero analizar, clasificar y agrupar los repuestos según sus características comerciales, históricas y temporales, con el objetivo de encontrar modelos de predicción más adecuados para cada grupo de productos.

## Objetivo del Proyecto

El objetivo principal es construir una herramienta que permita estimar necesidades futuras de reabastecimiento de repuestos industriales a partir del análisis histórico de ventas y comportamiento del inventario.

La herramienta busca apoyar la toma de decisiones en procesos de compra, planificación de inventario y gestión de abastecimiento, reduciendo el riesgo de quiebres de stock, sobreinventario y obsolescencia.

## Contexto del Problema

La gestión de inventarios de repuestos industriales presenta retos particulares:

- Algunos repuestos tienen demanda constante.
- Otros presentan ventas esporádicas o intermitentes.
- Existen artículos críticos con baja rotación, pero alto impacto operativo.
- Los lead times pueden variar considerablemente según fabricante, proveedor o país de origen.
- La estacionalidad puede estar presente en ciertos grupos de productos, pero no necesariamente en todo el inventario.
- El promedio de venta anual puede no representar correctamente el comportamiento real de ciertos repuestos.
- Algunos productos pueden tener historial limitado o comportamientos atípicos.

Debido a estas condiciones, aplicar un único modelo de predicción para todos los artículos podría generar resultados poco confiables. Por ello, el proyecto plantea una estrategia basada en segmentación previa del inventario.

## Enfoque Metodológico

El proyecto propone una metodología en varias etapas:

### 1. Análisis exploratorio de datos

Se realizará un análisis inicial del historial de ventas de los repuestos industriales para identificar patrones, valores atípicos, comportamiento temporal, rotación, frecuencia de venta y características relevantes para la predicción.

### 2. Preparación y limpieza de datos

Se procesarán los datos históricos con el objetivo de estructurarlos adecuadamente para el análisis. Esta etapa puede incluir:

- Limpieza de registros inconsistentes.
- Tratamiento de valores nulos.
- Normalización de variables.
- Consolidación de ventas por período.
- Cálculo de métricas de rotación.
- Cálculo de promedios de venta.
- Identificación de artículos con comportamiento irregular.

### 3. Clasificación y clusterización de repuestos

Debido a que los repuestos industriales pueden tener comportamientos muy distintos entre sí, se buscará agruparlos según características como:

- Historial de ventas.
- Frecuencia de venta.
- Volumen promedio de demanda.
- Variabilidad de la demanda.
- Lead time.
- Estacionalidad.
- Fabricante o familia de producto.
- Nivel de rotación.
- Comportamiento de la serie temporal.

El objetivo de esta etapa es identificar grupos de artículos con patrones similares, permitiendo posteriormente seleccionar modelos de predicción más adecuados para cada tipo de comportamiento.

### 4. Modelado predictivo

Una vez definidos los grupos de repuestos, se evaluarán distintos algoritmos de predicción para determinar cuál se adapta mejor a cada segmento.

El proyecto no busca asumir que existe un único algoritmo óptimo para todo el inventario. En cambio, se analizará el desempeño de diferentes modelos según las características de cada grupo.

Algunos modelos que podrían evaluarse incluyen:

- Modelos estadísticos de series temporales.
- Modelos basados en machine learning.
- Modelos específicos para demanda intermitente.
- Modelos de regresión.
- Modelos comparativos de referencia o baseline.

### 5. Evaluación de resultados

Los modelos serán evaluados utilizando métricas de error y desempeño predictivo, con el objetivo de seleccionar la mejor alternativa para cada grupo de repuestos.

La evaluación permitirá comparar el desempeño de los modelos y determinar qué algoritmo presenta mejores métricas para cada tipo de comportamiento de demanda.

## Alcance del Proyecto

El alcance inicial del proyecto contempla:

- Analizar el historial de ventas de repuestos industriales.
- Identificar patrones de comportamiento en la demanda.
- Agrupar artículos con características similares.
- Evaluar diferentes algoritmos de predicción.
- Determinar qué modelo se adapta mejor a cada grupo.
- Generar una base metodológica para una herramienta de apoyo al reabastecimiento.

## Valor del Proyecto

Este proyecto busca aportar valor a la gestión de inventarios industriales mediante el uso de inteligencia artificial y análisis de datos.

Entre los beneficios esperados se encuentran:

- Mejor planificación de compras.
- Reducción de quiebres de inventario.
- Disminución de exceso de stock.
- Mejor identificación de artículos críticos.
- Mayor entendimiento del comportamiento de la demanda.
- Apoyo en la toma de decisiones de reabastecimiento.
- Segmentación inteligente del inventario según comportamiento real.

## Motivación

La motivación principal de este proyecto nace de la necesidad de aplicar técnicas de inteligencia artificial a un problema real de negocio dentro del sector industrial.

En empresas distribuidoras de repuestos, la planificación de inventario suele depender de criterios generales, experiencia comercial o promedios históricos. Sin embargo, estos métodos pueden no ser suficientes cuando los artículos presentan comportamientos altamente variables.

Este proyecto busca combinar conocimiento del negocio con herramientas de análisis avanzado para desarrollar una solución más robusta, adaptable y basada en datos.

## Estado del Proyecto

Actualmente, el proyecto se encuentra en fase de desarrollo como parte del Trabajo Fin de Máster en Inteligencia Artificial.

Las etapas principales incluyen:

- Definición del problema.
- Análisis del historial de ventas.
- Preparación de datos.
- Diseño de variables relevantes.
- Clusterización de repuestos.
- Evaluación de algoritmos predictivos.
- Comparación de métricas.
- Documentación de resultados.

## Tecnologías y Herramientas

Las tecnologías utilizadas o consideradas para el desarrollo del proyecto incluyen:

- Python
- Pandas
- NumPy
- Scikit-learn
- Matplotlib
- Seaborn
- Modelos de series temporales
- Algoritmos de clusterización
- Técnicas de machine learning

## Resultado Esperado

El resultado esperado es una herramienta analítica capaz de apoyar la toma de decisiones de reabastecimiento, clasificando los repuestos industriales según su comportamiento y recomendando modelos de predicción adecuados para cada grupo.

La finalidad no es únicamente generar una predicción numérica, sino construir una metodología que permita entender mejor el comportamiento del inventario y mejorar la precisión de las decisiones de compra.

## Autor

Proyecto desarrollado por Christian Hoppe como parte del Trabajo Fin de Máster en Inteligencia Artificial.

## Licencia

Este repositorio ha sido desarrollado con fines académicos y de investigación aplicada.