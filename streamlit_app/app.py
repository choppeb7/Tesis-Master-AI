import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from io import BytesIO

# ============================================================
# CONFIGURACIÓN DE LA APP
# ============================================================

st.set_page_config(
    page_title="Consulta CEROSA",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Prueba local - Consulta CEROSA")
st.write("Esta app prueba la conexión con PostgreSQL en Render.")


# ============================================================
# CONEXIÓN A POSTGRESQL
# ============================================================

@st.cache_resource
def get_engine():
    user = st.secrets["PGUSER"]
    password = st.secrets["PGPASSWORD"]
    host = st.secrets["PGHOST"]
    port = st.secrets["PGPORT"]
    dbname = st.secrets["PGDATABASE"]

    database_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"

    return create_engine(database_url)


# Crear el engine
engine = get_engine()

# ============================================================
# PRUEBA DE CONEXIÓN
# ============================================================

try:
    with engine.connect() as conn:
        resultado = conn.execute(text("SELECT 1 AS prueba;"))
        valor = resultado.scalar()

    st.success(f"Conexión exitosa a PostgreSQL. Resultado prueba: {valor}")

except Exception as e:
    st.error("Error al conectar con PostgreSQL.")
    st.exception(e)
    st.stop()

# ============================================================
# CARGA CACHEADA DE DATA
# ============================================================

@st.cache_data(ttl=3600)
def cargar_data():
    query = """
        SELECT *
        FROM cerosa_analytics.oitm_ventas
        WHERE marca_fabricante IS NOT NULL
          AND marca_fabricante <> ''
        ORDER BY marca_fabricante, codigo_articulo;
    """

    df = pd.read_sql(query, engine)

    return df

# ============================================================
# FUNCIÓN PARA GENERAR EXCEL EN MEMORIA
# ============================================================

def convertir_df_a_excel(df):
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Datos")

    output.seek(0)

    return output


# ============================================================
# CARGAR DATA
# ============================================================

try:
    df = cargar_data()

except Exception as e:
    st.error("Error cargando la data desde PostgreSQL.")
    st.exception(e)
    st.stop()


# ============================================================
# FILTRO INTERACTIVO POR MARCA
# ============================================================

marcas = sorted(df["marca_fabricante"].dropna().unique())

opciones_marcas = ["Todas"] + marcas

marca_seleccionada = st.selectbox(
    "Selecciona una marca fabricante",
    opciones_marcas
)


# ============================================================
# FILTRADO LOCAL EN PANDAS
# ============================================================

if marca_seleccionada == "Todas":
    df_filtrado = (
        df.groupby("marca_fabricante", group_keys=False)
          .head(10)
          .reset_index(drop=True)
    )

    titulo = "Primeras 10 filas por cada fabricante"

else:
    df_filtrado = (
        df[df["marca_fabricante"] == marca_seleccionada]
        .head(10)
        .reset_index(drop=True)
    )

    titulo = f"Primeras 10 filas de {marca_seleccionada}"


# ============================================================
# MOSTRAR RESULTADO
# ============================================================

st.subheader(titulo)

st.write(f"Filas mostradas: {len(df_filtrado)}")

st.dataframe(
    df_filtrado,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# DESCARGA EN EXCEL
# ============================================================

excel_file = convertir_df_a_excel(df_filtrado)

nombre_archivo = (
    "primeras_10_filas_por_fabricante.xlsx"
    if marca_seleccionada == "Todas"
    else f"primeras_10_filas_{marca_seleccionada}.xlsx"
)

st.download_button(
    label="Descargar Excel",
    data=excel_file,
    file_name=nombre_archivo,
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)