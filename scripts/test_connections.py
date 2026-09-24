from pathlib import Path
import sys
import traceback

# ============================================================
# DEFINIR RUTAS DEL PROYECTO
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FORECAST_APP_DIR = PROJECT_ROOT / "forecast_app"
ENV_PATH = PROJECT_ROOT / ".env"

if str(FORECAST_APP_DIR) not in sys.path:
    sys.path.insert(0, str(FORECAST_APP_DIR))


# ============================================================
# IMPORTAR FUNCIONES A PROBAR
# ============================================================

from pipeline.data_preparation.connections import (
    crear_engine_sqlserver,
    probar_conexion_sqlserver,
)


def probar_sqlserver():
    print("=" * 80)
    print("PRUEBA DE CONEXIÓN SQL SERVER / SAP B1")
    print("=" * 80)

    print(f"PROJECT_ROOT: {PROJECT_ROOT}")
    print(f"FORECAST_APP_DIR: {FORECAST_APP_DIR}")
    print(f"ENV_PATH: {ENV_PATH}")
    print(f"Existe .env: {ENV_PATH.exists()}")

    try:
        print("\nCreando engine SQL Server...")

        engine_sqlserver = crear_engine_sqlserver(
            env_path=ENV_PATH
        )

        print("Engine SQL Server creado correctamente ✅")

        print("\nProbando conexión con SELECT 1...")

        resultado = probar_conexion_sqlserver(
            engine=engine_sqlserver
        )

        print("Conexión SQL Server OK ✅")
        print(f"Ping: {resultado['ping']}")
        print("Versión SQL Server:")
        print(resultado["version"][:300])

    except Exception as error:
        print("Error probando conexión SQL Server ❌")
        print(type(error).__name__)
        print(error)
        print("\nDetalle técnico:")
        traceback.print_exc()


def probar_postgres():
    print("\n" + "=" * 80)
    print("PRUEBA DE CONEXIÓN POSTGRESQL")
    print("=" * 80)

    try:
        print("\nCreando engine PostgreSQL...")

        engine_postgres = crear_engine_postgres(
            env_path=ENV_PATH
        )

        print("Engine PostgreSQL creado correctamente ✅")

        with engine_postgres.connect() as conn:
            resultado = conn.exec_driver_sql("SELECT 1").scalar()

        print("Conexión PostgreSQL OK ✅")
        print(f"Ping: {resultado}")

    except Exception as error:
        print("Error probando conexión PostgreSQL ❌")
        print(type(error).__name__)
        print(error)
        print("\nEsto no afecta la prueba de SQL Server si todavía no vas a cargar a PostgreSQL.")


def main():
    probar_sqlserver()

    # Activa esta prueba solo si ya tienes variables PG configuradas en .env.
    # probar_postgres()


if __name__ == "__main__":
    main()