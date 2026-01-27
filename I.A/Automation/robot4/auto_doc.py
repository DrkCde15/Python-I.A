import os
import sys
from dotenv import load_dotenv
from google import genai

load_dotenv()

# Configuração do Cliente com a nova lib google-genai
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("Erro: GEMINI_API_KEY não encontrada no arquivo .env")
    sys.exit(1)
# Configuração do Cliente
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
MODEL_ID = "gemini-2.5-flash"

def mapear_arquitetura(caminho_raiz):
    estrutura = []
    resumo_codigo = []
    
    print(f"[1/2] Mapeando estrutura de pastas...")
    for raiz, dirs, arquivos in os.walk(caminho_raiz):
        # Ignora pastas pesadas ou irrelevantes
        dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', '__pycache__', 'dist', 'build']]
        
        nivel = raiz.replace(caminho_raiz, '').count(os.sep)
        indentacao = '  ' * nivel
        estrutura.append(f"{indentacao}{os.path.basename(raiz)}/")
        
        for arquivo in arquivos:
            if arquivo.endswith(('.py', '.js', '.ts', '.json', '.java', '.go', '.rb', '.php', '.html', '.css', 
                                 '.cpp', '.c', '.rs', '.swift', '.kt', '.jsx', '.tsx', '.yml', '.yaml', '.md', '.txt')):
                estrutura.append(f"{indentacao} - {arquivo}")
                
                # Lê apenas o início do arquivo para capturar a intenção (imports e docs)
                caminho_completo = os.path.join(raiz, arquivo)
                try:
                    with open(caminho_completo, 'r', encoding='utf-8') as f:
                        inicio_codigo = f.read(500) 
                        resumo_codigo.append(f"Arquivo: {arquivo}\nContexto: {inicio_codigo}...")
                except:
                    continue
                    
    return "\n".join(estrutura), "\n\n".join(resumo_codigo)

def gerar_docs():
    if len(sys.argv) < 2:
        print("Uso: python documentador.py 'C:/Caminho/Do/Projeto'")
        return

    caminho_projeto = sys.argv[1]
    tree, snippets = mapear_arquitetura(caminho_projeto)

    prompt = f"""
    Aja como um Arquiteto de Software. Analise a estrutura de pastas e os trechos de código abaixo do projeto.
    
    ESTRUTURA DE PASTAS:
    {tree}
    
    TRECHOS DE CÓDIGO (Contexto):
    {snippets}
    
    Crie um README.md que contenha:
    1. Nome do Projeto e Visão Geral.
    2. Árvore de Diretórios formatada.
    3. Explicação do papel de cada pasta principal (ex: o que faz a 'src/controllers').
    4. Fluxo de dados (como os componentes se comunicam).
    5. Tecnologias detectadas.
    
    Escreva em Português, de forma clara e profissional.
    """

    print("[2/2] IA analisando arquitetura...")
    response = client.models.generate_content(model=MODEL_ID, contents=prompt)
    
    saida = os.path.join(caminho_projeto, "ARCHITECTURE.md")
    with open(saida, "w", encoding="utf-8") as f:
        f.write(response.text)
    
    print(f"Arquitetura documentada com sucesso em: {saida}")

if __name__ == "__main__":
    gerar_docs()