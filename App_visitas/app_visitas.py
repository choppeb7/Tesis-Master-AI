import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import date

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="Registro de Visitas Comerciales",
    page_icon="📍",
    layout="centered"
)

st.title("📍 Registro de Visitas Comerciales")
st.caption("Formulario interno para registrar visitas a clientes")

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

engine = get_engine()

# ============================================================
# LISTAS BASE
# Idealmente después estas listas vienen de SAP o de tu tabla de clientes
# ============================================================

vendedores = [
    "Oscar",
    "Néstor",
    "Cristian Cruz",
    "Christian Hoppe"
]

clientes = [
    "Cliente A",
    "Cliente B",
    "Cliente C",
    "Cliente D"
]

tipos_visita = [
    "Visita comercial",
    "Seguimiento de cotización",
    "Levantamiento técnico",
    "Cobro",
    "Entrega de pedido",
    "Reclamo / soporte",
    "Presentación de producto",
    "Otro"
]

# ============================================================
# FORMULARIO
# ============================================================

with st.form("form_visita"):

    vendedor = st.selectbox("Vendedor", vendedores)

    cliente = st.selectbox("Cliente visitado", clientes)

    fecha_visita = st.date_input(
        "Fecha de visita",
        value=date.today()
    )

    tipo_visita = st.selectbox("Tipo de visita", tipos_visita)

    comentario = st.text_area(
        "Comentario de la visita",
        placeholder="Ejemplo: Se visitó al cliente para revisar necesidad de variador de frecuencia para motor de 15 HP..."
    )

    producto_interes = st.text_input(
        "Producto de interés",
        placeholder="Ejemplo: variador, motor, rodamiento, contactor, PLC, etc."
    )

    requiere_seguimiento = st.checkbox("¿Requiere seguimiento?")

    fecha_proximo_seguimiento = None

    if requiere_seguimiento:
        fecha_proximo_seguimiento = st.date_input(
            "Fecha de próximo seguimiento",
            value=date.today()
        )

    enviar = st.form_submit_button("Guardar visita")

# ============================================================
# INSERTAR DATOS
# ============================================================

if enviar:

    if not comentario.strip():
        st.error("El comentario de la visita es obligatorio.")
        st.stop()

    insert_query = text("""
        INSERT INTO cerosa_comercial.visitas_clientes (
            fecha_visita,
            vendedor,
            cliente,
            tipo_visita,
            comentario,
            producto_interes,
            requiere_seguimiento,
            fecha_proximo_seguimiento
        )
        VALUES (
            :fecha_visita,
            :vendedor,
            :cliente,
            :tipo_visita,
            :comentario,
            :producto_interes,
            :requiere_seguimiento,
            :fecha_proximo_seguimiento
        );
    """)

    params = {
        "fecha_visita": fecha_visita,
        "vendedor": vendedor,
        "cliente": cliente,
        "tipo_visita": tipo_visita,
        "comentario": comentario,
        "producto_interes": producto_interes,
        "requiere_seguimiento": requiere_seguimiento,
        "fecha_proximo_seguimiento": fecha_proximo_seguimiento
    }

    try:
        with engine.begin() as conn:
            conn.execute(insert_query, params)

        st.success("Visita registrada correctamente.")

    except Exception as e:
        st.error("Ocurrió un error al guardar la visita.")
        st.exception(e)