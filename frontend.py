from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import requests
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Config backend (tu VM)
BACKEND_URL = "http://147.224.209.193:8000"

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/upload-excel', methods=['POST'])
def upload_excel():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    
    # Llama a tu backend (tu curl 1)
    try:
        files = {'file': (secure_filename(file.filename), file.stream, file.content_type)}
        response = requests.post(f"{BACKEND_URL}/upload-excel", files=files, timeout=30)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    question = data.get('question', '')
    async_mode = data.get('async_mode', False)
    
    if not question:
        return jsonify({'error': 'No question'})
    
    # Llama a tu backend (tu curl 2 para sync)
    try:
        payload = {"question": question, "async_mode": async_mode}
        response = requests.post(f"{BACKEND_URL}/ask", json=payload, timeout=60)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/query-status', methods=['POST'])
def query_status():
    data = request.json
    query_id = data.get('query_id', '')
    
    if not query_id:
        return jsonify({'error': 'No query_id'})
    
    # Llama a tu backend (tu curl 4)
    try:
        response = requests.get(f"{BACKEND_URL}/query-status/{query_id}", timeout=10)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/chart/<chart_name>')
def get_chart(chart_name):
    # Llama a tu backend (tu curl 5)
    try:
        response = requests.get(f"{BACKEND_URL}/chart/{chart_name}", timeout=10)
        return response.content, 200, {'Content-Type': 'image/png'}
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/health')
def health():
    # Llama a tu backend
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/reset')
def reset():
    # Llama a tu backend
    try:
        response = requests.delete(f"{BACKEND_URL}/reset", timeout=10)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)