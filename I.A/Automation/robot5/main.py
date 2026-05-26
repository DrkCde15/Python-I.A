import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

import pandas as pd


def carregar_env(caminho_env='.env'):
    caminho = Path(caminho_env)

    if not caminho.exists():
        raise FileNotFoundError(f'Arquivo {caminho_env} nao encontrado.')

    for linha in caminho.read_text(encoding='utf-8-sig').splitlines():
        linha = linha.strip()

        if not linha or linha.startswith('#') or '=' not in linha:
            continue

        chave, valor = linha.split('=', 1)
        chave = chave.strip()
        valor = valor.strip().strip('"').strip("'")

        os.environ.setdefault(chave, valor)


carregar_env()

email_remetente = os.getenv('EMAIL')
senha_app = os.getenv('EMAIL_PASS_APP')
email_destino = os.getenv('EMAIL_DESTINO', email_remetente)
smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
smtp_port = int(os.getenv('SMTP_PORT', '587'))

if not email_remetente or not senha_app:
    raise ValueError('Configure EMAIL e EMAIL_PASS_APP no arquivo .env.')

# importar a base de dados
tabela_vendas = pd.read_excel('Vendas.xlsx')

# visualizar a base de dados
pd.set_option('display.max_columns', None)
print(tabela_vendas)

# faturamento por loja
faturamento = tabela_vendas[['ID Loja', 'Valor Final']].groupby('ID Loja').sum()
print(faturamento)

# quantidade de produtos vendidos por loja
quantidade = tabela_vendas[['ID Loja', 'Quantidade']].groupby('ID Loja').sum()
print(quantidade)

print('-' * 50)

# ticket medio por produto em cada loja
ticket_medio = (faturamento['Valor Final'] / quantidade['Quantidade']).to_frame()
ticket_medio = ticket_medio.rename(columns={0: 'Ticket Medio'})
print(ticket_medio)

html = f'''
<p>Prezados,</p>

<p>Segue o Relatorio de Vendas por cada Loja.</p>

<p>Faturamento:</p>
{faturamento.to_html(formatters={'Valor Final': 'R${:,.2f}'.format})}

<p>Quantidade Vendida:</p>
{quantidade.to_html()}

<p>Ticket Medio dos Produtos em cada Loja:</p>
{ticket_medio.to_html(formatters={'Ticket Medio': 'R${:,.2f}'.format})}

<p>Qualquer duvida estou a disposicao.</p>

<p>Att.,</p>
<p>Mintify</p>
'''

mensagem = EmailMessage()
mensagem['From'] = email_remetente
mensagem['To'] = email_destino
mensagem['Subject'] = 'Relatorio de Vendas por Loja'
mensagem.set_content('Segue o Relatorio de Vendas por cada Loja.')
mensagem.add_alternative(html, subtype='html')

with smtplib.SMTP(smtp_server, smtp_port) as servidor:
    servidor.starttls()
    servidor.login(email_remetente, senha_app)
    servidor.send_message(mensagem)

print('Email Enviado')
