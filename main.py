from excel_loader import ExcelAnalyzer
from agent import build_agent
import tools

print("=== Analizador IA de Excel ===\n")

excel_path = input("Ruta Excel (enter para omitir): ").strip()

if excel_path:
    try:
        excel = ExcelAnalyzer(excel_path)
        tools.excel = excel  # Asigna la instancia al módulo tools
        print(f"✅ Excel cargado: {len(excel.df)} filas\n")
    except Exception as e:
        print(f"❌ Error cargando Excel: {e}")
        exit(1)
else:
    print("⚠️ No se cargó ningún Excel")
    exit(0)

# Construye el agente
agent = build_agent()

print("\n🤖 IA lista. Ejemplos de preguntas:")
print("  - 'muéstrame el gráfico de eventos CLOSED en octubre y noviembre'")
print("  - 'dame los warning y critical en gráfico'")
print("  - 'gráfico de tickets abiertos por mes'")
print("\nEscribe 'salir' para terminar.\n")

while True:
    q = input("Tú: ").strip()
    
    if q.lower() in ["salir", "exit", "quit"]:
        print("👋 ¡Hasta luego!")
        break
    
    if not q:
        continue
    
    try:
        # Invoca el agente
        result = agent.invoke({"input": q})
        
        # Extrae la respuesta
        answer = result.get("output", str(result))
        print(f"\n🤖 IA: {answer}\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}\n")