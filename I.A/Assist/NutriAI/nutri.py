from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from dotenv import load_dotenv
from food_analyser import FoodAnalyser
import os, warnings, traceback
import mysql.connector
from datetime import datetime
from typing import List, Optional

warnings.filterwarnings("ignore", category=DeprecationWarning)

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise EnvironmentError("GOOGLE_API_KEY não definida no .env")
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY


class MySQLChatHistory:
    def __init__(self, session_id: str, user_id: Optional[int], email: Optional[str], mysql_config: dict):
        self.session_id = session_id
        self.user_id = user_id
        self.email = email
        self.mysql_config = mysql_config
        self.connection = None
        self._ensure_connection()
        self._create_tables()

    def _ensure_connection(self):
        try:
            if self.connection is None or not self.connection.is_connected():
                self.connection = mysql.connector.connect(**self.mysql_config)
        except Exception as e:
            print(f"Erro ao conectar MySQL: {e}")
            raise

    def _create_tables(self):
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    session_id VARCHAR(255) NOT NULL,
                    user_id INT NULL,
                    email VARCHAR(255) NULL,
                    message_type ENUM('human', 'ai') NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_session_id (session_id),
                    INDEX idx_user_id (user_id),
                    INDEX idx_email (email),
                    INDEX idx_timestamp (timestamp)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)
            self.connection.commit()
            cursor.close()
        except Exception as e:
            print(f"Erro ao criar tabelas: {e}")
            raise

    def add_message(self, message: BaseMessage):
        self._ensure_connection()
        try:
            cursor = self.connection.cursor()
            message_type = "human" if isinstance(message, HumanMessage) else "ai"
            cursor.execute(
                """
                INSERT INTO chat_history (session_id, user_id, email, message_type, content, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    self.session_id,
                    self.user_id,
                    self.email,
                    message_type,
                    message.content,
                    datetime.now(),
                )
            )
            self.connection.commit()
            cursor.close()
        except Exception as e:
            print(f"Erro ao adicionar mensagem: {e}")
            self.connection = None
            self._ensure_connection()

    def get_messages(self, by_user: bool = False) -> List[BaseMessage]:
        self._ensure_connection()
        try:
            cursor = self.connection.cursor()
            if by_user and self.user_id:
                cursor.execute(
                    """
                    SELECT message_type, content, timestamp
                    FROM chat_history
                    WHERE user_id = %s
                    ORDER BY timestamp ASC
                    """,
                    (self.user_id,)
                )
            else:
                cursor.execute(
                    """
                    SELECT message_type, content, timestamp
                    FROM chat_history
                    WHERE session_id = %s
                    ORDER BY timestamp ASC
                    """,
                    (self.session_id,)
                )
            results = cursor.fetchall()
            cursor.close()

            messages = []
            for message_type, content, _ in results:
                if message_type == "human":
                    messages.append(HumanMessage(content=content))
                else:
                    messages.append(AIMessage(content=content))
            return messages
        except Exception as e:
            print(f"Erro ao recuperar mensagens: {e}")
            self.connection = None
            self._ensure_connection()
            return []

    def clear(self):
        self._ensure_connection()
        try:
            cursor = self.connection.cursor()
            if self.user_id:
                cursor.execute("DELETE FROM chat_history WHERE user_id = %s", (self.user_id,))
            else:
                cursor.execute("DELETE FROM chat_history WHERE session_id = %s", (self.session_id,))
            self.connection.commit()
            cursor.close()
        except Exception as e:
            print(f"Erro ao limpar histórico: {e}")

    def __del__(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()


class CustomConversationBufferMemory(ConversationBufferMemory):
    def __init__(self, chat_history: MySQLChatHistory, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, "chat_history_backend", chat_history)
        self.chat_memory.messages = self.chat_history_backend.get_messages()

    def save_context(self, inputs: dict, outputs: dict):
        super().save_context(inputs, outputs)
        if self.chat_memory.messages:
            recent_messages = self.chat_memory.messages[-2:]
            for message in recent_messages:
                self.chat_history_backend.add_message(message)

    def clear(self):
        super().clear()
        self.chat_history_backend.clear()


class NutritionistAgent:
    def __init__(self, session_id: str, mysql_config: dict = None, user_id: Optional[int] = None, email: Optional[str] = None):
        self.session_id = session_id
        self.user_id = user_id
        self.email = email
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)

        system_prompt = """
        Você é uma nutricionista virtual especializada em nutrição esportiva.
        - Sempre que você receber um "oi" ou "olá", responda com "Olá sou seu assistente de I.A, em que posso ajudar hoje sobre treinos ou dietas?"
        - Sugestões de refeições detalhadas e tabela nutricional.
        - Treinos adaptados conforme objetivo.
        - Comunicação clara, objetiva e motivadora.
        - Se o usuário pedir algo fora do escopo, responda "Desculpe, não posso ajudar com isso, pois estou aqui para ajudar com treinos e dietas."
        """

        if mysql_config is None:
            mysql_config = {
                "host": os.getenv("MYSQL_HOST", "localhost"),
                "port": int(os.getenv("MYSQL_PORT", 3306)),
                "user": os.getenv("MYSQL_USER", "root"),
                "password": os.getenv("MYSQL_PASSWORD", ""),
                "database": os.getenv("MYSQL_DATABASE", "nutri_chat"),
                "charset": "utf8mb4",
                "autocommit": True,
                "connection_timeout": 60,
            }

        self.chat_history = MySQLChatHistory(
            session_id=session_id,
            mysql_config=mysql_config,
            user_id=user_id,
            email=email,
        )

        self.memory = CustomConversationBufferMemory(
            chat_history=self.chat_history,
            memory_key="chat_history",
            return_messages=True,
        )

        self.agent = initialize_agent(
            llm=self.llm,
            tools=[],
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=False,
            memory=self.memory,
            agent_kwargs={"system_message": system_prompt},
        )

        self.analyser = FoodAnalyser()

    def run_text(self, input_text: str) -> str:
        try:
            response = self.agent.invoke({"input": input_text})
            return response.get("output") if isinstance(response, dict) else response
        except Exception:
            print(f"Erro chat: {traceback.format_exc()}")
            return "Desculpe, não foi possível processar sua solicitação."

    def run_image(self, image_path: str) -> str:
        try:
            result = self.analyser._run(image_path)
            self.memory.save_context(
                {"input": f"Análise de imagem: {image_path}"}, {"output": result}
            )
            return result
        except Exception:
            print(f"Erro imagem: {traceback.format_exc()}")
            return "Não foi possível analisar a imagem."

    def get_conversation_history(self, by_user: bool = False) -> List[dict]:
        messages = self.chat_history.get_messages(by_user=by_user)
        history = []
        for msg in messages:
            history.append(
                {
                    "type": "human" if isinstance(msg, HumanMessage) else "ai",
                    "content": msg.content,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        return history

    def clear_history(self):
        self.memory.clear()
