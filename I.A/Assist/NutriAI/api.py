from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from nutri import NutritionistAgent
import os, uuid, logging

# Configuração básica
app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache de agentes por session_id
agent_cache = {}

# Factory para obter/criar agente para uma sessão específica
def get_agent(session_id: str):
    global agent_cache
    if not session_id:
        session_id = 'anon'

    if session_id in agent_cache:
        return agent_cache[session_id]

    logger.info(f"Criando novo NutritionistAgent para session_id={session_id}")

    # Se quiser, carregue configurações do MySQL via env e repasse como mysql_config
    mysql_config = None
    agent = NutritionistAgent(session_id=session_id, mysql_config=mysql_config)
    agent_cache[session_id] = agent
    return agent

# Pasta para uploads temporários
UPLOAD_FOLDER = "temp_uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Rota que serve o template HTML
@app.route("/", methods=["GET"])
def home():
    # Espera que exista templates/index.html
    return render_template('index.html')

# Rota para obter histórico de chat de uma sessão específica
@app.route("/chat_history", methods=["GET"])
def chat_history():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"success": False, "error": "session_id não informado"}), 400

    try:
        agent = get_agent(session_id)
        history = agent.get_conversation_history()  # retorna lista de dicts
        return jsonify({"success": True, "history": history})
    except Exception as e:
        logger.exception("Erro ao buscar histórico")
        return jsonify({"success": False, "error": "Erro ao buscar histórico"}), 500

# Rota de health (status)
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

# Rota de chat
@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return jsonify({"message": "OK"}), 200

    try:
        # Obter session_id (prioridade: header X-Session-ID -> form -> json -> gerar)
        session_id = request.headers.get('X-Session-ID')
        if not session_id:
            session_id = request.form.get('session_id')
        if not session_id and request.is_json:
            session_id = request.get_json().get('session_id')

        # Se ainda não tem, tente criar/retornar para o cliente
        if not session_id:
            # gera um id temporário e devolve no payload
            session_id = str(uuid.uuid4())

        # Mensagem do usuário (form-data ou json)
        message = request.form.get('message')
        if not message and request.is_json:
            data = request.get_json()
            message = data.get('message')

        if not message:
            return jsonify({"error": "Nenhuma mensagem enviada"}), 400

        logger.info(f"[{session_id}] Mensagem recebida: {message}")

        agent = get_agent(session_id)
        response = agent.run_text(message)

        logger.info(f"[{session_id}] Resposta gerada")

        return jsonify({
            "success": True,
            "session_id": session_id,
            "response": response
        })

    except Exception as e:
        logger.exception("Erro no endpoint /chat")
        return jsonify({"success": False, "error": "Erro interno no servidor"}), 500

# Rota de análise de imagem
@app.route("/analyze_image", methods=["POST", "OPTIONS"])
def analyze_image():
    if request.method == "OPTIONS":
        return jsonify({"message": "OK"}), 200

    try:
        session_id = request.headers.get('X-Session-ID') or request.form.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())

        if 'file' not in request.files:
            return jsonify({"error": "Nenhum arquivo enviado"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Nenhum arquivo selecionado"}), 400

        file_ext = os.path.splitext(file.filename)[1]
        temp_file_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}{file_ext}")

        file.save(temp_file_path)

        agent = get_agent(session_id)
        analysis_result = agent.run_image(temp_file_path)

        return jsonify({
            "success": True,
            "session_id": session_id,
            "response": analysis_result
        })

    except Exception as e:
        logger.exception("Erro no endpoint /analyze_image")
        return jsonify({"success": False, "error": "Erro na análise"}), 500

    finally:
        try:
            if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        except Exception:
            logger.exception("Erro ao remover arquivo temporário")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv('PORT', 8000)))
