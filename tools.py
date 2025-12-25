from langchain.tools import Tool
from excel_loader import ExcelAnalyzer

excel: ExcelAnalyzer = ...  # Será asignado en main

def closed_events_tool_wrapper(q):
    msg, data = excel.run_query('closed_events_oct_nov')
    detalle = "Detalle por mes: " + ', '.join([f"{v} en {k}" for k, v in data.items()])
    return f"{msg}\n{detalle}"

def events_by_severity_tool_wrapper(q):
    msg, data = excel.run_query('events_by_severity')
    detalle = "Detalle: " + ', '.join([f"{v} {k}" for k, v in data.items()])
    return f"{msg}\n{detalle}"

def open_tickets_by_month_tool_wrapper(q):
    msg, data = excel.run_query('open_tickets_by_month')
    detalle = "Detalle por mes: " + ', '.join([f"{v} en mes {k}" for k, v in data.items()])
    return f"{msg}\n{detalle}"

tool_closed_events = Tool(
    name="closed_events_oct_nov",
    func=closed_events_tool_wrapper,
    description="Genera un gráfico con la cantidad de eventos CLOSED en octubre y noviembre en el Excel cargado."
)

tool_events_by_severity = Tool(
    name="events_by_severity",
    func=events_by_severity_tool_wrapper,
    description="Genera un gráfico con la cantidad de eventos WARNING y CRITICAL en el Excel cargado."
)
tool_open_tickets_by_month = Tool(
    name="open_tickets_by_month",
    func=open_tickets_by_month_tool_wrapper,
    description="Genera un gráfico de tickets abiertos por mes en el Excel cargado."
)
TOOLS = [tool_closed_events, tool_events_by_severity, tool_open_tickets_by_month]