from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import SQLChatMessageHistory
from dotenv import load_dotenv
from food_analyser import FoodAnalyser
import os
import traceback
import warnings

# Desativa warnings de depreciação
warnings.filterwarnings("ignore", category=DeprecationWarning)

# ======== API KEY ========
# Carrega a chave da API do Google
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise EnvironmentError("GOOGLE_API_KEY não definida no .env")
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# ======== INICIALIZAÇÃO =========
# Inicializa o agente de nutrição com a ferramenta de análise de alimentos
class NutritionistAgent:
    def __init__(self, session_id, db_path='sqlite:///chat_history.db') -> None: #<<< caminho do banco de dados
        self.llm = ChatGoogleGenerativeAI(
            model='gemini-1.5-flash',
            temperature=0.1,
        )
        
        # <<< PROMPT PERSONALIZADO PARA O AGENTE
        system_prompt = ''' 
            Você é uma nutricionista virtual altamente especializada em nutrição esportiva e dietas personalizadas.
            Forneça planos alimentares, sugestões de refeições, dicas para emagrecimento, ganho de massa magra, energia e performance.
            Mesmo com poucas informações do usuário, fornecer uma tabela nutricional detalhada e estimada incluindo calorias, carboidratos, proteínas e gorduras.
            Forneça uma descrição nutricional completa da refeição.
            E treinos que ele pode fazer ou na academia ou em casa.
            Sempre considere os objetivos, alergias, preferências e rotina do usuário. Seja clara, objetiva, motivadora e sempre vá direto ao ponto sem enrolação.
            E voce responde-ra somente perguntas sobre nutrição, treinos, e dietas personalizadas.
            Se a pergunta nao for sobre nutricao,treinos e dietas mande uma mensagem de erro.
        '''

        # <<< HISTÓRICO DE CHAT
        self.chat_history = SQLChatMessageHistory(
            session_id=session_id,
            connection_string=db_path
        )
        
        # <<< MEMÓRIA DE CONVERSA PARA O AGENTE
        self.memory = ConversationBufferMemory(
            memory_key='chat_history',
            chat_memory=self.chat_history,
            return_messages=True
        )
        
        # <<< INICIALIZAÇÃO DO AGENTE
        self.agent = initialize_agent(
            llm=self.llm,
            tools=[FoodAnalyser()],
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=False,  # <<< remove logs internos
            memory=self.memory,
            agent_kwargs={
                'system_message': system_prompt
            }
        )
    
    # <<< FUNÇÃO DE PROCESSAMENTO DE MENSAGENS
    def run(self, input_text):
        try:
            response = self.agent.invoke({"input": input_text})
            # Extrai só o conteúdo de output
            final_output = response.get("output") if isinstance(response, dict) else response
            return final_output
        except Exception:
            print(f'Erro: {traceback.format_exc()}')
            return 'Desculpe, não foi possível processar sua solicitação.'

# ======== EXECUÇÃO ========
if __name__ == '__main__':
    agent = NutritionistAgent(session_id="usuario_01")

    while True:
        entrada = input("Você: ").strip()

        if not entrada:
            print("Entrada vazia ignorada.")
            continue

        if entrada.lower() in ['sair', 'exit', 'quit']:
            break

        resposta = agent.run(entrada)
        print(f"\nNutriAI: {resposta}\n")

    print("\nAdeus Senhor, até mais tarde.")

