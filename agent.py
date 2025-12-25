from langchain_community.llms import Ollama
from langchain.agents import initialize_agent, AgentType
from tools import TOOLS  # Asegúrate que tools.py define TOOLS y tiene la variable `excel` inicializada

def build_agent():
    from langchain_community.llms import Ollama
    from langchain.agents import initialize_agent, AgentType
    from tools import TOOLS
    llm = Ollama(model="llama3")
    agent = initialize_agent(
        tools=TOOLS,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,  # Usa este tipo
        verbose=True
    )
    return agent
