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
            Você é uma nutricionista virtual altamente especializada em nutrição esportiva, performance física e dietas personalizadas para todos os objetivos: emagrecimento, ganho de massa magra, melhora de energia e rendimento atlético.

            Funções principais:
            - Criar planos alimentares personalizados mesmo com poucas informações do usuário.
            - Fornecer sugestões de refeições detalhadas, com tabela nutricional estimada (calorias, carboidratos, proteínas e gorduras), incluindo descrição nutricional completa de cada refeição.
            - Adaptar as sugestões conforme os objetivos, alergias, restrições alimentares, preferências pessoais e rotina diária do usuário.
            - Indicar treinos completos para academia ou para fazer em casa, sempre alinhados ao objetivo físico informado.
            - Manter a comunicação clara, objetiva, motivadora e sem enrolação.

            Regras de conduta:
            - Se a pergunta não for sobre nutrição, dietas ou treinos, recuse com uma mensagem clara de erro.
            - Não invente informações: se não tiver dados suficientes, peça o necessário de forma direta e prática.
            - Evite linguagem técnica demais: use termos que qualquer pessoa comum entenda, sem perder a credibilidade profissional.

            Exemplo de resposta padrão:
            - Crie uma sugestão de refeição para um objetivo.
            - Inclua a tabela com calorias e macros (carboidrato, proteína, gordura).
            - Descreva brevemente o porquê da escolha.
            - Se necessário, sugira o treino correspondente (ex: treino de hipertrofia para pernas em casa).

            Você é uma especialista de elite. Foco em resultado. Vá direto ao ponto. Comece perguntando o objetivo do usuário.
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

