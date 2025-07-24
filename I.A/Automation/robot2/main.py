import openpyxl
import pyautogui
from time import sleep
import pyperclip

#entrar na planilha
workbook = openpyxl.load_workbook('./planilha/produtos_ficticios.xlsx')
sheet_produtos = workbook['Produtos']

#copiar informações de um campo e colar no seu campo correspondente
for linha in sheet_produtos.iter_rows(min_row=2):
    # Nome do Produto
    nome_produto = linha[0].value
    pyperclip.copy(nome_produto)
    pyautogui.click(1234,299,duration=1)
    pyautogui.hotkey('ctrl','v')

    # Descrição
    descricao = linha[1].value
    pyperclip.copy(descricao)
    pyautogui.click(1160,416,duration=1)
    pyautogui.hotkey('ctrl','v')
    
    # Categoria
    categoria = linha[2].value
    pyperclip.copy(categoria)
    pyautogui.click(1195,575,duration=1)
    pyautogui.hotkey('ctrl','v')

    # Codigo Produto
    codigo_produto = linha[3].value
    pyperclip.copy(codigo_produto)
    pyautogui.click(1158,682,duration=1)
    pyautogui.hotkey('ctrl','v')

    # Peso
    peso = linha[4].value
    pyperclip.copy(peso)
    pyautogui.click(1175,798,duration=1)
    pyautogui.hotkey('ctrl','v')

    # Dimensões
    dimensoes = linha[5].value
    pyperclip.copy(dimensoes)
    pyautogui.click(1197,897,duration=1)
    pyautogui.hotkey('ctrl','v')

    # Botão próximo
    pyautogui.click(1171,970,duration=1)
    sleep(5)

    # Preço
    preco = linha[6].value
    pyperclip.copy(preco)
    pyautogui.click(1216,329,duration=1)
    pyautogui.hotkey('ctrl','v')

    # Quantidade em estoque
    quantidade_em_estoque = linha[7].value
    pyperclip.copy(quantidade_em_estoque)
    pyautogui.click(1247,443,duration=1)
    pyautogui.hotkey('ctrl','v')

    # Data de validade
    data_de_validade = linha[8].value
    pyperclip.copy(data_de_validade)
    pyautogui.click(1227,547,duration=1)
    pyautogui.hotkey('ctrl','v')
    
    # Cor
    cor = linha[9].value
    pyperclip.copy(cor)
    pyautogui.click(1230,648,duration=1)
    pyautogui.hotkey('ctrl','v')

    # Tamanho
    tamanho = linha[10].value
    pyautogui.click(1246,758,duration=1)
    if tamanho == 'Pequeno':
        pyautogui.click(1241,814,duration=1)
    elif tamanho == 'Médio':
        pyautogui.click(1217,853,duration=1)
    else:
        pyautogui.click(1204,881,duration=1)

    # material    
    material = linha[11].value
    pyperclip.copy(material)
    pyautogui.click(1220,860,duration=1)
    pyautogui.hotkey('ctrl','v')
    
    # Botão próximo
    pyautogui.click(1311,870,duration=1)
    sleep(5)
    
    # material    
    material = linha[11].value
    pyperclip.copy(material)
    pyautogui.click(1482,753,duration=1)
    pyautogui.hotkey('ctrl','v')
    
    # Botão próximo
    pyautogui.click(1173,941,duration=1)
    sleep(5)
    
    #Fabricante
    fabricante = linha[12].value
    pyperclip.copy(fabricante)
    pyautogui.click(1398,360,duration=1)
    pyautogui.hotkey('ctrl','v')

    #Pais de origem
    pais_origem = linha[13].value
    pyperclip.copy(pais_origem)
    pyautogui.click(1266,469,duration=1)
    pyautogui.hotkey('ctrl','v')

    #Observações
    observacoes = linha[14].value
    pyperclip.copy(observacoes)
    pyautogui.click(1238,587,duration=1)
    pyautogui.hotkey('ctrl','v')

    # Codigo de barras
    codigo_de_barras = linha[15].value
    pyperclip.copy(codigo_de_barras)
    pyautogui.click(1281,738,duration=1)
    pyautogui.hotkey('ctrl','v')
    
    # Localização armazem
    localizacao_armazem = linha[16].value
    pyperclip.copy(localizacao_armazem)
    pyautogui.click(1232,841,duration=1)
    pyautogui.hotkey('ctrl','v')

    # Botão concluir
    pyautogui.click(1185,920,duration=1)
    # Botão confirmar inclusão
    pyautogui.click(1643,232,duration=1)
    # iniciar cadastro novamente
    pyautogui.click(1442,631,duration=1)
    break #excluir o break caso queira completar a planilha