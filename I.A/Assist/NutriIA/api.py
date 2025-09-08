from flask import Flask, request, jsonify
from flask_cors import CORS
from nutri import NutritionistAgent
import os, uuid

app = Flask(__name__)

# Configuração CORS mais específica
CORS(app, origins=["http://localhost:4200", "http://127.0.0.1:4200"])

agent = NutritionistAgent(session_id="usuario_api")
UPLOAD_FOLDER = "temp_uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Rota de teste
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "API Flask funcionando!", "status": "ok"})

# Rota de chat
@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return jsonify({"message": "OK"}), 200
    
    try:
        # Tenta pegar da form-data primeiro
        message = request.form.get("message")
        
        # Se não encontrar, tenta JSON
        if not message and request.is_json:
            data = request.get_json()
            message = data.get("message")
        
        if not message:
            return jsonify({"error": "Nenhuma mensagem enviada"}), 400
        
        print(f"Mensagem recebida: {message}")  # Debug
        response = agent.run_text(message)
        print(f"Resposta gerada: {response}")   # Debug
        
        return jsonify({"response": response, "status": "success"})
    
    except Exception as e:
        print(f"Erro: {str(e)}")  # Debug
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

# Rota de análise de imagem
@app.route("/analyze_image", methods=["POST", "OPTIONS"])
def analyze_image():
    if request.method == "OPTIONS":
        return jsonify({"message": "OK"}), 200
        
    if "file" not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    file = request.files["file"]
    if file.filename == '':
        return jsonify({"error": "Nenhum arquivo selecionado"}), 400

    file_ext = os.path.splitext(file.filename)[1]
    temp_file_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}{file_ext}")

    try:
        file.save(temp_file_path)
        analysis_result = agent.run_image(temp_file_path)
        return jsonify({"response": analysis_result, "status": "success"})
    except Exception as e:
        return jsonify({"error": f"Erro na análise: {str(e)}"}), 500
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8000)