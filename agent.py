# -*- coding: utf-8 -*-
from langchain_community.llms import Ollama
from typing import Dict, Any, List, Optional, Tuple
import json
import re

class IntelligentExcelAgent:
    
    def __init__(self, tools_dict: Dict):
        self.llm = Ollama(
            model="llama3.2:1b", 
            temperature=0.3,
            base_url="http://localhost:11434",
            timeout=60
        )
        self.tools_dict = tools_dict
        self.conversation_history = []
        self.last_query_context = None
        
    def _extract_month_numbers(self, question: str) -> Optional[List[int]]:
        """Extrae numeros de meses de la pregunta"""
        month_map = {
            'enero': 1, 'ene': 1, 'febrero': 2, 'feb': 2, 'marzo': 3, 'mar': 3,
            'abril': 4, 'abr': 4, 'mayo': 5, 'may': 5, 'junio': 6, 'jun': 6,
            'julio': 7, 'jul': 7, 'agosto': 8, 'ago': 8, 'septiembre': 9, 'sep': 9,
            'octubre': 10, 'oct': 10, 'noviembre': 11, 'nov': 11, 'diciembre': 12, 'dic': 12
        }
        
        q_lower = question.lower()
        
        # Detectar si pregunta por TODOS los meses
        if any(word in q_lower for word in ['todos', 'todo', 'cada', 'all']):
            return None  # None significa "todos los meses"
        
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
    
    def _extract_colors(self, question: str) -> Optional[List[str]]:
        """Extrae colores mencionados en la pregunta"""
        color_map = {
            'rojo': '#FF0000', 'red': '#FF0000',
            'azul': '#0000FF', 'blue': '#0000FF',
            'verde': '#00FF00', 'green': '#00FF00',
            'amarillo': '#FFFF00', 'yellow': '#FFFF00',
            'naranja': '#FFA500', 'orange': '#FFA500',
            'morado': '#800080', 'purple': '#800080',
            'rosa': '#FFC0CB', 'pink': '#FFC0CB',
            'negro': '#000000', 'black': '#000000',
            'blanco': '#FFFFFF', 'white': '#FFFFFF',
            'gris': '#808080', 'gray': '#808080', 'grey': '#808080'
        }
        
        q_lower = question.lower()
        colors = [color_map[name] for name in color_map if name in q_lower]
        return colors if colors else None
    
    def _is_follow_up_question(self, question: str) -> bool:
        """Detecta si es una pregunta de seguimiento que necesita contexto"""
        follow_up_keywords = [
            'entonces', 'ahora', 'y', 'tambien', 'ademas',
            'ese', 'esa', 'esos', 'esas', 'el mismo', 'la misma',
            'cuantos hay', 'hay en', 'en ese', 'de eso',
            'cambia', 'cambiar', 'modifica', 'modificar', 'regenera'
        ]
        
        q_lower = question.lower()
        return any(keyword in q_lower for keyword in follow_up_keywords)
    
    def _is_chart_request(self, question: str) -> bool:
        """Detecta si el usuario esta pidiendo un grafico"""
        q_lower = question.lower()
        chart_keywords = [
            'grafico', 'grafica', 'chart', 'plot', 
            'visualiza', 'muestra', 'dibuja', 'genera',
            'pastel', 'barras', 'linea', 'pie'
        ]
        return any(keyword in q_lower for keyword in chart_keywords)
    
    def _resolve_context_with_llm(self, question: str) -> Tuple[str, Dict]:
        """Usa el LLM para resolver el contexto de una pregunta de seguimiento"""
        if not self.last_query_context:
            return question, {}
        
        last_tool = self.last_query_context.get('tool')
        last_params = self.last_query_context.get('params', {})
        last_question = self.last_query_context.get('question', '')
        
        context_prompt = f"""Contexto de la conversacion anterior:
- Pregunta anterior: "{last_question}"
- Tipo de consulta: {last_tool}
- Parametros usados: {last_params}

Nueva pregunta del usuario: "{question}"

Esta nueva pregunta hace referencia a la anterior? Responde SOLO con:
1. "SI" si es una pregunta de seguimiento que necesita contexto
2. "NO" si es una pregunta nueva e independiente

Respuesta (SI o NO):"""

        try:
            response = self.llm.invoke(context_prompt).strip().upper()
            needs_context = "SI" in response or "YES" in response
            
            if needs_context:
                print(f"[DEBUG] Pregunta de seguimiento detectada, usando contexto")
                return question, last_params
            else:
                return question, {}
                
        except Exception as e:
            print(f"[WARNING] Error resolviendo contexto: {str(e)[:50]}")
            return question, {}
    
    def _generate_natural_response(self, question: str, data: Dict, tool_name: str) -> str:
        """Genera una respuesta natural, formal y profesional usando el LLM"""
        if not data:
            return "No se encontraron registros que cumplan con los criterios especificados en el sistema de monitoreo."
        
        # Preparar el resumen de datos
        data_items = list(data.items())
        total = sum(data.values())
        
        # Construir detalle estructurado
        if len(data_items) <= 5:
            data_detail = ", ".join([f"{k}: {v}" for k, v in data_items])
        else:
            top_items = sorted(data_items, key=lambda x: x[1], reverse=True)[:3]
            data_detail = ", ".join([f"{k}: {v}" for k, v in top_items])
            data_detail += f" (y {len(data_items)-3} categorias adicionales)"
        
        # Contexto del dominio
        domain_context = """
Contexto del sistema:
Servicio de monitoreo avanzado y proactivo para infraestructuras y plataformas tecnicas alojadas en Oracle Cloud (IaaS/PaaS).
Monitoreo 24/7 de componentes tecnicos (servidores, bases de datos, redes, middleware).
Deteccion temprana de incidentes, analisis de desempeno, capacidad y seguridad.
"""
        
        # Información de contexto conversacional
        context_info = ""
        if len(self.conversation_history) > 0:
            last_conv = self.conversation_history[-1]
            context_info = f"\nConsulta previa relacionada: {last_conv.get('question', '')}"
        
        # Prompt optimizado para respuesta profesional
        prompt = f"""Eres un asistente especializado en analisis de metricas de monitoreo de infraestructura Oracle Cloud.

{domain_context}

Consulta del usuario: "{question}"

Resultados obtenidos del sistema:
- Total de registros: {total}
- Distribucion: {data_detail}
{context_info}

INSTRUCCIONES ESTRICTAS:
1. Responde en tono FORMAL y PROFESIONAL 
2. Usa terminologia tecnica apropiada para monitoreo de servicios
3. Se CONCISO: maximo 3 oraciones
4. Responde UNICAMENTE lo consultado, sin agregar informacion no solicitada
5. Menciona el total y los valores mas relevantes
6. NO uses emojis, NO uses asteriscos, NO uses puntos suspensivos

Respuesta profesional:"""

        try:
            response = self.llm.invoke(prompt)
            response = response.strip()
            
            # Limpieza de la respuesta
            response = re.sub(r'\*+', '', response)  # Eliminar asteriscos
            response = re.sub(r'\.{3,}', '.', response)  # Eliminar puntos suspensivos
            response = re.sub(r'\s+', ' ', response)  # Normalizar espacios
            
            # Limitar longitud si es necesario
            if len(response) > 350:
                sentences = [s.strip() for s in response.split('.') if s.strip()]
                response = '. '.join(sentences[:3]) + '.'
            
            # Asegurar que termina con punto
            if response and not response.endswith('.'):
                response += '.'
            
            return response
            
        except Exception as e:
            print(f"[ERROR] Error en generacion de respuesta LLM: {str(e)}")
            return self._fallback_response(data, total)
    
    def _fallback_response(self, data: Dict, total: int) -> str:
        """Respuesta de respaldo formal si el LLM falla"""
        details = ", ".join([f"{v} registros en {k}" for k, v in list(data.items())[:5]])
        if len(data) > 5:
            details += f" (y {len(data)-5} categorias adicionales)"
        return f"Se han identificado {total} registros en el sistema de monitoreo. Distribucion: {details}."
    
    def invoke(self, inputs: Dict[str, str]) -> Dict[str, Any]:
        question = inputs.get("input", "")
        q_lower = question.lower()
        
        print(f"[DEBUG] Procesando: {question}")
        
        # Verificar si es pregunta de seguimiento
        additional_context = {}
        if self._is_follow_up_question(question) and self.last_query_context:
            print("[DEBUG] Detectada pregunta de seguimiento")
            _, additional_context = self._resolve_context_with_llm(question)
        
        # Detectar tipo de grafico
        chart_type = self._detect_chart_type(question)
        
        # Detectar colores
        colors = self._extract_colors(question)
        
        # Detectar si quiere regenerar/cambiar grafico o generar uno nuevo
        is_regenerate = any(word in q_lower for word in ['cambia', 'cambiar', 'regenera', 'modifica', 'nuevo grafico'])
        is_chart_request = self._is_chart_request(question)
        
        # Si es una peticion de grafico y tenemos contexto previo, usar la ultima herramienta
        if (is_regenerate or is_chart_request) and self.last_query_context:
            tool_name = self.last_query_context['tool']
            params = self.last_query_context['params'].copy()
            
            # Actualizar tipo de grafico si se especifica uno nuevo
            params['chart_type'] = chart_type
            
            # Actualizar colores si se especifican
            if colors:
                params['colors'] = colors
            
            # Si menciona meses especificos en esta nueva pregunta, actualizar
            new_months = self._extract_month_numbers(question)
            if new_months:
                params['months'] = new_months
            
            # Si menciona severidades en esta nueva pregunta, actualizar
            new_severities = self._detect_severities(question)
            if new_severities:
                params['severities'] = new_severities
            
            print(f"[DEBUG] Regenerando/Generando grafico con herramienta: {tool_name}, params: {params}")
            return self._execute_tool(tool_name, params, question)
        
        # Detectar herramienta por keywords
        tool_name = None
        params = {}
        
        if "cerrado" in q_lower or "closed" in q_lower:
            tool_name = "closed_events_by_month"
            months = self._extract_month_numbers(question)
            
            if months is None and additional_context.get('months') is not None:
                months = additional_context['months']
                print(f"[DEBUG] Usando meses del contexto: {months}")
            
            params = {"months": months, "chart_type": chart_type}
            if colors:
                params['colors'] = colors
            print(f"[DEBUG] Herramienta: {tool_name}, meses: {months}")
            
        elif "severidad" in q_lower or "warning" in q_lower or "critical" in q_lower:
            tool_name = "events_by_severity"
            severities = self._detect_severities(question)
            
            if severities is None and additional_context.get('severities') is not None:
                severities = additional_context['severities']
                print(f"[DEBUG] Usando severidades del contexto: {severities}")
            
            params = {"severities": severities, "chart_type": chart_type}
            if colors:
                params['colors'] = colors
            print(f"[DEBUG] Herramienta: {tool_name}, severidades: {severities}")
            
        elif "abierto" in q_lower or "open" in q_lower or "ticket" in q_lower:
            tool_name = "open_tickets_by_month"
            months = self._extract_month_numbers(question)
            
            if months is None and additional_context.get('months') is not None:
                months = additional_context['months']
                print(f"[DEBUG] Usando meses del contexto: {months}")
            
            params = {"months": months, "chart_type": chart_type}
            if colors:
                params['colors'] = colors
            print(f"[DEBUG] Herramienta: {tool_name}, meses: {months}")
            
        elif "estado" in q_lower or "state" in q_lower:
            tool_name = "events_by_state"
            params = {"chart_type": chart_type}
            if colors:
                params['colors'] = colors
            print(f"[DEBUG] Herramienta: {tool_name}")
        
        # Si no detectamos herramienta pero hay contexto
        if not tool_name and self.last_query_context and self._is_follow_up_question(question):
            print("[DEBUG] No se detecto herramienta, pero parece seguimiento. Usando contexto.")
            tool_name = self.last_query_context['tool']
            params = self.last_query_context['params'].copy()
            
            new_months = self._extract_month_numbers(question)
            if new_months:
                params['months'] = new_months
        
        # Ejecutar herramienta
        if tool_name and tool_name in self.tools_dict:
            return self._execute_tool(tool_name, params, question)
        else:
            return {
                "output": "No se pudo identificar la consulta solicitada. Por favor, especifique el tipo de analisis deseado (eventos cerrados, abiertos, por severidad o por estado).",
                "tool_used": None
            }
    
    def _execute_tool(self, tool_name: str, params: Dict, question: str) -> Dict[str, Any]:
        """Ejecuta la herramienta con los parametros"""
        tool = self.tools_dict[tool_name]
        kwargs = {"show_chart": True}
        
        if params.get("months") is not None:
            kwargs["months"] = params["months"]
        if params.get("severities") is not None:
            kwargs["severities"] = params["severities"]
        if params.get("states") is not None:
            kwargs["states"] = params["states"]
        if params.get("chart_type"):
            kwargs["chart_type"] = params["chart_type"]
        if params.get("colors"):
            kwargs["colors"] = params["colors"]
        
        print(f"[DEBUG] Ejecutando {tool_name} con: {kwargs}")
        
        try:
            result_msg, data = tool.func(question, **kwargs)
            
            print("[DEBUG] Generando respuesta profesional con LLM...")
            response = self._generate_natural_response(question, data, tool_name)
            print(f"[DEBUG] Respuesta generada: {response[:100]}...")
            
            self.last_query_context = {
                "question": question,
                "tool": tool_name,
                "params": params,
                "data": data
            }
            
            self.conversation_history.append({
                "question": question,
                "tool": tool_name,
                "params": params,
                "data": data,
                "response": response
            })
            
            return {
                "output": response,
                "tool_used": tool_name,
                "data": data
            }
            
        except Exception as e:
            print(f"[ERROR] {str(e)}")
            return {
                "output": f"Se ha producido un error al procesar la consulta: {str(e)}",
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