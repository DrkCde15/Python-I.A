from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def iniciar_driver():
    #Inicializa o ChromeDriver com o webdriver_manager.
    print("Iniciando...\n")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    return driver

def realizar_pesquisa(driver, termo):
    #Realiza a pesquisa no Google usando o termo fornecido
    driver.get("https://www.google.com.br/")

    try:
        # Espera até o campo de pesquisa estar visível
        pesquisa = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "q"))
        )
        pesquisa.send_keys(termo)  # Envia o termo para a pesquisa
        pesquisa.send_keys(Keys.RETURN)  # Simula pressionamento de Enter

        # Espera os resultados aparecerem
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "search"))
        )
        print(f"Resultados para '{termo}' carregados com sucesso.")

    except Exception as e:
        print(f"Erro ao realizar a pesquisa: {e}")

def manter_navegador_ativo():
    #Mantém o navegador aberto até o usuário pressionar Enter.
    input("\nPressione Enter para fechar o navegador...")

def fechar_driver(driver):
    #Fecha o navegador após o processo.
    print("Fechando o navegador...")
    driver.quit()

if __name__ == "__main__":
    # Solicita ao usuário o termo para pesquisa
    termo_pesquisa = input("O que você gostaria de pesquisar no Google? ")

    # Iniciar o driver
    driver = iniciar_driver()

    try:
        # Realiza a pesquisa no Google
        realizar_pesquisa(driver, termo_pesquisa)

        # Mantém o navegador aberto até o usuário decidir fechá-lo
        manter_navegador_ativo()

    finally:
        # Fechar o navegador
        fechar_driver(driver)
