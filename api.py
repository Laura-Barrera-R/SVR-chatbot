from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse 
from pydantic import BaseModel
import os
import shutil
from pathlib import Path
from excel_loader import ExcelAnalyzer
from agent import build_agent
import tools
import asyncio
from concurrent.futures import ThreadPoolExecutor
import uuid
from typing import Optional

app = FastAPI(title="Ollama Excel Analyzer API")

# Variables globales para mantener estado
excel_analyzer = None
agent_instance = None

# Directorio para archivos temporales
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Directorio para gráficos generados
CHARTS_DIR = Path("./charts")
CHARTS_DIR.mkdir(exist_ok=True)

# Executor para tareas sincrónicas
executor = ThreadPoolExecutor(max_workers=4)

# Almacenamiento temporal de respuestas para consultas async
pending_queries = {}


class QuestionRequest(BaseModel):
    question: str
    async_mode: bool = False  # Nueva opción para modo asíncrono


class QuestionResponse(BaseModel):
    answer: str
    charts_generated: list[str] = []


class AsyncQueryResponse(BaseModel):
    query_id: str
    status: str
    message: str


class QueryStatusResponse(BaseModel):
    query_id: str
    status: str  # "pending", "completed", "error"
    answer: Optional[str] = None
    charts_generated: list[str] = []
    error: Optional[str] = None


# Endpoint para servir el frontend
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """
    Sirve el frontend HTML.
    """
    html_path = Path("./frontend_web/templates/index.html")
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(encoding='utf-8'), status_code=200)
    return HTMLResponse(content="<h1>Frontend no encontrado. Verifica la ruta.</h1>", status_code=404)

# Variables globales para mantener estado
excel_analyzer = None
agent_instance = None

@app.post("/upload-excel")
async def upload_excel(file: UploadFile = File(...)):
    """
    Endpoint para subir el archivo Excel que será analizado.
    """
    global excel_analyzer, agent_instance
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="El archivo debe ser Excel (.xlsx o .xls)")
    
    # Guardar archivo
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Inicializar analizador
        excel_analyzer = ExcelAnalyzer(str(file_path))
        tools.excel = excel_analyzer
        
        # Construir agente
        agent_instance = build_agent()
        
        return {
            "message": "Excel cargado exitosamente",
            "filename": file.filename,
            "rows": len(excel_analyzer.df),
            "columns": list(excel_analyzer.df.columns)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar Excel: {str(e)}")


def run_agent_query(question: str, query_id: str):
    """
    Función que ejecuta la consulta del agente en un thread separado.
    """
    global excel_analyzer, agent_instance
    
    try:
        # Cambiar directorio de trabajo
        original_dir = os.getcwd()
        os.chdir(CHARTS_DIR)
        # Ejecutar agente
        result = agent_instance.invoke({"input": question})
        answer = result["output"]
        # Volver al directorio original
        os.chdir(original_dir)
        # Detectar gráficos generados
        charts = []
        chart_files = [
            "cerrados_oct_nov.png",
            "eventos_warning_critical.png",
            "tickets_abiertos_por_mes.png"
        ]
        for chart_file in chart_files:
            chart_path = CHARTS_DIR / chart_file
            if chart_path.exists():
                charts.append(chart_file)
        
        # Actualizar estado
        pending_queries[query_id] = {
            "status": "completed",
            "answer": answer,
            "charts_generated": charts
        }
    
    except Exception as e:
        os.chdir(original_dir)
        pending_queries[query_id] = {
            "status": "error",
            "error": str(e)
        }


@app.post("/ask")
async def ask_question(request: QuestionRequest):
    """
    Endpoint para hacer preguntas sobre el Excel cargado.
    Soporta modo síncrono y asíncrono.
    """
    global excel_analyzer, agent_instance
    
    if excel_analyzer is None or agent_instance is None:
        raise HTTPException(
            status_code=400, 
            detail="Primero debes cargar un archivo Excel usando /upload-excel"
        )
    
    # Modo asíncrono: devuelve ID y procesa en background
    if request.async_mode:
        query_id = str(uuid.uuid4())
        pending_queries[query_id] = {"status": "pending"}
        
        # Ejecutar en background
        loop = asyncio.get_event_loop()
        loop.run_in_executor(executor, run_agent_query, request.question, query_id)
        
        return {
            "query_id": query_id,
            "status": "pending",
            "message": "Consulta en proceso. Usa /query-status/{query_id} para verificar el estado.",
            "check_url": f"/query-status/{query_id}"
        }
    
    # Modo síncrono (comportamiento original, puede dar timeout)
    try:
        original_dir = os.getcwd()
        os.chdir(CHARTS_DIR)
        
        answer = agent_instance.run(request.question)
        
        os.chdir(original_dir)
        
        charts = []
        chart_files = [
            "cerrados_oct_nov.png",
            "eventos_warning_critical.png", 
            "tickets_abiertos_por_mes.png"
        ]
        
        for chart_file in chart_files:
            chart_path = CHARTS_DIR / chart_file
            if chart_path.exists():
                charts.append(chart_file)
        
        return QuestionResponse(
            answer=answer,
            charts_generated=charts
        )
    
    except Exception as e:
        os.chdir(original_dir)
        raise HTTPException(status_code=500, detail=f"Error al procesar pregunta: {str(e)}")


@app.get("/query-status/{query_id}", response_model=QueryStatusResponse)
async def get_query_status(query_id: str):
    """
    Endpoint para verificar el estado de una consulta asíncrona.
    """
    if query_id not in pending_queries:
        raise HTTPException(status_code=404, detail="Query ID no encontrado")
    
    result = pending_queries[query_id]
    
    response = QueryStatusResponse(
        query_id=query_id,
        status=result["status"]
    )
    
    if result["status"] == "completed":
        response.answer = result.get("answer")
        response.charts_generated = result.get("charts_generated", [])
    elif result["status"] == "error":
        response.error = result.get("error")
    
    return response


@app.get("/chart/{chart_name}")
async def get_chart(chart_name: str):
    """
    Endpoint para descargar los gráficos generados.
    """
    chart_path = CHARTS_DIR / chart_name
    
    if not chart_path.exists():
        raise HTTPException(status_code=404, detail="Gráfico no encontrado")
    
    return FileResponse(
        chart_path,
        media_type="image/png",
        filename=chart_name
    )


@app.get("/health")
async def health_check():
    """
    Endpoint para verificar que el servidor está funcionando.
    """
    return {
        "status": "healthy",
        "excel_loaded": excel_analyzer is not None,
        "agent_ready": agent_instance is not None,
        "ollama_model": "llama3"
    }


@app.delete("/reset")
async def reset_system():
    """
    Endpoint para resetear el sistema (limpiar Excel y agente cargados).
    """
    global excel_analyzer, agent_instance
    
    excel_analyzer = None
    agent_instance = None
    tools.excel = None
    pending_queries.clear()
    
    return {"message": "Sistema reseteado exitosamente"}


@app.get("/")
async def root():
    """
    Endpoint raíz con información de la API.
    """
    return {
        "name": "Ollama Excel Analyzer API",
        "version": "1.0",
        "endpoints": {
            "health": "GET /health",
            "upload": "POST /upload-excel",
            "ask_sync": "POST /ask (con async_mode=false)",
            "ask_async": "POST /ask (con async_mode=true)",
            "query_status": "GET /query-status/{query_id}",
            "get_chart": "GET /chart/{chart_name}",
            "reset": "DELETE /reset"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)