import pandas as pd
import streamlit as st
from forecast_app.pipeline.main_pipeline import ejecutar_pipeline_forecast
from io import BytesIO
import numpy as np
import plotly.express as px

# ============================================================
# CONFIGURACIÓN DE LA APP
# ============================================================

st.set_page_config(
    page_title="Consulta CEROSA",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Prueba local - Modelo AI basado en Statsforecast para reabastecimiento articulos CEROSA")
st.write("Esta app prueba la conexión con PostgreSQL en Render.")


# ============================================================
# CONEXIÓN A POSTGRESQL
# ============================================================

@st.cache_data(show_spinner=True, show_time=True, ttl=3600)
def correr_pipeline_cacheado(ruta_excel, meses_evaluacion, meses_forecast_futuro, ventana_dummy):
    return ejecutar_pipeline_forecast(
        ruta_excel=ruta_excel,
        meses_evaluacion=meses_evaluacion,
        meses_forecast_futuro=meses_forecast_futuro,
        ventana_dummy=ventana_dummy
    )


def main(): 

    # ------------------------------------------------------------
    # Inicializar session_state
    # ------------------------------------------------------------
    # Esto permite guardar los resultados del pipeline después de presionar
    # el botón. Si no lo haces, los resultados podrían perderse en cada rerun.
    # ------------------------------------------------------------

    if "resultados_pipeline" not in st.session_state:
        st.session_state["resultados_pipeline"] = None

    if "pipeline_ejecutado" not in st.session_state:
        st.session_state["pipeline_ejecutado"] = False


    with st.sidebar.form("form_pipeline"):
        st.header("Definir parametros de entrada para el pipeline")
        meses_evaluacion=st.slider("Meses de evaluación", min_value=1, max_value=12, value=6)
        meses_forecast_futuro=st.slider("Cantidad de Meses a predecir", min_value=1, max_value=12, value=6)
        ventana_dummy=st.slider("Intervalo de entrenamiento modelo dummy", min_value=1, max_value=24, value=12)

        ejecutar=st.form_submit_button("Ejecutar pipeline forecast")

        if ejecutar:
            ruta_excel="./Datos/df_matriz_ventas_articulos_forecast.xlsx"
            resultados_pipeline = correr_pipeline_cacheado(
                ruta_excel=ruta_excel,
                meses_evaluacion=meses_evaluacion,
                meses_forecast_futuro=meses_forecast_futuro,
                ventana_dummy=ventana_dummy
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

        st.subheader("Resumen distribución modelos ganadores")
        df_resultado_kpi = resultados_pipeline["df_resultado_final"].copy()
        df_best_model_kpi = resultados_pipeline["df_best_model"].copy()

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

        wape_limpio = (df_best_model_kpi["WAPE_ranking"].replace([np.inf, -np.inf], np.nan))
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
            | np.isinf(df_best_model_kpi["WAPE_ranking"])
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
                values="Porcentaje",
                use_container_width=True
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        # ============================================================
        # TABS PENDIENTES
        # ============================================================
        # De momento dejamos los otros tabs con mensajes placeholder.
        # Esto permite probar la app sin que falle por secciones incompletas.
        # ============================================================
    with tab2:
        st.info("Pendiente: Top 10 artículos con menor error de predicción.")

    with tab3:
        st.info("Pendiente: Top 10 artículos con mayor error de predicción.")

    with tab4:
        st.info("Pendiente: distribución de WAPE_ranking.")

    with tab5:
        st.info("Pendiente: distribución de sesgo por modelo ganador.")

    with tab6:
        st.info("Pendiente: distribución de modelos ganadores por cluster de ventas.")


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