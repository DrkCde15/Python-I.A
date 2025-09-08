# food_analyser.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import BaseTool
from langchain_core.messages import SystemMessage, HumanMessage
from PIL import Image
import base64
from io import BytesIO
from pydantic import PrivateAttr

class FoodAnalyser(BaseTool):
    name: str = "food_analyser"
    description: str = "Nutricionista virtual especializada em nutrição esportiva, analisa imagens de refeições."

    _llm: ChatGoogleGenerativeAI = PrivateAttr()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._llm = ChatGoogleGenerativeAI(model='gemini-1.5-flash', temperature=0.7)

    def _run(self, image_path: str) -> str:
        """Single-input: só recebe o caminho da imagem"""
        return self._analyze_image(image_path)

    async def _arun(self, image_path: str) -> str:
        """Async single-input"""
        return self._analyze_image(image_path)

    def _analyze_image(self, image_path: str) -> str:
        image = Image.open(image_path)
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

        instructions = SystemMessage(content='''
        Analise a imagem enviada e descreva detalhadamente os alimentos visíveis.
        Gere tabela nutricional estimada (calorias, carboidratos, proteínas, gorduras).
        ''')
        
        message = [HumanMessage(
            content=[
                {'type': 'text', 'text': instructions.content},
                {'type': 'image_url', 'image_url': {'url': f"data:image/jpeg;base64,{img_b64}"}}
            ]
        )]

        response = self._llm.invoke(message)
        return response.content
