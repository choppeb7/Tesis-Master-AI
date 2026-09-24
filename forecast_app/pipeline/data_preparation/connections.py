from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv
import os
import pyodbc
from pathlib import Path
import sys
import traceback



def obtener_ruta_env():
    """
    Obtiene la ruta del archivo .env ubicado en la raíz del proyecto.

    Este archivo connections.py está en:
    Tesis-Master-AI/forecast_app/pipeline/data_preparation/connections.py

    Por eso:
    parents[0] = data_preparation
    parents[1] = pipeline
    parents[2] = forecast_app
    parents[3] = Tesis-Master-AI
    """

    project_root = Path(__file__).resolve().parents[3]
    env_path = project_root / ".env"

    return env_path


def crear_engine_sqlserver(env_path=None, driver="ODBC Driver 17 for SQL Server"):
        
    if env_path is None:
        env_path = obtener_ruta_env()
        print("Ruta .env utilizada:", env_path)
        print("Existe .env:", env_path.exists())

    load_dotenv(dotenv_path=env_path)

    SERVER = os.getenv("DB_SERVER1")
    DBNAME = os.getenv("DB_NAME1")
    USER = os.getenv("DB_USER1")
    PASS = os.getenv("DB_PASSWORD1")
    ENCRYPT = os.getenv("DB_ENCRYPT", "yes")
    TRUST = os.getenv("DB_TRUST_CERT", "yes")

    variables_requeridas = {
        "DB_SERVER1": SERVER,
        "DB_NAME1": DBNAME,
        "DB_USER1": USER,
        "DB_PASSWORD1": PASS
    }

    faltantes = [
        nombre
        for nombre, valor in variables_requeridas.items()
        if valor is None or str(valor).strip() == ""
        ]

    if faltantes:
        raise ValueError(
            "Faltan variables de entorno para conexión SQL Server: "
            + ", ".join(faltantes)
            )

    SERVER = SERVER.replace("\\\\", "\\")  # normaliza


    cnx = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={SERVER};"
        f"DATABASE={DBNAME};"
        f"UID={USER};"
        f"PWD={PASS};"
        f"Encrypt={ENCRYPT};TrustServerCertificate={TRUST};"
        )

    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={quote_plus(cnx)}")

    return engine

def probar_conexion_sqlserver(engine):
    """
    Prueba la conexión a SQL Server ejecutando SELECT 1.
    """

    with engine.connect() as conn:
        ping = conn.execute(text("SELECT 1")).scalar_one()
        version = conn.execute(text("SELECT @@VERSION")).scalar_one()

    return {
        "ping": ping,
        "version": version
        }

def main():
    """
    Prueba directa del módulo connections.py.
    """

    print("=" * 80)
    print("PRUEBA DE CONEXIÓN SQL SERVER / SAP B1")
    print("=" * 80)

    try:
        engine = crear_engine_sqlserver()

        print("Engine creado correctamente ✅")

        resultado = probar_conexion_sqlserver(engine)

        print("Conexión SQL Server OK ✅")
        print("Ping:", resultado["ping"])
        print("Versión SQL Server:")
        print(resultado["version"][:500])

    except Exception as error:
        print("Error probando conexión SQL Server ❌")
        print(type(error).__name__)
        print(error)

        print("\nDetalle técnico:")
        traceback.print_exc()


if __name__ == "__main__":
    main()