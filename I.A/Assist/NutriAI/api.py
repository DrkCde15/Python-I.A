from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from nutri import NutritionistAgent
import mysql.connector
import os, uuid, logging

# Configuração básica
app = Flask(__name__)
CORS(app)
app.secret_key = "uma_chave_secreta_forte_aqui"
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache de agentes por session_id
agent_cache = {}

def get_agent(session_id: str):
    global agent_cache
    if not session_id:
        session_id = 'anon'

    if session_id in agent_cache:
        return agent_cache[session_id]

    logger.info(f"Criando novo NutritionistAgent para session_id={session_id}")
    mysql_config = None
    agent = NutritionistAgent(session_id=session_id, mysql_config=mysql_config)
    agent_cache[session_id] = agent
    return agent

# Conexão MySQL
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password=os.getenv('MYSQL_PASSWORD', ''),
        database='nutri_chat_teste'
    )

# Pasta para uploads temporários
UPLOAD_FOLDER = "temp_uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- ROTAS DE AUTENTICAÇÃO ----------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        birth_date = request.form.get("birth_date")
        gender = request.form.get("gender")
        email = request.form.get("email")
        password = request.form.get("password")

        if not all([first_name, last_name, birth_date, gender, email, password]):
            flash("Preencha todos os campos!", "error")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
            if cursor.fetchone():
                flash("E-mail já cadastrado!", "error")
                return redirect(url_for("register"))

            cursor.execute("""
                INSERT INTO users (first_name, last_name, birth_date, gender, email, password)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (first_name, last_name, birth_date, gender, email, hashed_password))
            conn.commit()
            flash("Cadastro realizado! Faça login.", "success")
            return redirect(url_for("login"))
        finally:
            cursor.close()
            conn.close()
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
            user = cursor.fetchone()

            if not user or not check_password_hash(user["password"], password):
                flash("E-mail ou senha inválidos!", "error")
                return redirect(url_for("login"))

            session["user_id"] = user["id"]
            session["user_name"] = user["first_name"]
            return redirect(url_for("chat_page"))

        finally:
            cursor.close()
            conn.close()

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------- ROTAS DO CHAT ----------------

@app.route("/chat_page")
def chat_page():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template('chat.html')

@app.route("/chat_history", methods=["GET"])
def chat_history():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"success": False, "error": "session_id não informado"}), 400

    try:
        agent = get_agent(session_id)
        history = agent.get_conversation_history()
        return jsonify({"success": True, "history": history})
    except Exception as e:
        logger.exception("Erro ao buscar histórico")
        return jsonify({"success": False, "error": "Erro ao buscar histórico"}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return jsonify({"message": "OK"}), 200
    try:
        session_id = request.headers.get('X-Session-ID') or request.form.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())

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

        return jsonify({"success": True, "session_id": session_id, "response": response})

    except Exception as e:
        logger.exception("Erro no endpoint /chat")
        return jsonify({"success": False, "error": "Erro interno no servidor"}), 500

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

        return jsonify({"success": True, "session_id": session_id, "response": analysis_result})

    except Exception as e:
        logger.exception("Erro no endpoint /analyze_image")
        return jsonify({"success": False, "error": "Erro na análise"}), 500

    finally:
        try:
            if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        except Exception:
            logger.exception("Erro ao remover arquivo temporário")

# ---------------- ROTA HOME ----------------
@app.route("/", methods=["GET"])
def home():
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv('PORT', 8000)))
