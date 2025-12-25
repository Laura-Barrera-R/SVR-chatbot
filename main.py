from excel_loader import ExcelAnalyzer
from pdf_loader import load_pdf_text
from memory import create_memory
from agent import build_agent
import tools  # <- Importa y luego asigna excel más abajo

texts = []

excel_path = input("Ruta Excel (enter para omitir): ")
excel = None
if excel_path:
    excel = ExcelAnalyzer(excel_path)
    texts.append("ESQUEMA:\n" + excel.schema())
    texts.append("MUESTRA:\n" + excel.sample())
    tools.excel = excel  # <- Asigna la instancia al módulo tools

pdf_path = input("Ruta PDF (enter para omitir): ")
if pdf_path:
    texts.append(load_pdf_text(pdf_path))

memory = create_memory(texts)
agent = build_agent()

print("\n🤖 IA lista para ayudarte: escribe preguntas como 'muéstrame el gráfico de eventos CLOSED en octubre y noviembre', 'dame los warning y critical en gráfico', etc.\n")
while True:
    q = input("Tú: ")
    if q.lower() == "salir":
        break
    res = agent.run(q)   # <-- Pasa únicamente el string de la pregunta
    print("\n🤖 IA:", res, "\n")