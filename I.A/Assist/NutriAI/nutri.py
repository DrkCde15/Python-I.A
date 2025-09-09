# nutri.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from dotenv import load_dotenv
from food_analyser import FoodAnalyser
import os, warnings, traceback
import mysql.connector
from datetime import datetime
from typing import List

warnings.filterwarnings("ignore", category=DeprecationWarning)

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise EnvironmentError("GOOGLE_API_KEY não definida no .env")
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

class MySQLChatHistory:
    """Classe customizada para gerenciar histórico de chat no MySQL"""
    
    def __init__(self, session_id: str, mysql_config: dict):
        self.session_id = session_id
        self.mysql_config = mysql_config
        self.connection = None
        self._ensure_connection()
        self._create_tables()

    def _ensure_connection(self):
        """Garante que a conexão com MySQL está ativa"""
        try:
            if self.connection is None or not self.connection.is_connected():
                self.connection = mysql.connector.connect(**self.mysql_config)
        except Exception as e:
            print(f"Erro ao conectar MySQL: {e}")
            raise

    def _create_tables(self):
        """Cria as tabelas necessárias se não existirem"""
        try:
            cursor = self.connection.cursor()
            
            create_table_query = """
            CREATE TABLE IF NOT EXISTS chat_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id VARCHAR(255) NOT NULL,
                message_type ENUM('human', 'ai') NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_session_id (session_id),
                INDEX idx_timestamp (timestamp)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            
            cursor.execute(create_table_query)
            self.connection.commit()
            cursor.close()
            
        except Exception as e:
            print(f"Erro ao criar tabelas: {e}")
            raise

    def add_message(self, message: BaseMessage):
        """Adiciona uma mensagem ao histórico"""
        self._ensure_connection()
        
        try:
            cursor = self.connection.cursor()
            
            message_type = 'human' if isinstance(message, HumanMessage) else 'ai'
            content = message.content
            
            insert_query = """
            INSERT INTO chat_history (session_id, message_type, content, timestamp)
            VALUES (%s, %s, %s, %s)
            """
            
            cursor.execute(insert_query, (
                self.session_id, 
                message_type, 
                content, 
                datetime.now()
            ))
            
            self.connection.commit()
            cursor.close()
            
        except Exception as e:
            print(f"Erro ao adicionar mensagem: {e}")
            # Reconectar em caso de erro
            self.connection = None
            self._ensure_connection()

    def get_messages(self) -> List[BaseMessage]:
        """Recupera todas as mensagens da sessão"""
        self._ensure_connection()
        
        try:
            cursor = self.connection.cursor()
            
            select_query = """
            SELECT message_type, content, timestamp 
            FROM chat_history 
            WHERE session_id = %s 
            ORDER BY timestamp ASC
            """
            
            cursor.execute(select_query, (self.session_id,))
            results = cursor.fetchall()
            cursor.close()
            
            messages = []
            for message_type, content, timestamp in results:
                if message_type == 'human':
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
        """Limpa o histórico da sessão"""
        self._ensure_connection()
        
        try:
            cursor = self.connection.cursor()
            delete_query = "DELETE FROM chat_history WHERE session_id = %s"
            cursor.execute(delete_query, (self.session_id,))
            self.connection.commit()
            cursor.close()
            
        except Exception as e:
            print(f"Erro ao limpar histórico: {e}")

    def __del__(self):
        """Fecha a conexão quando o objeto é destruído"""
        if self.connection and self.connection.is_connected():
            self.connection.close()

class CustomConversationBufferMemory(ConversationBufferMemory):
    """Memória customizada que usa MySQL como backend"""
    
    def __init__(self, chat_history: MySQLChatHistory, **kwargs):
        super().__init__(**kwargs)
        # usar object.__setattr__ para evitar conflito com Pydantic
        object.__setattr__(self, "chat_history_backend", chat_history)
        # Carrega mensagens existentes do MySQL
        self.chat_memory.messages = self.chat_history_backend.get_messages()

    def save_context(self, inputs: dict, outputs: dict):
        """Salva o contexto da conversa no MySQL"""
        # Chama o método pai para processar
        super().save_context(inputs, outputs)
        
        # Salva as novas mensagens no MySQL
        if self.chat_memory.messages:
            # Pega as duas últimas mensagens (input e output)
            recent_messages = self.chat_memory.messages[-2:]
            for message in recent_messages:
                self.chat_history_backend.add_message(message)

    def clear(self):
        """Limpa a memória e o histórico do MySQL"""
        super().clear()
        self.chat_history_backend.clear()

class NutritionistAgent:
    def __init__(self, session_id, mysql_config=None):
        self.llm = ChatGoogleGenerativeAI(model='gemini-1.5-flash', temperature=0.7)

        system_prompt = ''' 
        Você é uma nutricionista virtual especializada em nutrição esportiva.
        - Sugestões de refeições detalhadas e tabela nutricional.
        - Treinos adaptados conforme objetivo.
        - Comunicação clara, objetiva e motivadora.
        '''

        # Configuração padrão do MySQL (pode ser sobrescrita)
        if mysql_config is None:
            mysql_config = {
                'host': os.getenv('MYSQL_HOST', 'localhost'),
                'port': int(os.getenv('MYSQL_PORT', 3306)),
                'user': os.getenv('MYSQL_USER', 'root'),
                'password': os.getenv('MYSQL_PASSWORD', ''),
                'database': os.getenv('MYSQL_DATABASE', 'nutri_chat_teste'),
                'charset': 'utf8mb4',
                'autocommit': True,
                'connection_timeout': 60
            }

        # Inicializa a conexão MySQL customizada
        self.chat_history = MySQLChatHistory(session_id, mysql_config)
        
        # Usa nossa memória customizada
        self.memory = CustomConversationBufferMemory(
            chat_history=self.chat_history,
            memory_key='chat_history',
            return_messages=True
        )

        self.agent = initialize_agent(
            llm=self.llm,
            tools=[],
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=False,
            memory=self.memory,
            agent_kwargs={'system_message': system_prompt}
        )

        self.analyser = FoodAnalyser()

    def run_text(self, input_text: str) -> str:
        """Chat de texto com persistência no MySQL"""
        try:
            response = self.agent.invoke({"input": input_text})
            return response.get("output") if isinstance(response, dict) else response
        except Exception:
            print(f'Erro chat: {traceback.format_exc()}')
            return 'Desculpe, não foi possível processar sua solicitação.'

    def run_image(self, image_path: str) -> str:
        """Análise de imagens"""
        try:
            result = self.analyser._run(image_path)
            
            # Opcional: salvar análise de imagem no histórico
            self.memory.save_context(
                {"input": f"Análise de imagem: {image_path}"}, 
                {"output": result}
            )
            
            return result
        except Exception:
            print(f'Erro imagem: {traceback.format_exc()}')
            return 'Não foi possível analisar a imagem.'

    def get_conversation_history(self) -> List[dict]:
        """Retorna o histórico da conversa em formato dict"""
        messages = self.chat_history.get_messages()
        history = []
        
        for msg in messages:
            history.append({
                'type': 'human' if isinstance(msg, HumanMessage) else 'ai',
                'content': msg.content,
                'timestamp': datetime.now().isoformat()  # Você pode ajustar isso
            })
        
        return history

    def clear_history(self):
        """Limpa o histórico da conversa"""
        self.memory.clear()