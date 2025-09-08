# nutri.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import SQLChatMessageHistory
from dotenv import load_dotenv
from food_analyser import FoodAnalyser
import os, warnings, traceback

warnings.filterwarnings("ignore", category=DeprecationWarning)

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise EnvironmentError("GOOGLE_API_KEY não definida no .env")
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

class NutritionistAgent:
    def __init__(self, session_id, db_path='sqlite:///chat_history.db'):
        self.llm = ChatGoogleGenerativeAI(model='gemini-1.5-flash', temperature=0.7)

        system_prompt = ''' 
        Você é uma nutricionista virtual especializada em nutrição esportiva.
        - Sugestões de refeições detalhadas e tabela nutricional.
        - Treinos adaptados conforme objetivo.
        - Comunicação clara, objetiva e motivadora.
        '''

        self.chat_history = SQLChatMessageHistory(session_id=session_id, connection_string=db_path)
        self.memory = ConversationBufferMemory(memory_key='chat_history', chat_memory=self.chat_history, return_messages=True)

        self.agent = initialize_agent(
            llm=self.llm,
            tools=[],  # Nenhuma ferramenta de multi-input aqui
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=False,
            memory=self.memory,
            agent_kwargs={'system_message': system_prompt}
        )

        self.analyser = FoodAnalyser()  # Ferramenta para imagens

    # Chat de texto
    def run_text(self, input_text: str) -> str:
        try:
            response = self.agent.invoke({"input": input_text})
            return response.get("output") if isinstance(response, dict) else response
        except Exception:
            print(f'Erro chat: {traceback.format_exc()}')
            return 'Desculpe, não foi possível processar sua solicitação.'

    # Análise de imagens
    def run_image(self, image_path: str) -> str:
        try:
            return self.analyser._run(image_path)
        except Exception:
            print(f'Erro imagem: {traceback.format_exc()}')
            return 'Não foi possível analisar a imagem.'
