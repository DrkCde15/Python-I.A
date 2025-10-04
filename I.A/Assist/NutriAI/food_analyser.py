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
from datetime import datetime

class FoodAnalyser(BaseTool):
    name: str = "food_analyser"
    description: str = """Analisa imagens de refeições fornecendo informações nutricionais detalhadas e 
    sugestões de uma nutricionista especializada em nutrição esportiva."""

    _llm: ChatGoogleGenerativeAI = PrivateAttr()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._llm = ChatGoogleGenerativeAI(
            model='gemini-2.5-flash',
            temperature=0.7,
            max_tokens=2048
        )

    # ----------------- Implementação obrigatória BaseTool -----------------
    def _run(self, image_path: str) -> str:
        """Análise síncrona do BaseTool"""
        return self._analyze_image(image_path)

    async def _arun(self, image_path: str) -> str:
        """Análise assíncrona do BaseTool"""
        return self._analyze_image(image_path)

    # ----------------- Funções auxiliares -----------------
    def _get_timestamp(self) -> str:
        return datetime.now().isoformat()

    def _validate_image_path(self, image_path: str) -> bool:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {image_path}")
        valid_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'}
        _, ext = os.path.splitext(image_path.lower())
        if ext not in valid_extensions:
            raise ValueError(f"Formato de imagem não suportado: {ext}")
        return True

    def _process_image(self, image_path: str) -> str:
        self._validate_image_path(image_path)
        with Image.open(image_path) as image:
            if image.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')

            max_size = (1024, 1024)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)

            buffered = BytesIO()
            image.save(buffered, format="JPEG", quality=85, optimize=True)
            return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def _create_analysis_prompt(self) -> str:
        return '''
Você é uma nutricionista especializada em nutrição esportiva. Analise a imagem da refeição e forneça
uma tabela nutricional em Markdown seguindo este formato:

| Nutriente | Quantidade | % VD* |
|-----------|------------|-------|
| Calorias | ... | ... |
| Carboidratos | ... | ... |
| Proteínas | ... | ... |
| Gorduras Totais | ... | ... |
| Gorduras Saturadas | ... | ... |
| Fibras | ... | ... |
| Sódio | ... | ... |

*VD = Valores Diários de referência baseados em uma dieta de 2.000 kcal

Após a tabela, inclua:
1. **Avaliação Geral**: Qualidade nutricional da refeição (Excelente/Boa/Regular/Precisa melhorar)
2. **Pontos Positivos**: O que está bom na refeição
3. **Sugestões de Melhoria**: 2-3 dicas práticas e objetivas

Seja clara, objetiva e use linguagem acessível.
'''

    def _extract_content_from_response(self, response) -> str:
        """Extrai o conteúdo de texto do objeto AIMessage de forma robusta"""
        try:
            # Método 1: Atributo content (mais comum)
            if hasattr(response, 'content') and response.content:
                if isinstance(response.content, str):
                    return response.content
                elif isinstance(response.content, list):
                    # Às vezes o content é uma lista de dicts
                    text_parts = []
                    for item in response.content:
                        if isinstance(item, dict) and 'text' in item:
                            text_parts.append(item['text'])
                        elif isinstance(item, str):
                            text_parts.append(item)
                    if text_parts:
                        return ' '.join(text_parts)
            
            # Método 2: Conversão direta para string
            if hasattr(response, '__str__'):
                content_str = str(response)
                # Remove metadados se presentes
                if 'content=' in content_str:
                    # Extrai apenas o conteúdo útil
                    start = content_str.find("content='") + 9
                    end = content_str.find("', additional_kwargs")
                    if start > 8 and end > start:
                        return content_str[start:end]
            
            # Método 3: Tentar acessar diretamente como dict
            if isinstance(response, dict) and 'content' in response:
                return str(response['content'])
            
            # Se tudo falhar, retorna representação em string
            return str(response)
            
        except Exception as e:
            print(f"Erro ao extrair conteúdo: {e}")
            return f"Erro ao processar resposta: {str(e)}"

    def _analyze_image(self, image_path: str) -> str:
        """Análise completa retornando apenas a tabela + dicas"""
        try:
            img_b64 = self._process_image(image_path)

            system_message = SystemMessage(content=self._create_analysis_prompt())
            human_message = HumanMessage(content=[
                {'type': 'text', 'text': 'Analise esta imagem de refeição e retorne a tabela nutricional completa com avaliação e dicas:'},
                {'type': 'image_url', 'image_url': {'url': f"data:image/jpeg;base64,{img_b64}", 'detail': 'high'}}
            ])

            # Invoca o modelo
            response = self._llm.invoke([system_message, human_message])
            
            # Extrai o conteúdo de forma robusta
            tabela_texto = self._extract_content_from_response(response)
            
            # Verifica se conseguiu extrair conteúdo válido
            if not tabela_texto or len(tabela_texto) < 50:
                return f"Erro: Resposta vazia ou inválida do modelo. Resposta recebida: {str(response)[:200]}"
            
            # Formata o resultado final
            result_text = f"""ANÁLISE NUTRICIONAL DA REFEIÇÃO
_Imagem: {os.path.basename(image_path)}_

{tabela_texto}

---
💡 **Dica da Nutricionista**: Para análises mais precisas, inclua informações sobre suas características (peso, altura, objetivos) e nível de atividade física!"""

            return result_text

        except Exception as e:
            error_details = traceback.format_exc()
            print(f"Erro completo na análise:\n{error_details}")
            return f"""Não foi possível analisar a imagem.

**Erro técnico**: {str(e)}

**Possíveis causas**:
- Formato de imagem não suportado
- Arquivo corrompido ou muito grande

**Sugestões**:
1. Verifique se a imagem está em formato válido (JPG, PNG, WEBP)
2. Tente com uma imagem menor (< 5MB)"""

    # ----------------- Interface pública -----------------
    def analyze_food_image(self, image_path: str) -> str:
        return self._analyze_image(image_path)

    def get_supported_formats(self) -> list:
        return ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif']


# ----------------- Batch processing -----------------
class BatchFoodAnalyser:
    """Classe para analisar múltiplas imagens"""

    def __init__(self):
        self.analyser = FoodAnalyser()

    def analyze_multiple_images(self, image_paths: list) -> list:
        """Analisa múltiplas imagens e retorna lista de resultados (tabela + dicas)"""
        results = []
        for i, path in enumerate(image_paths, 1):
            print(f"Analisando imagem {i}/{len(image_paths)}: {os.path.basename(path)}")
            result = self.analyser.analyze_food_image(path)
            results.append({
                'path': path,
                'filename': os.path.basename(path),
                'analysis': result
            })
        return results

    def create_summary_report(self, results: list) -> str:
        """Cria relatório final com todas as tabelas em sequência"""
        report = f"""# 📊 RELATÓRIO DE ANÁLISES NUTRICIONAIS

**Total de imagens analisadas**: {len(results)}
**Data**: {datetime.now().strftime('%d/%m/%Y %H:%M')}

---

"""
        for i, result in enumerate(results, 1):
            analysis = result['analysis'] if isinstance(result, dict) else result
            filename = result.get('filename', f'Imagem {i}') if isinstance(result, dict) else f'Imagem {i}'
            
            report += f"""## {i}. {filename}

{analysis}

---

"""
        
        report += "\n\n**Observação Final**: Este relatório é baseado em estimativas visuais e não substitui a consulta com um nutricionista profissional."
        
        return report