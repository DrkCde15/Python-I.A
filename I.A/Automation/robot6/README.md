# Bot de WhatsApp

Bot com interface Tkinter para ler e responder mensagens pelo WhatsApp Web sem API.

O uso principal agora e pela GUI. A interface chama o codigo Python diretamente,
sem montar comandos `argparse` por baixo.

## Como preparar

No PowerShell, dentro da pasta `robot6`:

```powershell
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium
copy .env.example .env
```

## Como abrir

De dois cliques em:

```text
abrir_gui.bat
```

Ou execute a interface diretamente:

```powershell
python main.py
```

## WhatsApp Web

Na primeira execucao, clique em `Iniciar` na interface. Uma janela do navegador
sera aberta. Escaneie o QR Code com o WhatsApp do celular. Depois disso, a sessao
fica salva na pasta `whatsapp_session`.

Na tela voce pode:

- iniciar e parar o bot;
- usar modo `Somente testar`;
- configurar a pasta de sessao;
- ajustar o intervalo de leitura;
- usar uma resposta fixa ou deixar o bot responder pelo `build_reply()`.

## Planilha de contatos

A planilha pode ser `.csv`, `.xlsx` ou `.xlsm`. A primeira linha deve ter
cabecalhos. O bot tenta encontrar automaticamente estas colunas:

- telefone: `telefone`, `celular`, `whatsapp`, `numero`, `phone` ou `number`
- nome: `nome`, `contato`, `cliente` ou `name`
- mensagem: `mensagem`, `message`, `texto` ou `recado`

Exemplo `contatos.csv`:

```csv
telefone,nome,mensagem
+5511999999999,Ana,"Ola {nome}, tudo bem?"
11988887777,Joao,"Ola {nome}, tudo bem?"
```

Na interface, escolha a planilha, preencha uma mensagem se quiser sobrescrever a
coluna `mensagem`, e use `Testar` antes de `Enviar`.

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
