from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import BaseTool
from langchain_core.messages import SystemMessage, HumanMessage
from PIL import Image
import base64
from io import BytesIO
from pydantic import PrivateAttr

class FoodAnalyser(BaseTool):
    name: str = "food_analyser"
    description: str = '''
    Você é uma nutricionista virtual especializada em nutrição esportiva, com foco em análise visual de refeições através de imagens enviadas pelo usuário.
        
        Ao receber uma imagem (via caminho, upload ou arraste), faça o seguinte:

        1. Identifique e descreva detalhadamente todos os alimentos visíveis no prato.
        2. Gere uma tabela nutricional estimada da refeição com os principais macros: calorias, carboidratos, proteínas e gorduras.
        3. Forneça uma descrição nutricional clara, explicando os impactos e benefícios daquela combinação alimentar.
        4. Se possível, dê recomendações rápidas para melhorar o prato em função do objetivo do usuário (emagrecimento, ganho de massa, energia, etc.).
        5. Sempre responda de forma objetiva, técnica, porém acessível e sem enrolação.

        Regras:
        - Use a ferramenta de análise sempre que receber um arquivo de imagem ou caminho de imagem.
        - Caso não tenha imagem, não tente gerar análise visual.
        - Se receber perguntas fora do escopo (nutrição, treino, dietas, análise de comida), responda com mensagem clara de erro.

        Você é uma especialista focada em resultados práticos e eficazes. Vá direto ao ponto, sem rodeios.
    '''

    _llm: ChatGoogleGenerativeAI = PrivateAttr()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._llm = ChatGoogleGenerativeAI(model='gemini-1.5-flash', temperature=0.7)

    def _run(self, image_path: str) -> str:
        image = Image.open(image_path)
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

        instructions = SystemMessage(content='''
        Você deve analisar a imagem enviada e verificar se ela contém um prato de comida.
        Caso seja um prato de comida, descreva os itens visíveis no prato e crie uma descrição nutricional detalhada e estimada
        incluindo calorias, carboidratos, proteínas e gorduras. Forneça uma descrição nutricional completa da refeição.
        ''')

        message = [HumanMessage(
            content=[
                {'type': 'text', 'text': instructions.content},
                {'type': 'image_url', 'image_url': {'url': f"data:image/jpeg;base64,{img_b64}"}}
            ]
        )]

        response = self._llm.invoke(message)
        return response.content

    async def _arun(self, image_path: str) -> str:
        raise NotImplementedError("Execução assíncrona não suportada")