# food_analyser.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import BaseTool
from langchain_core.messages import SystemMessage, HumanMessage
from PIL import Image
import base64
import os
from io import BytesIO
from pydantic import PrivateAttr
import traceback

class FoodAnalyser(BaseTool):
    name: str = "food_analyser"
    description: str = """Analisa imagens de refeições fornecendo informações nutricionais detalhadas e 
    sugestões de uma nutricionista especializada em nutrição esportiva."""

    _llm: ChatGoogleGenerativeAI = PrivateAttr()
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._llm = ChatGoogleGenerativeAI(
            model='gemini-1.5-flash', 
            temperature=0.7,
            max_tokens=2048
        )

    def _run(self, image_path: str) -> str:
        """Análise síncrona da imagem"""
        try:
            return self._analyze_image(image_path)
        except Exception as e:
            print(f"Erro na análise da imagem: {traceback.format_exc()}")
            return f"Não foi possível analisar a imagem. Erro: {str(e)}"

    async def _arun(self, image_path: str) -> str:
        """Análise assíncrona da imagem"""
        try:
            return self._analyze_image(image_path)
        except Exception as e:
            print(f"Erro na análise assíncrona da imagem: {traceback.format_exc()}")
            return f"Não foi possível analisar a imagem. Erro: {str(e)}"

    def _validate_image_path(self, image_path: str) -> bool:
        """Valida se o arquivo de imagem existe e é válido"""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {image_path}")
        
        valid_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'}
        _, ext = os.path.splitext(image_path.lower())
        
        if ext not in valid_extensions:
            raise ValueError(f"Formato de imagem não suportado: {ext}")
        
        return True

    def _process_image(self, image_path: str) -> str:
        """Processa e converte a imagem para base64"""
        self._validate_image_path(image_path)
        
        try:
            # Abre e processa a imagem
            with Image.open(image_path) as image:
                # Converte para RGB se necessário (remove transparência)
                if image.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                    image = background
                elif image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Redimensiona se muito grande (otimização)
                max_size = (1024, 1024)
                if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                    image.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Converte para base64
                buffered = BytesIO()
                image.save(buffered, format="JPEG", quality=85, optimize=True)
                img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
                
                return img_b64
                
        except Exception as e:
            raise Exception(f"Erro ao processar imagem: {str(e)}")

    def _create_analysis_prompt(self) -> str:
        """Cria o prompt detalhado para análise nutricional"""
        return '''
        Você é uma nutricionista especializada em nutrição esportiva. Analise a imagem da refeição enviada e forneça:

        ## IDENTIFICAÇÃO DOS ALIMENTOS
        - Liste todos os alimentos visíveis na imagem
        - Estime as quantidades/porções de cada item
        - Identifique o método de preparo (grelhado, frito, cozido, etc.)

        ## ANÁLISE NUTRICIONAL
        Calcule e apresente em formato de tabela:
        
        | Nutriente | Quantidade | % VD* |
        |-----------|------------|-------|
        | Calorias | X kcal | X% |
        | Carboidratos | X g | X% |
        | Proteínas | X g | X% |
        | Gorduras Totais | X g | X% |
        | Gorduras Saturadas | X g | X% |
        | Fibras | X g | X% |
        | Sódio | X mg | X% |
        
        *Valores Diários baseados em dieta de 2000 kcal

        ## AVALIAÇÃO NUTRICIONAL
        - Qualidade nutricional da refeição (1-10)
        - Adequação para objetivos esportivos
        - Pontos positivos e negativos

        ## SUGESTÕES DE MELHORIA
        - Como otimizar esta refeição
        - Substituições mais saudáveis
        - Ajustes para diferentes objetivos (ganho de massa, perda de peso, performance)

        ## TIMING DE CONSUMO
        - Melhor momento para consumir (pré/pós treino, etc.)
        - Combinações ideais com outros alimentos

        Seja precisa, educativa e motivadora em suas orientações!
        '''

    def _analyze_image(self, image_path: str) -> str:
        """Realiza a análise completa da imagem"""
        try:
            # Processa a imagem
            img_b64 = self._process_image(image_path)
            
            # Cria as mensagens para o LLM
            system_message = SystemMessage(content=self._create_analysis_prompt())
            
            human_message = HumanMessage(
                content=[
                    {
                        'type': 'text', 
                        'text': 'Analise esta imagem de refeição seguindo todas as diretrizes fornecidas:'
                    },
                    {
                        'type': 'image_url', 
                        'image_url': {
                            'url': f"data:image/jpeg;base64,{img_b64}",
                            'detail': 'high'
                        }
                    }
                ]
            )

            # Invoca o modelo
            messages = [system_message, human_message]
            response = self._llm.invoke(messages)
            
            # Adiciona metadados da análise
            analysis_result = f"""
🔍 **ANÁLISE NUTRICIONAL DA REFEIÇÃO**
_Imagem: {os.path.basename(image_path)}_

{response.content}

---
💡 **Dica da Nutricionista**: Para análises mais precisas, inclua informações sobre suas características (peso, altura, objetivos) e atividade física!
            """.strip()
            
            return analysis_result
            
        except Exception as e:
            print(f"Erro na análise: {traceback.format_exc()}")
            return self._get_error_message(str(e))

    def _get_error_message(self, error: str) -> str:
        """Retorna uma mensagem de erro amigável"""
        if "FileNotFoundError" in error:
            return "**Imagem não encontrada**\n\nVerifique se o caminho da imagem está correto e tente novamente."
        elif "formato" in error.lower() or "extension" in error.lower():
            return "**Formato não suportado**\n\nUse imagens nos formatos: JPG, PNG, WEBP, BMP ou GIF."
        elif "size" in error.lower() or "memory" in error.lower():
            return "**Imagem muito grande**\n\nTente usar uma imagem menor (máximo 10MB)."
        else:
            return f"**Erro na análise**\n\nNão foi possível processar a imagem. Tente novamente com outra imagem.\n\n_Detalhes técnicos: {error}_"

    # Métodos adicionais para integração com o sistema
    def analyze_food_image(self, image_path: str) -> dict:
        """Método que retorna análise em formato estruturado"""
        try:
            analysis = self._analyze_image(image_path)
            
            return {
                'success': True,
                'analysis': analysis,
                'image_path': image_path,
                'timestamp': self._get_timestamp()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'image_path': image_path,
                'timestamp': self._get_timestamp()
            }

    def _get_timestamp(self) -> str:
        """Retorna timestamp atual"""
        from datetime import datetime
        return datetime.now().isoformat()

    def get_supported_formats(self) -> list:
        """Retorna lista de formatos suportados"""
        return ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif']

# Classe utilitária para batch processing
class BatchFoodAnalyser:
    """Classe para analisar múltiplas imagens"""
    
    def __init__(self):
        self.analyser = FoodAnalyser()
    
    def analyze_multiple_images(self, image_paths: list) -> list:
        """Analisa múltiplas imagens e retorna resultados"""
        results = []
        
        for i, path in enumerate(image_paths, 1):
            print(f"Analisando imagem {i}/{len(image_paths)}: {os.path.basename(path)}")
            
            result = self.analyser.analyze_food_image(path)
            results.append(result)
        
        return results
    
    def create_summary_report(self, results: list) -> str:
        """Cria relatório resumido das análises"""
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        report = f"""
# RELATÓRIO DE ANÁLISES NUTRICIONAIS

## Resumo
- **Total de imagens**: {len(results)}
- **Análises bem-sucedidas**: {len(successful)}
- **Falhas**: {len(failed)}

## Imagens Analisadas
"""
        
        for i, result in enumerate(successful, 1):
            report += f"\n### {i}. {os.path.basename(result['image_path'])}\n"
            report += f"{result['analysis']}\n\n---\n"
        
        if failed:
            report += "\n## Erros Encontrados\n"
            for result in failed:
                report += f"- **{os.path.basename(result['image_path'])}**: {result['error']}\n"
        
        return report