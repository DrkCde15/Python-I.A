# Bot de WhatsApp

Bot simples que gera respostas e envia mensagens pelo WhatsApp Web.

Ele possui dois modos principais:

- modo automatico local, padrao, usando Playwright para ler o WhatsApp Web aberto no navegador;
- modo assistido opcional, usando `pywhatkit`, em que voce informa a mensagem recebida.

O modo automatico nao usa API. Ele depende do HTML do WhatsApp Web, entao pode
precisar de ajuste se o WhatsApp mudar a tela.

## Como preparar

No PowerShell, dentro da pasta `robot6`:

```powershell
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium
copy .env.example .env
```

## Ler e responder pelo WhatsApp Web, sem API

```powershell
python main.py
```

`--web` tambem funciona, mas nao e obrigatorio:

```powershell
python main.py --web
```

Na primeira execucao, uma janela do navegador sera aberta. Escaneie o QR Code
com o WhatsApp do celular. Depois disso, a sessao fica salva na pasta
`whatsapp_session`.

O bot monitora conversas nao lidas e tambem o chat que estiver aberto. Quando
encontra uma mensagem recebida nova, ele passa o texto para `build_reply()` e
digita a resposta no WhatsApp Web.

Para testar sem enviar respostas:

```powershell
python main.py --print-only
```

Para mudar o intervalo de leitura:

```powershell
python main.py --poll-interval 3
```

## Usar em modo assistido

```powershell
python main.py --manual
```

O bot pede o numero do contato, voce cola a mensagem recebida, ele gera a
resposta e pergunta se deve enviar.

## Enviar para contatos de uma planilha

A planilha pode ser `.csv`, `.xlsx` ou `.xlsm`. A primeira linha deve ter
cabecalhos. O bot tenta encontrar automaticamente estas colunas:

- telefone: `telefone`, `celular`, `whatsapp`, `numero`, `phone` ou `number`
- nome: `nome`, `contato`, `cliente` ou `name`
- mensagem: `mensagem`, `message`, `texto` ou `recado`

Exemplo `contatos.csv`:

```csv
telefone,nome,mensagem
+5511999999999,Ana,"Ola Ana, tudo bem?"
11988887777,Joao,"Ola Joao, tudo bem?"
```

O projeto tambem inclui `contatos.example.csv` com numeros ficticios para teste.

Testar sem enviar:

```powershell
python main.py --contacts contatos.example.csv --print-only
```

Enviar uma mensagem igual para todos, usando o nome da planilha:

```powershell
python main.py --contacts contatos.csv --message "Ola {nome}, tudo bem?"
```

Enviar sem confirmar contato por contato:

```powershell
python main.py --contacts contatos.csv --message "Ola {nome}, tudo bem?" --yes
```

Testar so os dois primeiros contatos:

```powershell
python main.py --contacts contatos.csv --message "Ola {nome}, tudo bem?" --limit 2 --print-only
```

Se sua coluna tiver outro nome:

```powershell
python main.py --contacts contatos.xlsx --phone-column Celular --name-column Cliente --message-column Texto
```

## Responder uma mensagem direto pelo terminal

```powershell
python main.py --to +5511999999999 --incoming "oi"
```

## Enviar uma mensagem pronta

```powershell
python main.py --to +5511999999999 --message "Ola, tudo bem?"
```

## Apenas testar a resposta, sem enviar

```powershell
python main.py --incoming "status" --to +5511999999999 --print-only
```

## Comandos que o bot entende

- `oi`
- `menu`
- `ajuda`
- `horario`
- `atendente`
- `status`

## Configuracao

As opcoes ficam no arquivo `.env`:

```env
BOT_NAME=robot6
BOT_TIMEZONE=America/Sao_Paulo
PYWHATKIT_WAIT_TIME=15
PYWHATKIT_CLOSE_TAB=false
PYWHATKIT_CLOSE_TIME=3
WHATSAPP_WEB_SESSION_DIR=whatsapp_session
DEFAULT_COUNTRY_CODE=+55
CONTACT_SEND_DELAY=5
```
