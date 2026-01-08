from langchain_core.tools import Tool
from excel_loader import ExcelAnalyzer
from typing import Optional

excel: Optional[ExcelAnalyzer] = None  # Sera asignado en main o api.py

def closed_events_tool_wrapper(q: str, **kwargs) -> tuple:
    """Wrapper para eventos cerrados por mes (flexible)"""
    if excel is None:
        return "Error: No hay Excel cargado", {}
    
    try:
        return excel.run_query('closed_events_by_month', **kwargs)
    except Exception as e:
        return f"Error: {str(e)}", {}


def events_by_severity_tool_wrapper(q: str, **kwargs) -> tuple:
    """Wrapper para eventos por severidad (flexible)"""
    if excel is None:
        return "Error: No hay Excel cargado", {}
    
    try:
        return excel.run_query('events_by_severity', **kwargs)
    except Exception as e:
        return f"Error: {str(e)}", {}


def open_tickets_by_month_tool_wrapper(q: str, **kwargs) -> tuple:
    """Wrapper para tickets abiertos por mes (flexible)"""
    if excel is None:
        return "Error: No hay Excel cargado", {}
    
    try:
        return excel.run_query('open_tickets_by_month', **kwargs)
    except Exception as e:
        return f"Error: {str(e)}", {}


def events_by_state_tool_wrapper(q: str, **kwargs) -> tuple:
    """Wrapper para eventos por estado"""
    if excel is None:
        return "Error: No hay Excel cargado", {}
    
    try:
        return excel.run_query('events_by_state', **kwargs)
    except Exception as e:
        return f"Error: {str(e)}", {}


# Definicion de herramientas mejoradas
tool_closed_events = Tool(
    name="closed_events_by_month",
    func=closed_events_tool_wrapper,
    description="Cuenta eventos con estado CLOSED por mes. Flexible para filtrar meses especificos o todos."
)

tool_events_by_severity = Tool(
    name="events_by_severity",
    func=events_by_severity_tool_wrapper,
    description="Cuenta eventos por nivel de severidad (WARNING, CRITICAL, etc). Flexible para filtrar severidades especificas."
)

tool_open_tickets_by_month = Tool(
    name="open_tickets_by_month",
    func=open_tickets_by_month_tool_wrapper,
    description="Cuenta eventos con estado OPEN por mes. Flexible para filtrar meses especificos o todos."
)

tool_events_by_state = Tool(
    name="events_by_state",
    func=events_by_state_tool_wrapper,
    description="Cuenta eventos por estado (OPEN, CLOSED, PENDING, etc)."
)

TOOLS = [
    tool_closed_events, 
    tool_events_by_severity, 
    tool_open_tickets_by_month,
    tool_events_by_state
]