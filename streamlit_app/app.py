from pathlib import Path
import sys

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st



# ============================================================
# DEFINIR RUTAS DEL PROYECTO
# ============================================================

# app.py está en:
# Tesis-Master-AI/streamlit_app/app.py

# PROJECT_ROOT apunta a:
# Tesis-Master-AI/
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# FORECAST_APP_DIR apunta a:
# Tesis-Master-AI/forecast_app/
FORECAST_APP_DIR = PROJECT_ROOT / "forecast_app"

# Agregar forecast_app al path para poder importar pipeline
if str(FORECAST_APP_DIR) not in sys.path:
    sys.path.insert(0, str(FORECAST_APP_DIR))

# ============================================================
# RUTA DEL EXCEL
# ============================================================
from datetime import datetime

fecha_hoy = datetime.today().strftime("%Y-%m-%d")

ruta_excel_default = (
    FORECAST_APP_DIR
    / "data"
    / "input"
    / "df_matriz_ventas_articulos_forecast.xlsx"
)

ruta_excel_output_default = (
    FORECAST_APP_DIR
    / "data"
    / "output"
    / f"df_matriz_ventas_articulos_con_forecast_{fecha_hoy}.xlsx"
)


# ============================================================
# IMPORTAR PIPELINE
# ============================================================
# Ahora Python sí puede encontrar:
# forecast_app/pipeline/main_pipeline.py
# ============================================================

from pipeline.main_pipeline import ejecutar_pipeline_forecast


# ============================================================
# CONFIGURACIÓN DE LA APP
# ============================================================

st.set_page_config(
    page_title="Consulta CEROSA",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Prueba local - Modelo AI basado en Statsforecast para reabastecimiento articulos CEROSA")
#st.write("Esta app prueba la conexión con PostgreSQL en Render.")


# ============================================================
# CONEXIÓN A POSTGRESQL
# ============================================================

@st.cache_data(show_spinner=True, show_time=True, ttl=3600)
def correr_pipeline_cacheado(ruta_excel, meses_evaluacion, meses_forecast_futuro, ventana_dummy, ruta_exportacion):
    return ejecutar_pipeline_forecast(
        ruta_excel=ruta_excel,
        meses_evaluacion=meses_evaluacion,
        meses_forecast_futuro=meses_forecast_futuro,
        ventana_dummy=ventana_dummy,
        ruta_exportacion=ruta_exportacion
    )


def main(): 

    # ------------------------------------------------------------
    # Inicializar session_state
    # ------------------------------------------------------------
    # Esto permite guardar los resultados del pipeline después de presionar
    # el botón. Si no lo haces, los resultados podrían perderse en cada rerun.
    # ------------------------------------------------------------
    if ruta_excel_default is None:
        st.error("No se encontró el archivo Excel de entrada. Por favor, verifica la ruta.")
        st.stop()
    else:
        st.session_state["ruta_excel_default"] = ruta_excel_default
        st.success("Archivo Excel de entrada encontrado.")

    if ruta_excel_output_default is None:
            st.error("No se encontró la ruta de salida del archivo Excel a calcular Por favor, verifica la ruta.")
            st.stop()
    else:
        st.session_state["ruta_excel_output_default"] = ruta_excel_output_default
        st.success("Archivo Excel de salida encontrado.")

    if "resultados_pipeline" not in st.session_state:
        st.session_state["resultados_pipeline"] = None

    if "pipeline_ejecutado" not in st.session_state:
        st.session_state["pipeline_ejecutado"] = False


    with st.sidebar.form("form_pipeline"):
        st.header("Definir parametros de entrada para el pipeline")
        #ruta_excel= st.text_input("Ruta archivo Excel", value=str(ruta_excel_default))
        meses_evaluacion=st.slider("Meses de evaluación", min_value=1, max_value=24, value=6)
        meses_forecast_futuro=st.slider("Cantidad de Meses a predecir", min_value=1, max_value=12, value=6)
        ventana_dummy=st.slider("Intervalo de entrenamiento modelo dummy", min_value=1, max_value=24, value=12)

        ejecutar=st.form_submit_button("Ejecutar pipeline forecast")

        if ejecutar:
            #ruta_excel="./Datos/df_matriz_ventas_articulos_forecast.xlsx"
            st.write(f"Ejecutando pipeline con los siguientes parámetros:\n- Ruta Excel: {st.session_state['ruta_excel_default']}\n- Meses evaluación: {meses_evaluacion}\n- Meses forecast futuro: {meses_forecast_futuro}\n- Ventana dummy: {ventana_dummy}")
            resultados_pipeline = correr_pipeline_cacheado(
                ruta_excel=st.session_state["ruta_excel_default"],
                meses_evaluacion=meses_evaluacion,
                meses_forecast_futuro=meses_forecast_futuro,
                ventana_dummy=ventana_dummy,
                ruta_exportacion=st.session_state["ruta_excel_output_default"]
            )
            st.session_state["resultados_pipeline"] = resultados_pipeline
            st.session_state["pipeline_ejecutado"] = True
            st.success("Pipeline ejecutado correctamente✅. Resultados obtenidos:")
    # ============================================================
    # Recuperar resultados del pipeline si ya se ejecutó o detener la app aqui
    # ============================================================

    resultados_pipeline=st.session_state.get("resultados_pipeline", None)

    if resultados_pipeline is None:
        st.warning("El pipeline aún no se ha ejecutado. Por favor, define los parámetros y haz clic en 'Ejecutar pipeline forecast' en la barra lateral.")
        st.stop()

    # ============================================================
    # EXTRAER DATAFRAMES DEL PIPELINE
    # ============================================================

    df_resultado_kpi = resultados_pipeline["df_resultado_final"].copy()
    df_best_model_kpi = resultados_pipeline["df_best_model"].copy()

    # ============================================================
    # TABS PARA VISUALIZAR RESULTADOS
    # ============================================================2

    tab1, tab2, tab3, tab4, tab5, tab6=st.tabs([
    "Resumen distribución modelos ganadores",
    "Top 10 articulos con menor error de predicción",
    "Top 10 articulos con mayor error de predicción",
    "distribución de Wape_ranking",
    "distribucion sesgo por modelo ganador",
    "distribucion modelos ganadores por cluster de ventas"])

    # ============================================================
    # TAB 1: RESUMEN DISTRIBUCIÓN MODELOS GANADORES
    # ============================================================
    with tab1: 
        st.header("Resumen Resultados del pipeline forecast")
        df_resultado_kpi = resultados_pipeline["df_resultado_final"].copy()
        df_resultado_kpi=df_resultado_kpi.rename(columns={"codigo_articulo":"unique_id"})
        df_best_model_kpi = resultados_pipeline["df_best_model"].copy()
        st.dataframe(df_resultado_kpi, use_container_width=True, hide_index=True)
        st.dataframe(df_best_model_kpi, use_container_width=True, hide_index=True)

        st.subheader("Resumen distribución modelos ganadores")

        #------------------------------------------------------------
        #KPI 1: artículos analizados
        #-----------------------------------------------------------
        articulos_analizados = df_resultado_kpi["unique_id"].nunique()

        # ------------------------------------------------------------
        # KPI 2: compra sugerida total
        # ------------------------------------------------------------
        compra_sugerida_total = df_resultado_kpi["compra_sugerida"].sum()
        # ------------------------------------------------------------
        # KPI 3: artículos con compra sugerida
        #----------------------------------------------------------------------
        articulos_con_compra_sugerida = df_resultado_kpi[df_resultado_kpi["compra_sugerida"] > 0]["unique_id"].nunique()
        porcentaje_articulos_con_compra = (articulos_con_compra_sugerida / articulos_analizados * 100
        if articulos_analizados > 0
        else 0
        )

        # ------------------------------------------------------------
        # KPI 4: WAPE mediano
        # ------------------------------------------------------------

        wape_limpio = (df_best_model_kpi["WAPE_ranking"].notna())
        wape_mediano = wape_limpio.median()

        # ------------------------------------------------------------
        # Regla sugerida:
        # - WAPE NaN
        # - WAPE infinito
        # - WAPE mayor a 150%
        #
        # Puedes ajustar este umbral según tu criterio.
        # ------------------------------------------------------------

        articulos_revision_manual = df_best_model_kpi[
            df_best_model_kpi["WAPE_ranking"].isna()
            #| np.isinf(df_best_model_kpi["WAPE_ranking"])
            | (df_best_model_kpi["WAPE_ranking"] > 150)
        ]["unique_id"].nunique()
        total_articulos_modelados = df_best_model_kpi["unique_id"].nunique()

        # ------------------------------------------------------------
        # KPI 5: Articulo con modelo especializados
        # ------------------------------------------------------------
        mask_dummy = (
        df_best_model_kpi["best_model"]
        .astype(str)
        .str.startswith("Dummy_promedio_")
        )

        articulos_dummy = df_best_model_kpi.loc[
        mask_dummy,
        "unique_id"
        ].nunique()

        articulos_modelos_especializados = total_articulos_modelados - articulos_dummy

        porcentaje_modelos_especializados = (
        articulos_modelos_especializados / total_articulos_modelados * 100
        if total_articulos_modelados > 0
        else 0
        )
        # ------------------------------------------------------------
        # Definir columnas para mostrar los KPIs
        # ------------------------------------------------------------
        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric("Artículos analizados",f"{articulos_analizados:,}")
        col2.metric("Compra sugerida total",f"{compra_sugerida_total:,}")
        col3.metric("Artículos con compra",f"{articulos_con_compra_sugerida:,}",delta=f"{porcentaje_articulos_con_compra:.1f}% del total")
        col4.metric("Modelos especializados",f"{articulos_modelos_especializados:,}",delta=f"{porcentaje_modelos_especializados:.1f}% del total")

        # ------------------------------------------------------------
        # Distribución de modelos ganadores
        # ------------------------------------------------------------
        st.subheader("Graficas: Distribución de modelos ganadores")

        conteo_modelos=(
            df_best_model_kpi["best_model"]
            .value_counts()
            .reset_index()
        )

        conteo_modelos.columns=["Modelo", "Cantidad de artículos"]

        conteo_modelos["Porcentaje"] = (
            conteo_modelos["Cantidad de artículos"] / conteo_modelos["Cantidad de artículos"].sum() * 100 )

        col_graf1, col_graf2=st.columns(2)  

        with col_graf1:
            st.markdown("### Cantidad de artículos por modelo ganador")
            st.bar_chart(
                conteo_modelos,
                x="Modelo",
                y="Cantidad de artículos",
                use_container_width=True
            )
        with col_graf2:
            st.markdown("### Porcentaje de artículos por modelo ganador")
            fig_pie=px.pie(
                conteo_modelos,
                names="Modelo",
                values="Porcentaje"
                #use_container_width=True
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        # ============================================================
        # TABS PENDIENTES
        # ============================================================
        # De momento dejamos los otros tabs con mensajes placeholder.
        # Esto permite probar la app sin que falle por secciones incompletas.
        # ============================================================
    with tab2:
        st.info("Pendiente: Top 10 artículos, menor error de predicción.")
        df_top_10_menor_error = (
            df_best_model_kpi
            .sort_values(by=["WAPE_ranking", "bias_total_abs_periodo_evaluacion", "RMSE", "MAE"], ascending=[True, True, True, True])
            .head(10)
        )
        st.dataframe(df_top_10_menor_error, use_container_width=True, hide_index=True)

    with tab3:
        st.info("Pendiente: Top 10 artículos con mayor error de predicción.")
        df_worst_10_mayor_error = (
            df_best_model_kpi
            .sort_values(by=["WAPE_ranking", "bias_total_abs_periodo_evaluacion", "RMSE", "MAE"], ascending=[True, True, True, True])
            .tail(10)
            .sort_values(by=["WAPE_ranking", "bias_total_abs_periodo_evaluacion", "RMSE", "MAE"], ascending=[False, False, False, False])
        )
        st.dataframe(df_worst_10_mayor_error, use_container_width=True, hide_index=True)

    with tab4:
        st.info("Pendiente: distribución de WAPE_ranking.")
        df_distribucion_wape = df_best_model_kpi[["unique_id", "WAPE_ranking"]].copy()
        df_distribucion_wape["WAPE_ranking"] = pd.to_numeric(df_distribucion_wape["WAPE_ranking"], errors="coerce")##Transformar a nan
        cantidad_articulos_WAPE_infinito = df_distribucion_wape["WAPE_ranking"].isin([np.inf, -np.inf]).sum()
        porcentaje_articulos_WAPE_infinito = (cantidad_articulos_WAPE_infinito / len(df_distribucion_wape) * 100)
        st.write(f"Cantidad de artículos con WAPE_ranking infinito: {cantidad_articulos_WAPE_infinito} que representa el {porcentaje_articulos_WAPE_infinito:.2f}% del total de artículos.")

        articulos_total = df_distribucion_wape["unique_id"].nunique()
        df_distribucion_wape["WAPE_ranking"] = df_distribucion_wape["WAPE_ranking"].replace([np.inf, -np.inf], np.nan)
        df_distribucion_wape_limpio = df_distribucion_wape.dropna(subset=["WAPE_ranking"]).copy()
        articulos_wape_valido = df_distribucion_wape_limpio["unique_id"].nunique()

        articulos_wape_revision = articulos_total - articulos_wape_valido

        col1, col2, col3 = st.columns(3)

        col1.metric(
        "Artículos modelados",
        f"{articulos_total:,}"
        )

        col2.metric(
        "Artículos con WAPE válido",
        f"{articulos_wape_valido:,}"
        )

        col3.metric(
        "Artículos sin WAPE graficable",
        f"{articulos_wape_revision:,}"
         )

        st.write(f"datatype  {df_distribucion_wape_limpio['WAPE_ranking'].dtype}")
        st.dataframe(df_distribucion_wape_limpio.sort_values(by="WAPE_ranking"), use_container_width=True, hide_index=True)

        #df_distribucion_wape = pd.DataFrame(df_distribucion_wape_limpio, columns=["unique_id", "WAPE_ranking"])
        #st.area_chart(df_distribucion_wape)

    # ============================================================
    # 3. Slider para limitar outliers visuales
    # ============================================================
    # Muchos WAPE pueden ser muy altos y deformar el histograma.
    # Este cap no elimina artículos, solo limita la visualización.
    # ============================================================

        limite_visual_max_wape = st.slider(
        "Límite visual máximo de WAPE para el histograma",
        min_value=10,
        max_value=150,
        value=150,
        step=10
        )

        df_distribucion_wape_limpio["WAPE_ranking_visual"] = df_distribucion_wape_limpio["WAPE_ranking"].clip(
        upper=limite_visual_max_wape
        )
    # ============================================================
    # 4. Histograma de WAPE_ranking
    # ============================================================

        fig_wape=px.histogram(
            df_distribucion_wape_limpio,
            x="WAPE_ranking_visual",
            nbins=30,
            marginal="box",
            title=f"Histograma de WAPE_ranking (limitado a {limite_visual_max_wape})",
            labels={"WAPE_ranking_visual": "WAPE_ranking (%)",
                    "count": "Cantidad de artículos"    },
            color_discrete_sequence=["#636EFA"]
        )
        fig_wape.add_vline(
            x=df_distribucion_wape_limpio["WAPE_ranking_visual"].median(),
            line_dash="dash",
            line_color="red",
            annotation_text=f"Mediana: {df_distribucion_wape_limpio['WAPE_ranking_visual'].median():.2f}",
            annotation_position="top right"
        )

        fig_wape.add_vline(
            x=df_distribucion_wape_limpio["WAPE_ranking_visual"].mean(),
            line_dash="dot",
            line_color="green",
            annotation_text=f"Media: {df_distribucion_wape_limpio['WAPE_ranking_visual'].mean():.2f}",
            annotation_position="top left"
        )

        fig_wape.add_vline(
            x=50,
            line_dash="solid",
            line_color="orange",
            annotation_text="Umbral: 50%",
            annotation_position="top right"
        )

        fig_wape.add_vline(
            x=100,
            line_dash="solid",
            line_color="orange",
            annotation_text="Umbral: 100%",
            annotation_position="top right"
        )

        st.plotly_chart(fig_wape, use_container_width=True)

        st.caption(
        f"Nota: valores mayores a {limite_visual_max_wape}% se muestran agrupados visualmente "
        f"en el límite superior para evitar que los outliers distorsionen la gráfica."
    )   
    # ============================================================
    # 5. Categorizar WAPE para interpretación ejecutiva
    # ============================================================

        bins_wape=[0, 25,50,100,150, np.inf]

        orden_categorias_wape=[
        "0% - 25% | Muy bueno",
        "25% - 50% | Aceptable",
        "50% - 100% | Alto",
        "100% - 150% | Muy alto",
        ">150% | Revisión manual"
        ]
        df_distribucion_wape_limpio["WAPE_categoria"] = pd.cut(
        df_distribucion_wape_limpio["WAPE_ranking"],
        bins=bins_wape,
        labels=orden_categorias_wape
        )

        resumen_wape=(
        df_distribucion_wape_limpio["WAPE_categoria"]
        .value_counts()
        .reindex(orden_categorias_wape)
        .reset_index()
        )
    # Asegurar que la categoría respete el orden lógico
        resumen_wape["WAPE_categoria"] = pd.Categorical(
        resumen_wape["WAPE_categoria"],
        categories=orden_categorias_wape,
        ordered=True
        )
        resumen_wape.columns=["Rango WAPE", "Cantidad de artículos"]

        resumen_wape["Porcentaje(%)"] = (
            round(resumen_wape["Cantidad de artículos"] / resumen_wape["Cantidad de artículos"].sum() * 100, 2)
        )
        st.markdown("### Resumen de artículos por categoría de WAPE")
        st.dataframe(resumen_wape, use_container_width=True, hide_index=True)

        # ============================================================
        # 6. Gráfico de barras por categoría
        # ============================================================
        colores_wape = {
        "0% - 25% | Muy bueno": "#2E7D32",          # Verde
        "25% - 50% | Aceptable": "#8BC34A",        # Verde claro
        "50% - 100% | Alto": "#FFC107",            # Amarillo
        "100% - 150% | Muy alto": "#FF9800",       # Naranja
        ">150% | Revisión manual": "#C62828"       # Rojo
        }

        fig_wape_categoria=px.bar(resumen_wape,
            x="Rango WAPE",
            y="Cantidad de artículos",
            color="Rango WAPE",
            color_discrete_map=colores_wape,
            #text="Porcentaje",
            #labels={"Cantidad de artículos": "Cantidad de artículos"},
            title="Distribución de artículos por categoría WAPE",
        )

        st.plotly_chart(
        fig_wape_categoria,
        use_container_width=True
        )

        st.markdown("### Porcentaje de artículos por modelo ganador")
        fig_pie=px.pie(
        resumen_wape,
        names="Rango WAPE",
        color="Rango WAPE",
        color_discrete_map=colores_wape,
        values="Porcentaje(%)"
        #use_container_width=True
                    )
        st.plotly_chart(fig_pie, use_container_width=True)

    with tab5:
        
        st.header("Distribucion Error absoluto total durante el periodo de evaluación")
        st.info("Este análisis compara el WAPE_ranking contra el error absoluto total del período de evaluación para identificar qué artículos presentan errores mensuales altos y cuáles realmente generan desviaciones relevantes a nivel de cobertura total del intervalo. " \
        "Para evitar que outliers extremos amplíen excesivamente las escalas y oculten las tendencias de la mayoría de los datos, se recomienda definir límites visuales mediante percentiles tanto para WAPE_ranking como para el error absoluto total.")

        df_bias_total = df_best_model_kpi[["unique_id", "bias_total_abs_periodo_evaluacion", "WAPE_ranking","sesgo"]].copy()

        df_bias_total["bias_total_abs_periodo_evaluacion"] = pd.to_numeric(df_bias_total["bias_total_abs_periodo_evaluacion"], errors="coerce")

        df_bias_total=df_bias_total.dropna(subset=["bias_total_abs_periodo_evaluacion"]).copy()
        st.warning("Con el siguiente slider puedes ajustar visualmente el limite superior del error absoluto total (por percentil)")
        bias_total_limite_max=st.slider("Percentil limite superior:", min_value=0.7, max_value=0.99, step=0.05, value=0.80)
        limite_inferior=df_bias_total["bias_total_abs_periodo_evaluacion"].quantile(0.01)
        limite_superior=df_bias_total["bias_total_abs_periodo_evaluacion"].quantile(bias_total_limite_max)
        df_bias_total["bias_visual"] = df_bias_total["bias_total_abs_periodo_evaluacion"].clip(lower=limite_inferior, upper=limite_superior)

        color_bias_map = {
            "Sobrepronóstico": "#0E71F1",  # azul
            "Subpronóstico": "#F10E0E",    # rojo
            "Exacto": "#0EF1A3"            # verde
        }

        fig_bias=px.histogram(
            df_bias_total,
            x="bias_visual",
            nbins=80,
            color="sesgo",
            color_discrete_map=color_bias_map,
            title=f"Distribución del Error absoluto total, limitada por percentiles 1% - {bias_total_limite_max*100}%",
            labels={"bias_total_abs_periodo_evaluacion": "error absoluto total del periodo de evaluación",
                    "sesgo": "Tipo de sesgo"
                    }
            )
        

        fig_bias.add_vline(
            x=0,
            line_dash="dash",
            annotation_text="Predicción exacta",
            line_color="green",
    
        )

        fig_bias.add_vline(
            x=df_bias_total["bias_visual"].median(),
            line_dash="dash",
            annotation_text="Mediana visual del error absoluto total",
            line_color="green"
        )

        fig_bias.add_vline(
        x=df_bias_total["bias_visual"].quantile(0.85),
        line_dash="dash",
        annotation_text="Percentil 80 visual del error absoluto total",
        line_color="red"
        )
        
        fig_bias.update_layout(
        xaxis_title="Error absoluto total",
        yaxis_title="Cantidad",
        legend_title="Tipo de sesgo"
        )


        st.plotly_chart(fig_bias, use_container_width=True)


        st.caption(f"La gráfica limita visualmente el error absoluto total entre "f"{limite_inferior:.1f} y {limite_superior:.1f} unidades. "
        "Los outliers no se eliminan del dataframe original.")

        #df_bias_abs=df_best_model_kpi.copy()

        #df_bias_total["bias_total_abs_periodo_evaluacion"] = df_bias_abs["bias_total_abs_periodo_evaluacion"].clip(lower=limite_inferior, upper=limite_superior)

        #st.caption(f"La gráfica limita visualmente el error absoluto total entre "f"{limite_inferior:.1f} y {limite_superior:.1f} unidades. "
        #"Los outliers no se eliminan del dataframe original."
        #)
        st.subheader("Relación entre Wape y Error absoluto total")
        st.warning("Omitimos en este analisis WAPE_ranking=Infinito")

        #df_calidad=df_best_model_kpi.copy()
        #st.write(df_bias_total.info())

        df_bias_total["WAPE_ranking"]=pd.to_numeric(df_bias_total["WAPE_ranking"], errors="coerce")
        df_bias_total["WAPE_ranking"] = df_bias_total["WAPE_ranking"].replace([np.inf, -np.inf], np.nan)
        #df_calidad["revision_manual"]=df_calidad["WAPE_Ranking"].isna() |df_calidad["WAPE_Ranking"].isin([float("inf"), float("-inf")])
        df_bias_total=df_bias_total.dropna(subset=[
            "WAPE_ranking",
            "bias_total_abs_periodo_evaluacion"
        ]).copy()
        valores_NaN=df_bias_total["WAPE_ranking"].isna().sum()
        
        st.write(f"Comprobamos Dataframe no contenga valores nulos o infinitos en WAPE_ranking. La cantidad de valores igual a NaN es igual a {valores_NaN}")
        st.dataframe(df_bias_total.sort_values(by="bias_visual", ascending=True), use_container_width=True)
        #df_bias_total["bias_total_abs_periodo_evaluacion"]=pd.to_numeric(df_calidad["bias_total_abs_periodo_evaluacion"], errors="coerce")
        st.write("Definir quantile limite superior")
        x=st.slider("Cuantile para limite superior", min_value=0.7, max_value=0.99, step=0.05, value=0.85)
        limite_inferior=df_bias_total["WAPE_ranking"].quantile(0.01)
        limite_superior=df_bias_total["WAPE_ranking"].quantile(x)
        df_bias_total["Wape_winsorizado"] = df_bias_total["bias_total_abs_periodo_evaluacion"].clip(lower=limite_inferior, upper=limite_superior)

        fig_scatter=px.scatter(
            df_bias_total, 
            x="Wape_winsorizado",
            y="bias_visual",
            #color="best_model",
            hover_data=[
                "unique_id",
                #"best_model",
                "Wape_winsorizado",
                "bias_visual",
                "sesgo"
            ],
            title="WAPE Vs. error absoluto total del periodo",
            labels={
                "Wape_winsorizado": "Wape ranking (%)",
                "bias_visual": "Erorr abs. total en periodo de eval.",
                #"best_model": "modelo ganador"
            }
        )

        fig_scatter.add_vline(
        x=100,
        line_dash="dash",
        annotation_text="WAPE 100%"
        )

        st.plotly_chart(
        fig_scatter,
        use_container_width=True
        )
            





    with tab6:
        st.info("Pendiente: distribución de modelos ganadores por cluster de ventas.")
#============================================================
# 3. Preparar dataframe base artículo + cluster
#============================================================
# Tomamos una sola fila por artículo para evitar duplicados.
#============================================================

        df_articulo_cluster = (
        df_resultado_kpi[
            ["unique_id", "cluster_kmeans_final", "descripcion_cluster"]
        ]
        .drop_duplicates()
        .copy()
        )
    # ============================================================
    # 4. Preparar dataframe de modelos ganadores
    # ============================================================

        df_modelo_ganador = (
        df_best_model_kpi[
            ["unique_id", "best_model"]
        ]
        .drop_duplicates()
        .copy()
        )

#============================================================
# 5. Unir modelo ganador con cluster
#============================================================

        df_modelo_cluster = df_modelo_ganador.merge(
        df_articulo_cluster,
        on="unique_id",
        how="left",
        validate="one_to_one"
        )

        #Eliminar articulos sin cluster asignado
        df_modelo_cluster = df_modelo_cluster.dropna(subset=["cluster_kmeans_final"]).copy()

        #Convertir cluster a texto para que plotly lo interprete como categoría
        df_modelo_cluster["cluster_kmeans_final"] = df_modelo_cluster["cluster_kmeans_final"].astype(str)

        #resumen_modelo_clusterdf_modelo_cluster.groupby(["cluster_kmeans_final", "descripcion_cluster"])
        st.dataframe(df_modelo_cluster, use_container_width=True, hide_index=True)

# ============================================================
# 6. Crear tabla de conteo modelo ganador por cluster
# ============================================================

        resumen_modelo_cluster = (
        df_modelo_cluster
        .groupby(["cluster_kmeans_final", "best_model"])
        .size()
        .reset_index(name="Cantidad de artículos")
        )
        #st.dataframe(resumen_modelo_cluster, use_container_width=True, hide_index=True)

        resumen_modelo_cluster["Total cluster"] = (
        resumen_modelo_cluster
        .groupby("cluster_kmeans_final")["Cantidad de artículos"]
        .transform("sum")
        )
        #st.dataframe(resumen_modelo_cluster, use_container_width=True, hide_index=True)

        resumen_modelo_cluster["Porcentaje dentro del cluster"] = (
        resumen_modelo_cluster["Cantidad de artículos"]
        / resumen_modelo_cluster["Total cluster"]
        * 100
        )

        resumen_modelo_cluster["Porcentaje texto"] = (
        resumen_modelo_cluster["Porcentaje dentro del cluster"]
        .round(1)
        .astype(str)
        + "%"
        )
# ============================================================
# 8. KPIs rápidos del tab
# ============================================================
        total_articulos_con_cluster=df_modelo_cluster["unique_id"].nunique()
        total_clusters=df_modelo_cluster["cluster_kmeans_final"].nunique()
        total_modelos_ganadores=df_modelo_cluster["best_model"].nunique()

        col1, col2, col3=st.columns(3)

        col1.metric("Total artículos con cluster",f"{total_articulos_con_cluster:,}")

        col2.metric("Total clusters",f"{total_clusters:,}")

        col3.metric("Total modelos ganadores",f"{total_modelos_ganadores:,}")

# ============================================================
# 9. Gráfico de barras apiladas por cantidad
# ============================================================

        st.markdown("### Gráfico de barras apiladas: cantidad de artículos por modelo y cluster")

        fig_barras_apiladas=px.bar(
            resumen_modelo_cluster,
            x="cluster_kmeans_final",
            y="Cantidad de artículos",
            color="best_model",
            text="Cantidad de artículos",
            labels={
                "cluster_kmeans_final": "Cluster",
                "Cantidad de artículos": "Cantidad de artículos",
                "best_model": "Modelo ganador"
            },
            title="Cantidad de artículos por modelo ganador y cluster",
        )

        fig_barras_apiladas.update_layout(
        barmode="stack",
        xaxis_title="Cluster de ventas",
        yaxis_title="Cantidad de artículos",
        legend_title="Modelo ganador"
        )

        fig_barras_apiladas.update_traces(
        textposition="inside"
        )

        st.plotly_chart(fig_barras_apiladas, use_container_width=True)
    # ============================================================
    # 10. Gráfico de barras apiladas porcentual
    # ============================================================
    # Este gráfico es más interpretativo, porque todos los clusters
    # quedan comparables en escala de 0% a 100%.
    # ============================================================
        st.markdown("### Distribución porcentual de modelos ganadores por cluster")

        fig_cluster_porcentual=px.bar(
            resumen_modelo_cluster,
            x="cluster_kmeans_final",
            y="Porcentaje dentro del cluster",
            color="best_model",
            text="Porcentaje texto",
            labels={
                "cluster_kmeans_final": "Cluster",
                "Porcentaje dentro del cluster": "Porcentaje de artículos",
                "best_model": "Modelo ganador"
            }
            )
        
        fig_cluster_porcentual.update_layout(
        barmode="stack",
        xaxis_title="Cluster de ventas",
        yaxis_title="Porcentaje dentro del cluster",
        legend_title="Modelo ganador",
        yaxis=dict(range=[0, 100])
        )

        fig_cluster_porcentual.update_traces(
        textposition="inside"
        )

        st.plotly_chart(fig_cluster_porcentual, use_container_width=True)

    # ============================================================
    # 11. Tabla resumen
    # ============================================================

        st.markdown("### Tabla resumen modelo ganador por cluster")

        tabla_resumen_modelo_cluster = resumen_modelo_cluster.sort_values(
        by=["cluster_kmeans_final", "Cantidad de artículos"],
        ascending=[True, False]
        )

        tabla_resumen_modelo_cluster["Porcentaje dentro del cluster"] = (
        tabla_resumen_modelo_cluster["Porcentaje dentro del cluster"]
        .round(1)
        )

        st.dataframe(
        tabla_resumen_modelo_cluster,
        use_container_width=True,
        hide_index=True
        )       

# ============================================================
# PUNTO DE ENTRADA DE LA APP
# ============================================================

if __name__ == "__main__":
    main()


# # ============================================================
# # PRUEBA DE CONEXIÓN
# # ============================================================

# try:
#     with engine.connect() as conn:
#         resultado = conn.execute(text("SELECT 1 AS prueba;"))
#         valor = resultado.scalar()

#     st.success(f"Conexión exitosa a PostgreSQL. Resultado prueba: {valor}")

# except Exception as e:
#     st.error("Error al conectar con PostgreSQL.")
#     st.exception(e)
#     st.stop()

# # ============================================================
# # CARGA CACHEADA DE DATA
# # ============================================================

# @st.cache_data(ttl=3600)
# def cargar_data():
#     query = """
#         SELECT *
#         FROM cerosa_analytics.oitm_ventas
#         WHERE marca_fabricante IS NOT NULL
#           AND marca_fabricante <> ''
#         ORDER BY marca_fabricante, codigo_articulo;
#     """

#     df = pd.read_sql(query, engine)

#     return df

# # ============================================================
# # FUNCIÓN PARA GENERAR EXCEL EN MEMORIA
# # ============================================================

# def convertir_df_a_excel(df):
#     output = BytesIO()

#     with pd.ExcelWriter(output, engine="openpyxl") as writer:
#         df.to_excel(writer, index=False, sheet_name="Datos")

#     output.seek(0)

#     return output


# # ============================================================
# # CARGAR DATA
# # ============================================================

# try:
#     df = cargar_data()

# except Exception as e:
#     st.error("Error cargando la data desde PostgreSQL.")
#     st.exception(e)
#     st.stop()


# # ============================================================
# # FILTRO INTERACTIVO POR MARCA
# # ============================================================

# marcas = sorted(df["marca_fabricante"].dropna().unique())

# opciones_marcas = ["Todas"] + marcas

# marca_seleccionada = st.selectbox(
#     "Selecciona una marca fabricante",
#     opciones_marcas
# )


# # ============================================================
# # FILTRADO LOCAL EN PANDAS
# # ============================================================

# if marca_seleccionada == "Todas":
#     df_filtrado = (
#         df.groupby("marca_fabricante", group_keys=False)
#           .head(10)
#           .reset_index(drop=True)
#     )

#     titulo = "Primeras 10 filas por cada fabricante"

# else:
#     df_filtrado = (
#         df[df["marca_fabricante"] == marca_seleccionada]
#         .head(10)
#         .reset_index(drop=True)
#     )

#     titulo = f"Primeras 10 filas de {marca_seleccionada}"


# # ============================================================
# # MOSTRAR RESULTADO
# # ============================================================

# st.subheader(titulo)

# st.write(f"Filas mostradas: {len(df_filtrado)}")

# st.dataframe(
#     df_filtrado,
#     use_container_width=True,
#     hide_index=True
# )


# # ============================================================
# # DESCARGA EN EXCEL
# # ============================================================

# excel_file = convertir_df_a_excel(df_filtrado)

# nombre_archivo = (
#     "primeras_10_filas_por_fabricante.xlsx"
#     if marca_seleccionada == "Todas"
#     else f"primeras_10_filas_{marca_seleccionada}.xlsx"
# )

# st.download_button(
#     label="Descargar Excel",
#     data=excel_file,
#     file_name=nombre_archivo,
#     mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
# )

# if __name__ == "__main__":
#         main()