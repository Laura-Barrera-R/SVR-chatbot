# coding: utf-8
from langchain_community.llms import Ollama
from typing import Dict, Any, List, Optional
import json
import re

class IntelligentExcelAgent:
    
    def __init__(self, tools_dict: Dict):
        self.llm = Ollama(
            model="llama3", 
            temperature=0,
            base_url="http://localhost:11434",
            timeout=15  # Timeout de 15 segundos
        )
        self.tools_dict = tools_dict
        self.conversation_history = []
        self.use_llm = True  # Flag para activar/desactivar LLM
        
    def _extract_month_numbers(self, question: str) -> Optional[List[int]]:
        month_map = {
            'enero': 1, 'ene': 1, 'febrero': 2, 'feb': 2, 'marzo': 3, 'mar': 3,
            'abril': 4, 'abr': 4, 'mayo': 5, 'may': 5, 'junio': 6, 'jun': 6,
            'julio': 7, 'jul': 7, 'agosto': 8, 'ago': 8, 'septiembre': 9, 'sep': 9,
            'octubre': 10, 'oct': 10, 'noviembre': 11, 'nov': 11, 'diciembre': 12, 'dic': 12
        }
        
        q_lower = question.lower()
        months = [num for name, num in month_map.items() if name in q_lower]
        return months if months else None
    
    def _detect_chart_type(self, question: str) -> str:
        """Detecta el tipo de grafico solicitado"""
        q_lower = question.lower()
        if "pastel" in q_lower or "circular" in q_lower or "pie" in q_lower or "torta" in q_lower:
            return "pie"
        elif "linea" in q_lower or "lineas" in q_lower or "line" in q_lower:
            return "line"
        return "bar"
    
    def _detect_severities(self, question: str) -> Optional[List[str]]:
        """Detecta severidades mencionadas"""
        q_lower = question.lower()
        severities = []
        
        if "warning" in q_lower:
            severities.append("WARNING")
        if "critical" in q_lower:
            severities.append("CRITICAL")
        if "major" in q_lower:
            severities.append("MAJOR")
        if "minor" in q_lower:
            severities.append("MINOR")
        
        return severities if severities else None
    
    def invoke(self, inputs: Dict[str, str]) -> Dict[str, Any]:
        question = inputs.get("input", "")
        q_lower = question.lower()
        
        # Usar logica basada en keywords (MAS RAPIDO)
        print(f"[DEBUG] Procesando: {question}")
        
        # Detectar tipo de grafico
        chart_type = self._detect_chart_type(question)
        
        # Detectar herramienta por keywords
        tool_name = None
        params = {}
        
        if "cerrado" in q_lower or "closed" in q_lower:
            tool_name = "closed_events_by_month"
            months = self._extract_month_numbers(question)
            params = {"months": months, "chart_type": chart_type}
            print(f"[DEBUG] Herramienta: {tool_name}, meses: {months}")
            
        elif "severidad" in q_lower or "warning" in q_lower or "critical" in q_lower:
            tool_name = "events_by_severity"
            severities = self._detect_severities(question)
            params = {"severities": severities, "chart_type": chart_type}
            print(f"[DEBUG] Herramienta: {tool_name}, severidades: {severities}")
            
        elif "abierto" in q_lower or "open" in q_lower or "ticket" in q_lower:
            tool_name = "open_tickets_by_month"
            months = self._extract_month_numbers(question)
            params = {"months": months, "chart_type": chart_type}
            print(f"[DEBUG] Herramienta: {tool_name}, meses: {months}")
            
        elif "estado" in q_lower or "state" in q_lower:
            tool_name = "events_by_state"
            params = {"chart_type": chart_type}
            print(f"[DEBUG] Herramienta: {tool_name}")
        
        # Ejecutar herramienta
        if tool_name and tool_name in self.tools_dict:
            return self._execute_tool(tool_name, params, question)
        else:
            return {
                "output": "No entendi la pregunta. Ejemplos: 'eventos cerrados en octubre', 'grafico de WARNING', 'tickets abiertos'",
                "tool_used": None
            }
    
    def _execute_tool(self, tool_name: str, params: Dict, question: str) -> Dict[str, Any]:
        """Ejecuta la herramienta con los parametros"""
        tool = self.tools_dict[tool_name]
        kwargs = {"show_chart": True}
        
        # Agregar parametros
        if params.get("months") is not None:
            kwargs["months"] = params["months"]
        if params.get("severities") is not None:
            kwargs["severities"] = params["severities"]
        if params.get("states") is not None:
            kwargs["states"] = params["states"]
        if params.get("chart_type"):
            kwargs["chart_type"] = params["chart_type"]
        
        print(f"[DEBUG] Ejecutando {tool_name} con: {kwargs}")
        
        try:
            result_msg, data = tool.func(question, **kwargs)
            
            # Generar respuesta simple
            if data:
                total = sum(data.values())
                details = ", ".join([f"{v} en {k}" for k, v in list(data.items())[:5]])  # Max 5 items
                if len(data) > 5:
                    details += f" (y {len(data)-5} mas)"
                response = f"He generado el grafico. Total: {total}. Detalle: {details}."
            else:
                response = result_msg
            
            # Guardar en historial
            self.conversation_history.append({
                "question": question,
                "tool": tool_name,
                "params": params,
                "data": data
            })
            
            return {
                "output": response,
                "tool_used": tool_name,
                "data": data
            }
            
        except Exception as e:
            print(f"[ERROR] {str(e)}")
            return {
                "output": f"Error al procesar: {str(e)}",
                "tool_used": None
            }


def build_agent():
    from tools import TOOLS
    
    tools_dict = {tool.name: tool for tool in TOOLS}
    agent = IntelligentExcelAgent(tools_dict)
    
    import tools
    if hasattr(tools, 'excel') and tools.excel:
        agent.excel = tools.excel
    
    return agent