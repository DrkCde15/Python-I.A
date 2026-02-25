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
        # CORREÇÃO CRÍTICA: Aumentar max_output_tokens e desabilitar thinking
        self._llm = ChatGoogleGenerativeAI(
            model='gemini-2.0-flash',  # Versão mais estável
            temperature=0.7,
            max_output_tokens=4096,  # Aumentado significativamente
            max_tokens=None,  # Remove limite de tokens totais
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
        return '''🍽️ **Análise Nutricional da Refeição**

Por favor, responda **somente** neste formato (usando Markdown):

| 🧾 Nutriente | 💪 Quantidade | ⚖️ % VD* |
|--------------|---------------|----------|
| Calorias | X kcal | X% |
| Carboidratos | X g | X% |
| Proteínas | X g | X% |
| Gorduras Totais | X g | X% |
| Gorduras Saturadas | X g | X% |
| Fibras | X g | X% |
| Sódio | X mg | X% |

*VD = Valores Diários (base: dieta de 2.000 kcal)*

---

### 🌟 Avaliação geral
> **Classificação:** [Excelente / Boa / Regular / Precisa melhorar]

### ✅ Pontos Positivos
- [ponto 1]
- [ponto 2]

### 💡 Sugestões de Melhoria
- [sugestão 1]
- [sugestão 2]

🧠 *Dica: Responda diretamente com a tabela e as listas acima, sem explicações adicionais.*'''

    def _extract_content_from_response(self, response) -> str:
        """Extrai o conteúdo de texto do objeto AIMessage de forma robusta"""
        try:
            # Método 1: Atributo content direto
            if hasattr(response, 'content'):
                if isinstance(response.content, str) and response.content.strip():
                    return response.content.strip()
                elif isinstance(response.content, list):
                    text_parts = []
                    for item in response.content:
                        if isinstance(item, dict) and 'text' in item:
                            text_parts.append(item['text'])
                        elif isinstance(item, str):
                            text_parts.append(item)
                    if text_parts:
                        return ' '.join(text_parts).strip()
            
            # Método 2: Tentar extrair de diferentes atributos
            for attr in ['text', 'output', 'output_text', 'result']:
                if hasattr(response, attr):
                    content = getattr(response, attr)
                    if isinstance(content, str) and content.strip():
                        return content.strip()
            
            # Método 3: Se for um dict
            if isinstance(response, dict):
                for key in ['content', 'text', 'output']:
                    if key in response and response[key]:
                        return str(response[key]).strip()
            
            # Se chegou aqui, o content está vazio
            return ""
            
        except Exception as e:
            print(f"Erro ao extrair conteúdo: {e}")
            return ""

    def _analyze_image(self, image_path: str) -> str:
        """Análise completa retornando apenas a tabela + dicas"""
        try:
            img_b64 = self._process_image(image_path)

            system_message = SystemMessage(content=self._create_analysis_prompt())
            human_message = HumanMessage(content=[
                {
                    'type': 'text', 
                    'text': 'Você é uma nutricionista. Analise esta refeição e forneça a tabela nutricional DIRETAMENTE, sem raciocínio interno extenso:'
                },
                {
                    'type': 'image_url', 
                    'image_url': {
                        'url': f"data:image/jpeg;base64,{img_b64}",
                        'detail': 'high'
                    }
                }
            ])

            # Invoca o modelo com configuração otimizada
            response = self._llm.invoke(
                [system_message, human_message],
                config={
                    'max_output_tokens': 4096,
                    'temperature': 0.7,
                }
            )
            
            # Debug: mostra o que foi recebido
            print(f"\n🔍 DEBUG - Resposta recebida:")
            print(f"Tipo: {type(response)}")
            print(f"Atributos: {dir(response)}")
            if hasattr(response, 'response_metadata'):
                print(f"Metadata: {response.response_metadata}")
            if hasattr(response, 'usage_metadata'):
                print(f"Usage: {response.usage_metadata}")
            
            # Extrai o conteúdo
            tabela_texto = self._extract_content_from_response(response)
            
            # Verifica se o content está vazio (problema MAX_TOKENS em reasoning)
            if not tabela_texto or len(tabela_texto) < 50:
                # Tenta uma segunda chamada com prompt mais direto
                print("Conteúdo vazio, tentando com prompt simplificado...")
                
                simple_message = HumanMessage(content=[
                    {
                        'type': 'text',
                        'text': 'Liste os alimentos visíveis e estime calorias, proteínas, carboidratos e gorduras em formato de tabela markdown.'
                    },
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': f"data:image/jpeg;base64,{img_b64}",
                            'detail': 'low'  # Reduz processamento
                        }
                    }
                ])
                
                response = self._llm.invoke([simple_message])
                tabela_texto = self._extract_content_from_response(response)
                
                if not tabela_texto or len(tabela_texto) < 50:
                    return f"""**Erro: Resposta vazia do modelo**

O modelo está consumindo todos os tokens em raciocínio interno e não gerando saída.

**Detalhes técnicos**:
- finish_reason: {response.response_metadata.get('finish_reason', 'unknown')}
- output_tokens: {response.usage_metadata.get('output_tokens', 0) if hasattr(response, 'usage_metadata') else 'N/A'}
- reasoning_tokens: {response.usage_metadata.get('output_token_details', {}).get('reasoning', 0) if hasattr(response, 'usage_metadata') else 'N/A'}

**Soluções**:

2. Aumente `max_output_tokens` para 8192
3. Simplifique a imagem ou reduza o prompt

**Resposta bruta**: {str(response)[:300]}"""
            
            # Formata o resultado final
            result_text =f"""
🍱 **Análise Nutricional da Refeição**
📸 _Imagem analisada:_ **{os.path.basename(image_path)}**

{tabela_texto}

---

💬 **Dica da Nutricionista:**  
Para análises mais precisas, inclua informações como **peso, altura, objetivos** e **nível de atividade física**.

🧾 *Este é um relatório estimado, não substitui avaliação profissional.*
"""

            return result_text

        except Exception as e:
            error_details = traceback.format_exc()
            print(f"Erro completo na análise:\n{error_details}")
            return f"""Não foi possível analisar a imagem.

**Erro técnico**: {str(e)}

**Traceback**:
```
{error_details[:500]}
```

**Sugestões**:
1. Verifique a API key do Google
2. Teste com uma imagem menor"""

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
        """Analisa múltiplas imagens e retorna lista de resultados"""
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
        """Cria relatório final com todas as análises"""
        report = f"""# RELATÓRIO DE ANÁLISES NUTRICIONAIS

**Total de imagens**: {len(results)}
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
        
        report += "\n**Observação**: Estimativas baseadas em análise visual. Consulte um nutricionista para orientação personalizada."
        return report