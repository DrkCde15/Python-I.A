"""Bot de WhatsApp com pywhatkit.

O pywhatkit automatiza o WhatsApp Web para enviar mensagens. Ele nao recebe
mensagens automaticamente, entao este bot funciona em modo assistido: voce
informa a mensagem recebida e ele gera/envia a resposta.
"""

from __future__ import annotations

import argparse
import os
import unicodedata
from datetime import datetime, timezone, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pywhatkit
from dotenv import load_dotenv


load_dotenv()

BOT_NAME = os.getenv("BOT_NAME")
BOT_TIMEZONE = os.getenv("BOT_TIMEZONE")
DEFAULT_WAIT_TIME = int(os.getenv("PYWHATKIT_WAIT_TIME"))
DEFAULT_CLOSE_TIME = int(os.getenv("PYWHATKIT_CLOSE_TIME"))
DEFAULT_CLOSE_TAB = os.getenv("PYWHATKIT_CLOSE_TAB")


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_text.lower().split())


def is_enabled(value: str | None) -> bool:
    return normalize_text(value or "") in {"1", "true", "sim", "yes", "on"}


def get_timezone() -> tzinfo:
    try:
        return ZoneInfo(BOT_TIMEZONE)
    except ZoneInfoNotFoundError:
        return timezone.utc


def current_time() -> str:
    now = datetime.now(get_timezone())
    return now.strftime("%d/%m/%Y %H:%M")


def menu_message() -> str:
    return (
        f"Menu do {BOT_NAME}\n"
        "1 - Horario de atendimento\n"
        "2 - Falar com um atendente\n"
        "3 - Status do bot\n\n"
        "Voce tambem pode enviar: oi, ajuda, horario, atendente ou status."
    )


def build_reply(message: str) -> str:
    text = normalize_text(message)

    if not text:
        return "Recebi sua mensagem, mas ela veio sem texto. Pode enviar novamente?"

    if text in {"oi", "ola", "bom dia", "boa tarde", "boa noite"}:
        return f"Ola! Eu sou o {BOT_NAME}. Envie 'menu' para ver as opcoes."

    if text in {"menu", "ajuda", "help", "opcoes", "opcao"}:
        return menu_message()

    if text in {"1", "horario", "horarios", "atendimento"}:
        return "Nosso atendimento funciona de segunda a sexta, das 09h as 18h."

    if text in {"2", "humano", "atendente", "falar com atendente", "suporte"}:
        return (
            "Certo, vou registrar que voce quer falar com um atendente. "
            "Alguem da equipe deve responder assim que possivel."
        )

    if text in {"3", "status", "online"}:
        return f"{BOT_NAME} esta online. Hora do servidor: {current_time()}."

    return (
        "Recebi sua mensagem: "
        f"\"{message.strip()}\".\n\n"
        "Ainda estou aprendendo a responder esse assunto. Envie 'menu' para ver "
        "as opcoes disponiveis."
    )


def validate_phone(phone_number: str) -> str:
    phone_number = phone_number.strip()
    digits = phone_number[1:] if phone_number.startswith("+") else phone_number

    if not phone_number.startswith("+") or not digits.isdigit():
        raise ValueError("Use o numero em formato internacional, exemplo: +5511999999999")

    return phone_number


def send_whatsapp_message(
    phone_number: str,
    message: str,
    wait_time: int = DEFAULT_WAIT_TIME,
    close_tab: bool = is_enabled(DEFAULT_CLOSE_TAB),
    close_time: int = DEFAULT_CLOSE_TIME,
) -> None:
    pywhatkit.sendwhatmsg_instantly(
        validate_phone(phone_number),
        message,
        wait_time,
        close_tab,
        close_time,
    )


def ask_to_send() -> bool:
    answer = input("Enviar essa resposta pelo WhatsApp Web? [s/N]: ")
    return normalize_text(answer) in {"s", "sim", "y", "yes"}


def interactive_mode(args: argparse.Namespace) -> None:
    phone_number = args.to or input("Numero do contato com DDI (+55...): ")
    phone_number = validate_phone(phone_number)

    print(f"{BOT_NAME} pronto. Digite 'sair' para encerrar.")
    while True:
        incoming_message = input("\nMensagem recebida: ").strip()
        if normalize_text(incoming_message) in {"sair", "exit", "quit"}:
            break

        reply = args.message or build_reply(incoming_message)
        print("\nResposta gerada:")
        print(reply)

        if args.print_only:
            continue

        if ask_to_send():
            send_whatsapp_message(
                phone_number,
                reply,
                args.wait_time,
                args.close_tab,
                args.close_time,
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera e envia respostas no WhatsApp Web usando pywhatkit."
    )
    parser.add_argument("-t", "--to", help="Numero do contato com DDI. Ex: +5511999999999")
    parser.add_argument(
        "-i",
        "--incoming",
        help="Mensagem recebida. O bot gera uma resposta para esse texto.",
    )
    parser.add_argument(
        "-m",
        "--message",
        help="Mensagem pronta para enviar. Se usada, ignora a resposta automatica.",
    )
    parser.add_argument(
        "--print-only",
        action="store_true",
        help="Mostra a resposta sem abrir o WhatsApp Web.",
    )
    parser.add_argument(
        "--wait-time",
        type=int,
        default=DEFAULT_WAIT_TIME,
        help="Segundos para aguardar o WhatsApp Web carregar antes de enviar.",
    )
    parser.add_argument(
        "--close-tab",
        action="store_true",
        default=is_enabled(DEFAULT_CLOSE_TAB),
        help="Fecha a aba depois do envio.",
    )
    parser.add_argument(
        "--close-time",
        type=int,
        default=DEFAULT_CLOSE_TIME,
        help="Segundos para aguardar antes de fechar a aba.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.incoming or args.message:
        if not args.to:
            raise SystemExit("Informe o destinatario com --to +55...")

        reply = args.message or build_reply(args.incoming or "")
        print(reply)

        if not args.print_only:
            send_whatsapp_message(
                args.to,
                reply,
                args.wait_time,
                args.close_tab,
                args.close_time,
            )
        return

    interactive_mode(args)


if __name__ == "__main__":
    main()
