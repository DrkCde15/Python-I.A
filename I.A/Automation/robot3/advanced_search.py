import os
import time
from google import genai
from dotenv import load_dotenv
from ddgs import DDGS # DuckDuckGo Search API
import trafilatura # Biblioteca avançada de scraping de conteúdo web
from fpdf import FPDF

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def extrair_conteudo_avancado(url):
    """Usa trafilatura para extrair texto de sites difíceis."""
    try:
        # O trafilatura já lida com headers e limpeza de HTML internamente
        downloaded = trafilatura.fetch_url(url)
        # Extrai apenas o texto principal, ignorando menus e rodapés
        texto = trafilatura.extract(downloaded, include_comments=False, include_tables=True)
        
        if texto and len(texto) > 300:
            return texto[:8000] # Limite para a IA
        return None
    except Exception as e:
        print(f"Erro técnico no site: {e}")
        return None

def realizar_pesquisa_robusta():
    print("\n=== AGENTE DE PESQUISA AVANÇADO ===")
    tema = input("Qual o tema da pesquisa? ")
    
    dados_finais = {}
    
    with DDGS() as ddgs:
        print(f"Vasculhando a web por '{tema}'...")
        buscas = list(ddgs.text(f"{tema} artigo", region='pt-br', max_results=5))

    for i, res in enumerate(buscas, 1):
        url = res['href']
        print(f"[{i}] Analisando: {url}")
        
        texto_util = extrair_conteudo_avancado(url)
        
        if texto_util:
            print("Conteúdo extraído! Consultando Gemini...")
            
            # SISTEMA DE RETRY (ESPERA) PARA EVITAR ERRO 429
            sucesso_ia = False
            tentativas = 0
            while not sucesso_ia and tentativas < 3:
                try:
                    prompt = f"Crie um resumo estruturado em português sobre '{tema}' usando este texto: {texto_util}"
                    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                    dados_finais[url] = response.text
                    sucesso_ia = True
                    # Pausa obrigatória de 10 segundos entre sites para respeitar a cota free
                    time.sleep(10) 
                except Exception as e:
                    if "429" in str(e):
                        print("Cota atingida. Aguardando 25 segundos para tentar novamente...")
                        time.sleep(25)
                        tentativas += 1
                    else:
                        print(f"Erro inesperado: {e}")
                        break
        else:
            print("Site protegido ou sem texto relevante.")

    if dados_finais:
        gerar_pdf_final(tema, dados_finais)
    else:
        print("\nNenhum dado foi processado devido aos limites da API.")

def gerar_pdf_final(tema, dados):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 16) # Helvetica é mais segura que Arial em alguns sistemas
    pdf.cell(0, 10, f"Relatorio: {tema}", ln=True, align='C')
    pdf.ln(10)

    for url, resumo in dados.items():
        pdf.set_font("Helvetica", 'B', 10)
        pdf.multi_cell(0, 8, txt=f"FONTE: {url}")
        pdf.set_font("Helvetica", size=10)
        # Limpeza radical de caracteres estranhos para o PDF
        texto_limpo = resumo.encode('ascii', 'ignore').decode('ascii')
        pdf.multi_cell(0, 6, txt=texto_limpo)
        pdf.ln(10)

    pdf.output(f"Relatorio_{tema.replace(' ', '_')}.pdf")
    print(f"\nPDF gerado.")

if __name__ == "__main__":
    realizar_pesquisa_robusta()