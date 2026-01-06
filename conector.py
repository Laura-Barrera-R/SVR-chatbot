import streamlit as st
import requests
from io import BytesIO
from PIL import Image  # Para mostrar imágenes

# Configuración - Tu VM IP
SERVICE_URL = "http://147.224.209.193:8000"
UPLOAD_EXCEL_ENDPOINT = f"{SERVICE_URL}/upload-excel"
ASK_ENDPOINT = f"{SERVICE_URL}/ask"
CHART_ENDPOINT = f"{SERVICE_URL}/chart"
HEALTH_ENDPOINT = f"{SERVICE_URL}/health"
RESET_ENDPOINT = f"{SERVICE_URL}/reset"

st.set_page_config(page_title="Analizador IA Excel", page_icon="🧠", layout="wide")

st.title("🧠 Analizador IA de Excel con Ollama")
st.markdown("Carga un Excel y haz preguntas sobre los datos (ej. 'gráfico de eventos CLOSED en octubre'). El agente genera texto y gráficos.")

# Sidebar para controls
st.sidebar.header("Control del Servicio")
if st.sidebar.button("Ver Status"):
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=10)
        if response.status_code == 200:
            data = response.json()
            st.sidebar.success("✅ Status: Healthy")
            st.sidebar.info(f"Excel cargado: {'Sí' if data['excel_loaded'] else 'No'}")
            st.sidebar.info(f"Agente listo: {'Sí' if data['agent_ready'] else 'No'}")
            st.sidebar.info(f"Modelo Ollama: {data['ollama_model']}")
        else:
            st.sidebar.error(f"❌ Status: {response.status_code}")
    except Exception as e:
        st.sidebar.error(f"❌ Error conexión: {e}")

if st.sidebar.button("Reset Servicio"):
    try:
        response = requests.delete(RESET_ENDPOINT, timeout=10)
        if response.status_code == 200:
            st.sidebar.success("✅ Reseteado (Excel limpiado).")
            st.session_state.clear()
        else:
            st.sidebar.error(f"❌ Reset: {response.status_code}")
    except Exception as e:
        st.sidebar.error(f"❌ Error: {e}")

# Upload Excel
st.sidebar.subheader("Cargar Excel")
uploaded_file = st.sidebar.file_uploader("Elige Excel (.xlsx o .xls)", type=['xlsx', 'xls'])

if uploaded_file is not None:
    if st.sidebar.button("Cargar al Servicio"):
        with st.spinner("Subiendo Excel..."):
            try:
                files = {'file': uploaded_file}
                response = requests.post(UPLOAD_EXCEL_ENDPOINT, files=files, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    st.sidebar.success(f"✅ Cargado: {data['message']}\nFilas: {data['rows']}\nColumnas: {', '.join(data['columns'])}")
                    st.session_state['excel_loaded'] = True
                    st.session_state['excel_data'] = data
                    st.rerun()
                else:
                    st.sidebar.error(f"❌ Error: {response.status_code} - {response.text[:200]}")
            except Exception as e:
                st.sidebar.error(f"❌ Error: {e}")

# Main: Preguntas
if 'excel_loaded' not in st.session_state:
    st.session_state['excel_loaded'] = False

if not st.session_state['excel_loaded']:
    st.warning("⚠️ Carga un Excel en la sidebar para preguntar.")
else:
    st.header("Haz una Pregunta")
    question = st.text_input("Ej: 'muéstrame el gráfico de eventos CLOSED en octubre'", placeholder="Escribe tu pregunta...")
    async_mode = st.checkbox("Modo Asíncrono (para preguntas largas)", value=False)

    if st.button("Enviar Pregunta", type="primary"):
        if question:
            with st.spinner("Procesando con IA... (puede tardar)"):
                try:
                    payload = {"question": question, "async_mode": async_mode}
                    response = requests.post(ASK_ENDPOINT, json=payload, timeout=120 if async_mode else 60)
                    if response.status_code == 200:
                        data = response.json()
                        st.success("✅ Respuesta generada!")
                        
                        # Texto
                        st.subheader("Respuesta")
                        st.write(data['answer'])
                        
                        # Gráficos
                        charts = data.get('charts_generated', [])
                        if charts:
                            st.subheader("Gráficos")
                            cols = st.columns(len(charts))
                            for idx, chart_name in enumerate(charts):
                                with cols[idx]:
                                    url = f"{CHART_ENDPOINT}/{chart_name}"
                                    try:
                                        img_resp = requests.get(url, timeout=10)
                                        if img_resp.status_code == 200:
                                            img = Image.open(BytesIO(img_resp.content))
                                            st.image(img, caption=chart_name, use_column_width=True)
                                        else:
                                            st.error(f"Error {chart_name}: {img_resp.status_code}")
                                    except Exception as e:
                                        st.error(f"Error imagen {chart_name}: {e}")
                        else:
                            st.info("No gráficos generados.")
                    else:
                        st.error(f"❌ Error: {response.status_code} - {response.text[:200]}")
                except Exception as e:
                    st.error(f"❌ Error conexión: {e}")
        else:
            st.warning("Escribe una pregunta.")

st.markdown("---")
st.markdown("Backend: FastAPI + LangChain + Ollama | Frontend: Streamlit")