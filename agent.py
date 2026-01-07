# -*- coding: utf-8 -*-
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from tools import TOOLS

def build_agent():
    """
    Build an agent compatible with LangChain 1.2.0
    Uses simple keyword matching to route to the right tool
    Now returns which tool was used
    """
    llm = Ollama(model="llama3", temperature=0, base_url="http://localhost:11434")
    
    # Create tool mapping
    tools_dict = {tool.name: tool for tool in TOOLS}
    
    # Tool descriptions for the prompt
    tools_desc = "\n".join([
        f"- {tool.name}: {tool.description}" 
        for tool in TOOLS
    ])
    
    class Agent:
        def __init__(self, llm, tools_dict, tools_desc):
            self.llm = llm
            self.tools_dict = tools_dict
            self.tools_desc = tools_desc
            
        def _select_tool(self, question):
            """Select the appropriate tool based on keywords"""
            q_lower = question.lower()
            
            # Check for closed events in oct/nov
            if ("cerrado" in q_lower or "closed" in q_lower):
                if any(word in q_lower for word in ["octubre", "noviembre", "oct", "nov"]):
                    return "closed_events_oct_nov"
            
            # Check for severity-based events
            if any(word in q_lower for word in ["warning", "critical", "severidad", "severity"]):
                return "events_by_severity"
            
            # Check for open tickets by month
            if "ticket" in q_lower:
                if any(word in q_lower for word in ["mes", "month", "abierto", "open", "mensual"]):
                    return "open_tickets_by_month"
            
            return None
        
        def invoke(self, inputs):
            """Main execution method (LangChain 1.x standard)"""
            question = inputs.get("input", "")
            
            # Select and execute tool
            tool_name = self._select_tool(question)
            
            if tool_name and tool_name in self.tools_dict:
                tool = self.tools_dict[tool_name]
                try:
                    result = tool.func(question)
                    # IMPORTANTE: Retornar qué herramienta se usó
                    return {
                        "output": result,
                        "tool_used": tool_name
                    }
                except Exception as e:
                    return {
                        "output": f"Error ejecutando {tool_name}: {str(e)}",
                        "tool_used": None
                    }
            else:
                return {
                    "output": self._no_tool_response(question),
                    "tool_used": None
                }
        
        def run(self, question):
            """Backward compatibility method"""
            result = self.invoke({"input": question})
            return result["output"]
        
        def _no_tool_response(self, question):
            """Response when no tool matches"""
            return f"""No pude identificar una herramienta para tu pregunta: "{question}"

Herramientas disponibles:
{self.tools_desc}

Ejemplos de preguntas:
- "muestra los eventos cerrados en octubre y noviembre"
- "grafico de eventos warning y critical"
- "tickets abiertos por mes"

Por favor reformula tu pregunta."""
    
    return Agent(llm, tools_dict, tools_desc)