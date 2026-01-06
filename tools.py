# -*- coding: utf-8 -*-
from langchain_core.tools import Tool
from excel_loader import ExcelAnalyzer
from typing import Optional

excel: Optional[ExcelAnalyzer] = None  # Sera asignado en main o api.py

def closed_events_tool_wrapper(q: str) -> str:
    """Wrapper para eventos cerrados en oct/nov"""
    if excel is None:
        return "Error: No hay Excel cargado"
    
    try:
        msg, data = excel.run_query('closed_events_oct_nov')
        detalle = "Detalle por mes: " + ', '.join([f"{v} en {k}" for k, v in data.items()])
        return f"{msg}\n{detalle}"
    except Exception as e:
        return f"Error: {str(e)}"

def events_by_severity_tool_wrapper(q: str) -> str:
    """Wrapper para eventos por severidad"""
    if excel is None:
        return "Error: No hay Excel cargado"
    
    try:
        msg, data = excel.run_query('events_by_severity')
        detalle = "Detalle: " + ', '.join([f"{v} {k}" for k, v in data.items()])
        return f"{msg}\n{detalle}"
    except Exception as e:
        return f"Error: {str(e)}"

def open_tickets_by_month_tool_wrapper(q: str) -> str:
    """Wrapper para tickets abiertos por mes"""
    if excel is None:
        return "Error: No hay Excel cargado"
    
    try:
        msg, data = excel.run_query('open_tickets_by_month')
        detalle = "Detalle por mes: " + ', '.join([f"{v} en mes {k}" for k, v in data.items()])
        return f"{msg}\n{detalle}"
    except Exception as e:
        return f"Error: {str(e)}"

# Definicion de herramientas
tool_closed_events = Tool(
    name="closed_events_oct_nov",
    func=closed_events_tool_wrapper,
    description="Genera un grafico con la cantidad de eventos CLOSED en octubre y noviembre en el Excel cargado."
)

tool_events_by_severity = Tool(
    name="events_by_severity",
    func=events_by_severity_tool_wrapper,
    description="Genera un grafico con la cantidad de eventos WARNING y CRITICAL en el Excel cargado."
)

tool_open_tickets_by_month = Tool(
    name="open_tickets_by_month",
    func=open_tickets_by_month_tool_wrapper,
    description="Genera un grafico de tickets abiertos por mes en el Excel cargado."
)

TOOLS = [tool_closed_events, tool_events_by_severity, tool_open_tickets_by_month]