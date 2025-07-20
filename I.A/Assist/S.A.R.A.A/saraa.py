# S.A.R.A.A – Sistema Avançado de Respostas e Asistências Automatizadas

from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_community.document_loaders import WebBaseLoader, YoutubeLoader, PyPDFLoader, TextLoader, CSVLoader, UnstructuredFileLoader, UnstructuredWordDocumentLoader, JSONLoader
import os
from dotenv import load_dotenv
import platform
import subprocess
import traceback

# ======== API KEY ========
load_dotenv()  # Carrega variáveis de ambiente
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise EnvironmentError("GROQ_API_KEY não definida no .env")

os.environ["GROQ_API_KEY"] = GROQ_API_KEY

# ======== INICIALIZAÇÃO =========
try:
    chat = ChatGroq(model='llama3-70b-8192')
    print("SARAA inicializada com sucesso!")
except Exception:
    print("Erro ao inicializar a IA:")
    traceback.print_exc()
    exit()

# ======== FUNÇÕES DE CARREGAMENTO =========
def carrega_sites():
    url = input('Digite a URL do site: ').strip()
    return WebBaseLoader(url).load()

def carrega_pdf():
    caminho = carregar_arquivo('Digite o caminho do PDF (ex: C:/Users/Usuario/Documents/arquivo.pdf): ')
    return PyPDFLoader(caminho).load()

def carrega_video():
    link = input('Digite o link do vídeo do YouTube: ').strip()
    return YoutubeLoader.from_youtube_url(link, language=['pt']).load()

def carregar_arquivo(mensagem_prompt="Digite o caminho do arquivo: "):
    while True:
        caminho = input(mensagem_prompt).strip()
        caminho = caminho.replace("\\", "/")
        if not os.path.isfile(caminho):
            print("Arquivo não encontrado! Tente novamente.")
        else:
            return caminho

def carrega_arquivo_generico(caminho):
    extensao = os.path.splitext(caminho)[1].lower()

    try:
        if extensao == ".pdf":
            return PyPDFLoader(caminho).load()
        elif extensao == ".txt":
            return TextLoader(caminho, encoding="utf-8").load()
        elif extensao == ".csv":
            return CSVLoader(caminho).load()
        elif extensao == ".json":
            return JSONLoader(caminho, jq_schema=".").load()
        elif extensao in [".docx", ".doc"]:
            return UnstructuredWordDocumentLoader(caminho).load()
        else:
            # Tenta com Unstructured como fallback
            return UnstructuredFileLoader(caminho).load()
    except Exception as e:
        print(f"Erro ao carregar o arquivo: {e}")
        return []

def abrir_arquivo(caminho):
    if not os.path.isfile(caminho):
        print("Arquivo não encontrado para abrir.")
        return False
    
    sistema = platform.system()
    try:
        if sistema == "Windows":
            os.startfile(caminho)
        elif sistema == "Darwin":  # macOS
            subprocess.run(["open", caminho])
        else:  # Linux e outros
            subprocess.run(["xdg-open", caminho])
        print(f"Abrindo arquivo: {caminho}")
        return True
    except Exception as e:
        print(f"Erro ao tentar abrir o arquivo: {e}")
        return False

# ======== GERAR RESPOSTA COM CONTEXTO =========
def responde_com_contexto(lista_docs, pergunta):
    texto = ''.join(doc.page_content for doc in lista_docs)
    template = ChatPromptTemplate.from_messages([
        ('system', 'Você é um assistente amigável, que responde com base nestas informações: {documento_informado}'),
        ('user', '{input}')
    ])
    chain = template | chat
    return chain.invoke({'documento_informado': texto, 'input': pergunta}).content

# ======== CHATPAD TRADICIONAL =========
def resposta_do_bot(lista_mensagens):
    template = ChatPromptTemplate.from_messages([
        SystemMessage(content='Você é um assistente amigável chamado Asimo')
    ] + lista_mensagens)
    chain = template | chat
    return chain.invoke({}).content

# ======== MENU PRINCIPAL =========
print('Bem-vindo ao ChatBot da S.A.R.A.A! (Digite x para sair a qualquer momento.)\n')

menu_texto = ''' Selecione a opção desejada:
1 - Conversa com a SARAA
2 - Pesquisa na Web
3 - Leitor de Vídeos do YouTube
4 - Leitor de PDFs
5 - Acessar arquivos do sistema
'''

mensagens = []

while True:
    selecao = input(menu_texto).strip()
    if selecao == '1':
        mensagens.append(SystemMessage(content="Você é a SARAA, um assistente profissional que vai diretamente ao ponto, muito inteligente, frio e me chama de Senhor todas as vezes."))
        try:
            while True:
                pergunta = input('Usuário: ')
                if pergunta.strip().lower() in ['x', 'exit']:
                    break
                mensagens.append(HumanMessage(content=pergunta))
                resposta = resposta_do_bot(mensagens)
                mensagens.append(AIMessage(content=resposta))
                print(f'\nAssistente: {resposta}\n')
        except KeyboardInterrupt:
            print("\nInterrupção detectada. Encerrando o chat.")
        except Exception:
            print("Erro inesperado:")
            traceback.print_exc()
        break

    elif selecao == '2':
        documentos = carrega_sites()
        mensagens.append(SystemMessage(content='Você é um assistente amigável e informativo. Use o conteúdo do site carregado para responder.'))
        while True:
            pergunta = input("Usuário (Web): ")
            if pergunta.strip().lower() in ['x', 'exit']:
                break
            resposta = responde_com_contexto(documentos, pergunta)
            print(f'Resposta: {resposta}')
        break

    elif selecao == '3':
        documentos = carrega_video()
        mensagens.append(SystemMessage(content='Você é um assistente amigável e informativo. Use o conteúdo do vídeo carregado para responder.'))
        while True:
            pergunta = input("Usuário (YouTube): ")
            if pergunta.strip().lower() in ['x', 'exit']:
                break
            resposta = responde_com_contexto(documentos, pergunta)
            print(f'Resposta: {resposta}')
        break

    elif selecao == '4':
        documentos = carrega_pdf()
        mensagens.append(SystemMessage(content='Você é um assistente amigável e informativo. Use o conteúdo do PDF carregado para responder.'))
        while True:
            pergunta = input("Usuário (PDF): ")
            if pergunta.strip().lower() in ['x', 'exit']:
                break
            resposta = responde_com_contexto(documentos, pergunta)
            print(f'Resposta: {resposta}')
        break

    elif selecao == '5':
        mensagens.append(SystemMessage(content='Você é um assistente amigável e informativo. Use o conteúdo do arquivo carregado para responder.'))
        caminho_arquivo = carregar_arquivo('Digite o caminho do arquivo: ')
        abrir_arquivo(caminho_arquivo)

    documentos = carrega_arquivo_generico(caminho_arquivo)
    if not documentos:
        print("Erro ao carregar o conteúdo. Verifique se o tipo de arquivo é suportado.")
        break

    while True:
        pergunta = input("Usuário (Arquivo): ")
        if pergunta.strip().lower() in ['x', 'exit']:
            break
        resposta = responde_com_contexto(documentos, pergunta)
        print(f'Resposta: {resposta}')
    break


print('\nMuito obrigado por utilizar a SARAA. Até mais, Senhor!')