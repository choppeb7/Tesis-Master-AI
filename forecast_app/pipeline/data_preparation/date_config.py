from dataclasses import dataclass
from datetime import date
from dateutil.relativedelta import relativedelta
import pandas as pd
from datetime import timedelta



@dataclass
class DateConfig:
    fecha_fin: date
    fecha_fin_sql: str

    fecha_inicio_visual: date
    fecha_inicio_visual_sql: str

    fecha_inicio_historico: date
    fecha_inicio_historico_sql: str

    periodo_meses_historico: int
    periodo_meses_visual: int

    fecha_fin_exclusiva:date
    fecha_fin_exclusiva_sql:str


def construir_configuracion_fechas(
    fecha_fin=None,
    fecha_inicio_visual="2024-01-01",
    meses_historico=24
):
    """
    Construye la configuración de fechas usada por el query principal.

    fecha_fin:
        Fecha final del análisis. Puede ser None, string YYYY-MM-DD o date.
        Si es None, usa la fecha actual.

    fecha_inicio_visual:
        Fecha desde la cual se generan las columnas mensuales visibles,
        por ejemplo venta_enero_2024, venta_febrero_2024, etc.

    meses_historico:
        Cantidad de meses hacia atrás desde fecha_fin para calcular métricas
        como ventas 24m, frecuencia mensual, clientes 24m y compras 24m.
    """

    if fecha_fin is None:
        fecha_fin = date.today()

    elif isinstance(fecha_fin, str):
        fecha_fin = pd.to_datetime(fecha_fin).date()

    if isinstance(fecha_inicio_visual, str):
        fecha_inicio_visual = pd.to_datetime(fecha_inicio_visual).date()

    fecha_inicio_historico = fecha_fin - relativedelta(
        months=meses_historico
        )

    periodo_meses_visual = (
        (fecha_fin.year - fecha_inicio_visual.year) * 12
        + (fecha_fin.month - fecha_inicio_visual.month)
        + 1
        )

    if periodo_meses_visual <= 0:
        raise ValueError(
            "La fecha_inicio_visual no puede ser posterior a fecha_fin."
        )

    fecha_fin_exclusiva = fecha_fin + timedelta(days=1)

    return DateConfig(
        fecha_fin=fecha_fin,
        fecha_fin_sql=fecha_fin.strftime("%Y-%m-%d"),

        fecha_inicio_visual=fecha_inicio_visual,
        fecha_inicio_visual_sql=fecha_inicio_visual.strftime("%Y-%m-%d"),

        fecha_inicio_historico=fecha_inicio_historico,
        fecha_inicio_historico_sql=fecha_inicio_historico.strftime("%Y-%m-%d"),

        periodo_meses_historico=meses_historico,
        periodo_meses_visual=periodo_meses_visual,

        fecha_fin_exclusiva=fecha_fin_exclusiva,
        fecha_fin_exclusiva_sql=fecha_fin_exclusiva.strftime("%Y-%m-%d"),
    )


def main():
    """
    Prueba directa del módulo date_config.py.
    """

    config = construir_configuracion_fechas(
        fecha_fin="2026-09-22",
        fecha_inicio_visual="2024-01-01",
        meses_historico=24
    )

    print("=" * 80)
    print("PRUEBA DATE CONFIG")
    print("=" * 80)
    print(config)


if __name__ == "__main__":
    main()