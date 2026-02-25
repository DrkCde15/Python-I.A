from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from Nutri import NutritionistAgent
import mysql.connector
import os, uuid, logging
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import secrets

# ---------------- Configurações ----------------
app = Flask(__name__)

# Chave secreta
app.secret_key = os.getenv("FLASK_SECRET_KEY", "uma_chave_secreta_forte_aqui")

# Configuração de cookies de sessão
app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",  # Funciona bem em localhost
    SESSION_COOKIE_SECURE=False,    # HTTPS = True, localhost = False
)

# CORS
CORS(app, resources={r"/*": {"origins": "http://localhost:4200"}}, supports_credentials=True)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UPLOAD_FOLDER = r"C:\Users\Júlio César\Pictures\Uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- Conexão MySQL ----------------
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', ''),
        database=os.getenv('MYSQL_DATABASE', 'nutrinow2')
    )

# ---------------- Cache de agentes ----------------
agent_cache = {}
def get_agent(session_id: str, user_id: int = None, email: str = None):
    global agent_cache
    if not session_id:
        session_id = 'anon'
    key = f"{user_id}_{session_id}"
    if key in agent_cache:
        return agent_cache[key]
    logger.info(f"Criando novo NutritionistAgent para user_id={user_id}, session_id={session_id}")
    mysql_config = None
    agent = NutritionistAgent(session_id=session_id, mysql_config=mysql_config, user_id=user_id, email=email)
    agent_cache[key] = agent
    return agent

# ---------------- Rotas de autenticação ----------------
@app.route("/cadastro", methods=["POST"])
def cadastro():
    data = request.get_json()
    nome = data.get("nome")
    sobrenome = data.get("sobrenome")
    data_nascimento = data.get("data_nascimento")
    genero = data.get("genero")
    email = data.get("email")
    senha = data.get("senha")

    if not all([nome, sobrenome, email, senha]):
        return jsonify({"error": "Campos obrigatórios ausentes"}), 400

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Verifica se o email já existe
        cursor.execute("SELECT id FROM usuarios WHERE email=%s", (email,))
        if cursor.fetchone():
            return jsonify({"error": "Email já cadastrado"}), 409

        # Cria hash da senha
        senha_hash = generate_password_hash(senha)

        # Insere o usuário no banco
        cursor.execute("""
            INSERT INTO usuarios (nome, sobrenome, data_nascimento, genero, email, senha)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (nome, sobrenome, data_nascimento, genero, email, senha_hash))
        conn.commit()

        return jsonify({"message": "Conta criada com sucesso!"}), 201

    except mysql.connector.Error as e:
        logger.error(f"Erro MySQL: {e}")
        return jsonify({"error": "Erro no banco de dados"}), 500

    except Exception as e:
        logger.error(f"Erro ao criar conta: {e}")
        return jsonify({"error": "Erro interno ao criar conta"}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    senha = data.get("senha")
    if not email or not senha:
        return jsonify({"error": "Email e senha são obrigatórios"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, nome, email, senha FROM usuarios WHERE email=%s", (email,))
        user = cursor.fetchone()
        if not user or not check_password_hash(user["senha"], senha):
            return jsonify({"error": "Email ou senha inválidos"}), 401

        # Cria sessão Flask
        session["user_id"] = user["id"]
        session["user_name"] = user["nome"]
        session["user_email"] = user["email"]

        return jsonify({
            "message": "Login realizado com sucesso!",
            "user": {"id": user["id"], "nome": user["nome"], "email": user["email"]}
        }), 200
    finally:
        cursor.close()
        conn.close()

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logout realizado"}), 200

# ---------------- Rotas do chatbot ----------------
@app.route("/chat", methods=["POST"])
def chat():
    if "user_id" not in session:
        return jsonify({"error": "Usuário não autenticado"}), 401

    session_id = request.headers.get("X-Session-ID") or str(uuid.uuid4())
    user_id = session.get("user_id")
    email = session.get("user_email")
    data = request.get_json()
    message = data.get("message")
    if not message:
        return jsonify({"error": "Mensagem vazia"}), 400

    agent = get_agent(session_id=session_id, user_id=user_id, email=email)
    response_text = agent.run_text(message)
    return jsonify({"success": True, "session_id": session_id, "response": response_text}), 200

@app.route("/chat_history", methods=["GET"])
def chat_history():
    if "user_id" not in session:
        return jsonify({"error": "Usuário não autenticado"}), 401

    session_id = request.args.get("session_id") or str(uuid.uuid4())
    user_id = session.get("user_id")
    agent = get_agent(session_id=session_id, user_id=user_id)
    history = agent.get_conversation_history(by_user=True)
    return jsonify({"success": True, "history": history})

@app.route("/analyze_image", methods=["POST", "OPTIONS"])
def analyze_image():
    if request.method == "OPTIONS":
        return jsonify({"message": "OK"}), 200

    try:
        # Recupera sessão
        session_id = request.headers.get('X-Session-ID') or request.form.get('session_id')
        user_id = session.get("user_id")
        email = session.get("user_email")
        if not session_id:
            session_id = str(uuid.uuid4())
        if not user_id:
            return jsonify({"error": "Usuário não autenticado"}), 401

        # Verifica se veio arquivo
        if 'file' not in request.files:
            return jsonify({"error": "Nenhum arquivo enviado"}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Nenhum arquivo selecionado"}), 400

        # Define message_type (default 'human')
        message_type = request.form.get('message_type', 'human')
        if message_type not in ['human', 'ai']:
            return jsonify({"error": "message_type inválido"}), 400

        # Salva arquivo no servidor
        file_ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        # Salva no banco de dados
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO uploads (user_id, file_path, uploaded_at, message_type) VALUES (%s, %s, NOW(), %s)",
            (user_id, file_path, message_type)
        )
        conn.commit()
        cursor.close()
        conn.close()

        # Processa imagem com o agente
        agent = get_agent(session_id=session_id, user_id=user_id, email=email)
        analysis_result = agent.run_image(file_path)

        return jsonify({
            "success": True,
            "session_id": session_id,
            "file_path": file_path,
            "message_type": message_type,
            "response": analysis_result
        }), 200

    except Exception as e:
        logger.exception("Erro no endpoint /analyze_image")
        return jsonify({"success": False, "error": str(e)}), 500

# ---------------- Health check ----------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

# ---------------- Headers CORS extra para pré-flight ----------------
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response
#--------------- Envia email e recupera a senha ------------------------
# -----------------------------
# Função de envio de email
# -----------------------------
def enviar_email(destinatario, assunto, mensagem_html):
    remetente = "nnutrinow@gmail.com"
    senha = "tdngwxjbhiznkrlr"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"] = remetente
    msg["To"] = destinatario
    msg.attach(MIMEText(mensagem_html, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(remetente, senha)
            server.sendmail(remetente, destinatario, msg.as_string())
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar email: {e}")
        return False


# -----------------------------
# Endpoint: Esqueci minha senha
# -----------------------------
@app.route('/esqueci-senha', methods=['POST'])
def esqueci_senha():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'error': 'O email é obrigatório.'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)  # <--- aqui
        cursor.execute("SELECT id, nome FROM usuarios WHERE email=%s", (email,))
        usuario = cursor.fetchone()

        if not usuario:
            return jsonify({'message': 'Email não cadastrado.'}), 404

        token = secrets.token_urlsafe(32)
        expiracao = datetime.now() + timedelta(hours=1)

        cursor.execute("""
            INSERT INTO redefinicao_senha (usuario_id, token, data_expiracao)
            VALUES (%s, %s, %s)
        """, (usuario['id'], token, expiracao))
        conn.commit()

        link_reset = f"http://localhost:4200/redefinir-senha?token={token}"
        mensagem_html = f"""
        <html>
        <body>
            <h2>Redefinição de Senha - NutriNow</h2>
            <p>Olá, {usuario['nome']}!</p>
            <p>Clique no link abaixo para redefinir sua senha (válido por 1 hora):</p>
            <a href="{link_reset}" target="_blank">Redefinir minha senha</a>
            <br><br>
            <p>Se você não fez esta solicitação, ignore este e-mail.</p>
        </body>
        </html>
        """

        if enviar_email(email, "Recuperação de Senha - NutriNow", mensagem_html):
            return jsonify({'message': 'As instruções foram enviadas para o e-mail.'}), 200
        else:
            return jsonify({'error': 'Falha ao enviar o e-mail.'}), 500

    except mysql.connector.Error as err:
        logger.error(f"Erro MySQL: {err}")
        return jsonify({'error': str(err)}), 500
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()


# -----------------------------
# Endpoint: Redefinir senha
# -----------------------------
@app.route('/redefinir-senha', methods=['POST'])
def redefinir_senha():
    data = request.get_json()
    token = data.get('token')
    nova_senha = data.get('nova_senha')

    if not token or not nova_senha:
        return jsonify({'error': 'Token e nova senha são obrigatórios.'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)  # <--- aqui

        cursor.execute("""
            SELECT usuario_id FROM redefinicao_senha
            WHERE token=%s AND data_expiracao > NOW()
        """, (token,))
        registro = cursor.fetchone()

        if not registro:
            return jsonify({'error': 'Token inválido ou expirado.'}), 400

        senha_hash = generate_password_hash(nova_senha)
        cursor.execute("UPDATE usuarios SET senha=%s WHERE id=%s", (senha_hash, registro['usuario_id']))
        cursor.execute("DELETE FROM redefinicao_senha WHERE token=%s", (token,))
        conn.commit()

        return jsonify({'message': 'Senha redefinida com sucesso!'}), 200

    except mysql.connector.Error as err:
        logger.error(f"Erro MySQL: {err}")
        return jsonify({'error': str(err)}), 500
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

# -----------------------------
# Endpoint: perfil
# -----------------------------
@app.route('/perfil', methods=['GET'])
def get_perfil():
    if "user_id" not in session:
        return jsonify({"error": "Usuário não autenticado"}), 401

    user_id = session["user_id"]

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT u.nome, u.email, u.data_nascimento, 
                   IFNULL(p.meta, 'Não definida') AS meta, 
                   IFNULL(p.altura_peso, '-- / --') AS altura_peso
            FROM usuarios u
            LEFT JOIN perfil p ON u.id = p.usuario_id
            WHERE u.id = %s
        """, (user_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"error": "Usuário não encontrado"}), 404

        return jsonify({
            "success": True,
            "nome": user["nome"],
            "email": user["email"],
            "dataNascimento": user["data_nascimento"].strftime("%d/%m/%Y") if user["data_nascimento"] else "--/--/----",
            "meta": user["meta"],
            "alturaPeso": user["altura_peso"]
        }), 200

    except mysql.connector.Error as err:
        logger.error(f"Erro MySQL ao buscar perfil: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()


@app.route('/perfil', methods=['POST'])
def update_perfil():
    if "user_id" not in session:
        return jsonify({"error": "Usuário não autenticado"}), 401

    data = request.get_json()
    nome = data.get('nome')
    email = data.get('email')
    data_nascimento = data.get('dataNascimento')
    meta = data.get('meta')
    altura_peso = data.get('alturaPeso')

    user_id = session["user_id"]

    try:
        # Converte data dd/mm/yyyy → yyyy-mm-dd
        if data_nascimento:
            try:
                data_nascimento = datetime.strptime(data_nascimento, "%d/%m/%Y").strftime("%Y-%m-%d")
            except ValueError:
                return jsonify({"error": "Formato de data inválido. Use dd/mm/yyyy"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Atualiza tabela usuarios
        if any([nome, email, data_nascimento]):
            query_parts = []
            params = []
            if nome:
                query_parts.append("nome=%s")
                params.append(nome)
            if email:
                query_parts.append("email=%s")
                params.append(email)
            if data_nascimento:
                query_parts.append("data_nascimento=%s")
                params.append(data_nascimento)
            params.append(user_id)
            cursor.execute(f"UPDATE usuarios SET {', '.join(query_parts)} WHERE id=%s", tuple(params))

        # Atualiza ou insere tabela perfil
        cursor.execute("SELECT usuario_id FROM perfil WHERE usuario_id=%s", (user_id,))
        if cursor.fetchone():
            cursor.execute(
                "UPDATE perfil SET meta=%s, altura_peso=%s WHERE usuario_id=%s",
                (meta, altura_peso, user_id)
            )
        else:
            cursor.execute(
                "INSERT INTO perfil (usuario_id, meta, altura_peso) VALUES (%s, %s, %s)",
                (user_id, meta, altura_peso)
            )

        conn.commit()
        return jsonify({"success": True, "message": "Perfil atualizado com sucesso!"}), 200

    except mysql.connector.Error as err:
        logger.error(f"Erro MySQL ao atualizar perfil: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()


@app.route('/perfil', methods=['DELETE'])
def delete_perfil():
    if "user_id" not in session:
        return jsonify({"error": "Usuário não autenticado"}), 401

    user_id = session["user_id"]

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM perfil WHERE usuario_id=%s", (user_id,))
        cursor.execute("DELETE FROM usuarios WHERE id=%s", (user_id,))
        conn.commit()

        session.clear()
        return jsonify({"success": True, "message": "Conta e perfil excluídos com sucesso!"}), 200

    except mysql.connector.Error as err:
        logger.error(f"Erro MySQL ao excluir perfil: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

# ----------------------------- 
# Endpoint: Dieta-Treino Ajustado
# -----------------------------

# ------------------------ GET ------------------------
@app.route('/dieta-treino', methods=['GET'])
def get_items():
    if "user_id" not in session:
        return jsonify({"error": "Usuário não autenticado"}), 401

    user_id = session["user_id"]
    aba = request.args.get('tipo', 'treinos')

    # Normaliza o tipo
    tipo_raw = str(aba).lower()
    tipo = 'treino' if 'treino' in tipo_raw else 'dieta'

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, title, description, time, tipo, created_at, updated_at
            FROM dieta_treino
            WHERE user_id=%s AND tipo=%s
            ORDER BY created_at ASC
        """, (user_id, tipo))
        items = cursor.fetchall()
        return jsonify({"success": True, "items": items}), 200
    except Exception as e:
        print(f"[ERRO][GET] {e}")
        return jsonify({"error": "Falha ao buscar itens"}), 500
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

# ------------------------ POST ------------------------
@app.route('/dieta-treino', methods=['POST'])
def add_item():
    if "user_id" not in session:
        return jsonify({"error": "Usuário não autenticado"}), 401

    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    time = data.get('time')
    aba = str(data.get('tipo', '')).lower()

    if not all([title, description, aba]):
        return jsonify({"error": "Campos obrigatórios ausentes"}), 400

    tipo = 'treino' if 'treino' in aba else 'dieta'
    user_id = session["user_id"]

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO dieta_treino (user_id, tipo, title, description, time)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, tipo, title, description, time))
        conn.commit()
        return jsonify({"success": True, "message": "Item adicionado com sucesso!"}), 201
    except Exception as e:
        print(f"[ERRO][POST] {e}")
        return jsonify({"error": "Falha ao adicionar item"}), 500
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

# ------------------------ PUT ------------------------
@app.route('/dieta-treino/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    if "user_id" not in session:
        return jsonify({"error": "Usuário não autenticado"}), 401

    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    time = data.get('time')
    aba = str(data.get('tipo', '')).lower()

    if not all([title, description, aba]):
        return jsonify({"error": "Campos obrigatórios ausentes"}), 400

    tipo = 'treino' if 'treino' in aba else 'dieta'
    user_id = session["user_id"]

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE dieta_treino
            SET title=%s, description=%s, time=%s, tipo=%s, updated_at=%s
            WHERE id=%s AND user_id=%s
        """, (title, description, time, tipo, datetime.now(), item_id, user_id))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Item não encontrado"}), 404

        return jsonify({"success": True, "message": "Item atualizado com sucesso!"}), 200
    except Exception as e:
        print(f"[ERRO][PUT] {e}")
        return jsonify({"error": "Falha ao atualizar item"}), 500
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

# ------------------------ DELETE ------------------------
@app.route('/dieta-treino/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    if "user_id" not in session:
        return jsonify({"error": "Usuário não autenticado"}), 401

    user_id = session["user_id"]

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM dieta_treino
            WHERE id = %s AND user_id = %s
        """, (item_id, user_id))

        conn.commit()
        return jsonify({"success": True, "message": "Item excluído com sucesso!"}), 200

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# ---------------- Executar ----------------
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", 8000)), debug=True)
