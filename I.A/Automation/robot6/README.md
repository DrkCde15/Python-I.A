# Bot de WhatsApp

Bot simples que gera respostas e envia mensagens pelo WhatsApp Web usando
`pywhatkit`.

Importante: `pywhatkit` nao recebe mensagens automaticamente. Ele abre o
WhatsApp Web no navegador e envia mensagens para um contato. Para resposta
100% automatica de mensagens recebidas, seria preciso usar uma API com webhook.

## Como preparar

No PowerShell, dentro da pasta `robot6`:

```powershell
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Antes do primeiro envio, abra o WhatsApp Web no navegador e faca login:

```text
https://web.whatsapp.com
```

## Usar em modo interativo

```powershell
python main.py
```

O bot pede o numero do contato, voce cola a mensagem recebida, ele gera a
resposta e pergunta se deve enviar.

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
```
