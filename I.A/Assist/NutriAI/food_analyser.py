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
    Utilize essa ferramenta para analisar imagens de alimentos de pratos de comida que o usuário enviar. 
    Descreva os alimentos presentes e crie uma tabela nutricional da refeição.
    O agente deve usar a ferramenta sempre que um caminho de imagem for enviado, ou caso a imagem tenha sido arrastadas ou anexada no chat.
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