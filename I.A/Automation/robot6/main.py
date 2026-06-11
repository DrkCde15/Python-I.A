"""Bot de WhatsApp com modo assistido e modo WhatsApp Web."""

from __future__ import annotations

import argparse
import os
import sys
import time
import unicodedata
from collections.abc import Callable
from datetime import datetime, timezone, tzinfo
from string import Formatter
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from reader_msg import WhatsAppWebOptions, run_whatsapp_web_bot
from contact_reader import ContactSheetError, load_contact_rows
import pywhatkit
from dotenv import load_dotenv


load_dotenv()

DEFAULT_BOT_NAME = "robot6"
DEFAULT_TIMEZONE = "America/Sao_Paulo"
DEFAULT_PYWHATKIT_WAIT_TIME = 15
DEFAULT_PYWHATKIT_CLOSE_TIME = 3
DEFAULT_WEB_SESSION_DIR = "whatsapp_session"
DEFAULT_WEB_POLL_INTERVAL = 2.0
DEFAULT_COUNTRY_CODE = os.getenv("DEFAULT_COUNTRY_CODE", "+55")
DEFAULT_CONTACT_DELAY = float(os.getenv("CONTACT_SEND_DELAY", "5"))

BOT_NAME = os.getenv("BOT_NAME", DEFAULT_BOT_NAME)
BOT_TIMEZONE = os.getenv("BOT_TIMEZONE", DEFAULT_TIMEZONE)
DEFAULT_WAIT_TIME = int(os.getenv("PYWHATKIT_WAIT_TIME", DEFAULT_PYWHATKIT_WAIT_TIME))
DEFAULT_CLOSE_TIME = int(os.getenv("PYWHATKIT_CLOSE_TIME", DEFAULT_PYWHATKIT_CLOSE_TIME))
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


# CORREÇÃO 3: dict de dispatch substitui o if/elif encadeado em build_reply.
# Chaves são os textos normalizados; valores são strings ou callables (sem args).
_EXACT_REPLIES: dict[str, str | Callable[[], str]] = {
    # saudações
    "oi":            lambda: f"Ola! Eu sou o {BOT_NAME}. Envie 'menu' para ver as opcoes.",
    "ola":           lambda: f"Ola! Eu sou o {BOT_NAME}. Envie 'menu' para ver as opcoes.",
    "bom dia":       lambda: f"Ola! Eu sou o {BOT_NAME}. Envie 'menu' para ver as opcoes.",
    "boa tarde":     lambda: f"Ola! Eu sou o {BOT_NAME}. Envie 'menu' para ver as opcoes.",
    "boa noite":     lambda: f"Ola! Eu sou o {BOT_NAME}. Envie 'menu' para ver as opcoes.",
    # menu / ajuda
    "menu":          menu_message,
    "ajuda":         menu_message,
    "help":          menu_message,
    "opcoes":        menu_message,
    "opcao":         menu_message,
    # opção 1 — horário
    "1":             "Nosso atendimento funciona de segunda a sexta, das 09h as 18h.",
    "horario":       "Nosso atendimento funciona de segunda a sexta, das 09h as 18h.",
    "horarios":      "Nosso atendimento funciona de segunda a sexta, das 09h as 18h.",
    "atendimento":   "Nosso atendimento funciona de segunda a sexta, das 09h as 18h.",
    # opção 2 — atendente
    "2":                    "Certo, vou registrar que voce quer falar com um atendente. Alguem da equipe deve responder assim que possivel.",
    "humano":               "Certo, vou registrar que voce quer falar com um atendente. Alguem da equipe deve responder assim que possivel.",
    "atendente":            "Certo, vou registrar que voce quer falar com um atendente. Alguem da equipe deve responder assim que possivel.",
    "falar com atendente":  "Certo, vou registrar que voce quer falar com um atendente. Alguem da equipe deve responder assim que possivel.",
    "suporte":              "Certo, vou registrar que voce quer falar com um atendente. Alguem da equipe deve responder assim que possivel.",
    # opção 3 — status
    "3":        lambda: f"{BOT_NAME} esta online. Hora do servidor: {current_time()}.",
    "status":   lambda: f"{BOT_NAME} esta online. Hora do servidor: {current_time()}.",
    "online":   lambda: f"{BOT_NAME} esta online. Hora do servidor: {current_time()}.",
}

_FALLBACK = (
    'Recebi sua mensagem: "{message}".\n\n'
    "Ainda estou aprendendo a responder esse assunto. "
    "Envie 'menu' para ver as opcoes disponiveis."
)


def build_reply(message: str) -> str:
    if not message or not message.strip():
        return "Recebi sua mensagem, mas ela veio sem texto. Pode enviar novamente?"

    text = normalize_text(message)
    handler = _EXACT_REPLIES.get(text)

    if handler is None:
        return _FALLBACK.format(message=message.strip())

    return handler() if callable(handler) else handler


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
    # CORREÇÃO 2: default avaliado em tempo de execução, não no import do módulo.
    # Garante que alterações no .env (ou mocks em testes) sejam respeitadas.
    close_tab: bool | None = None,
    close_time: int = DEFAULT_CLOSE_TIME,
) -> None:
    if close_tab is None:
        close_tab = is_enabled(os.getenv("PYWHATKIT_CLOSE_TAB"))

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
    raw_phone = args.to or input("Numero do contato com DDI (+55...): ")

    # CORREÇÃO 4: ValueError de validate_phone capturado aqui em vez de crashar
    try:
        phone_number = validate_phone(raw_phone)
    except ValueError as exc:
        raise SystemExit(f"Numero invalido: {exc}") from exc

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


def contacts_mode(args: argparse.Namespace) -> None:

    try:
        contacts = load_contact_rows(
            args.contacts,
            args.phone_column,
            args.name_column,
            args.message_column,
        )
    except ContactSheetError as exc:
        raise SystemExit(f"Erro na planilha: {exc}") from exc

    selected_contacts = limit_contacts(contacts, args.limit)
    if not selected_contacts:
        raise SystemExit("Nenhum contato encontrado na planilha.")

    for contact in selected_contacts:
        send_contact_message(contact, args)


def limit_contacts(contacts: list, limit: int) -> list:
    if limit <= 0:
        return contacts

    return contacts[:limit]


def send_contact_message(contact, args: argparse.Namespace) -> None:
    try:
        phone_number = format_contact_phone(contact.phone_number, args.default_country_code)
        message = build_contact_message(contact, args)
    except ValueError as exc:
        print(f"Linha {contact.row_number} ignorada: {exc}")
        return

    print_contact_message(contact, phone_number, message)
    if args.print_only:
        return

    if not args.yes and not ask_to_send_contact(contact, phone_number):
        return

    send_whatsapp_message(
        phone_number,
        message,
        args.wait_time,
        args.close_tab,
        args.close_time,
    )
    wait_between_contacts(args.contact_delay)


def format_contact_phone(phone_number: str, default_country_code: str) -> str:
    if not phone_number.strip():
        raise ValueError("telefone vazio.")

    country_digits = digits_only(default_country_code)
    if not country_digits:
        raise ValueError("DDI padrao invalido.")

    if phone_number.strip().startswith("+"):
        return validate_phone(f"+{digits_only(phone_number)}")

    phone_digits = digits_only(phone_number)
    if not phone_digits:
        raise ValueError("telefone sem digitos.")

    if phone_digits.startswith(country_digits):
        return validate_phone(f"+{phone_digits}")

    return validate_phone(f"+{country_digits}{phone_digits}")


def digits_only(value: str) -> str:
    return "".join(character for character in value if character.isdigit())


def build_contact_message(contact, args: argparse.Namespace) -> str:
    if args.message:
        return render_contact_template(args.message, contact)

    if contact.message:
        return render_contact_template(contact.message, contact)

    if args.incoming:
        return build_reply(args.incoming)

    raise ValueError("sem mensagem; use --message ou uma coluna mensagem.")


def render_contact_template(template: str, contact) -> str:
    fields = contact_template_fields(contact)
    validate_template_fields(template, fields)
    return template.format_map(fields)


def contact_template_fields(contact) -> dict[str, str]:
    fields = {
        template_field_name(header): value
        for header, value in contact.values.items()
        if template_field_name(header)
    }
    fields.update(
        {
            "linha": str(contact.row_number),
            "nome": contact.name,
            "telefone": contact.phone_number,
        }
    )
    return fields


def validate_template_fields(template: str, fields: dict[str, str]) -> None:
    for _, field_name, _, _ in Formatter().parse(template):
        if not field_name:
            continue

        root_field = field_name.split(".", 1)[0].split("[", 1)[0]
        if root_field not in fields:
            raise ValueError(f"campo {{{root_field}}} nao existe na planilha.")


def template_field_name(value: str) -> str:
    text = normalize_text(value)
    return text.replace(" ", "_")


def print_contact_message(contact, phone_number: str, message: str) -> None:
    contact_name = contact.name or "sem nome"
    print(f"\nLinha {contact.row_number}: {contact_name} ({phone_number})")
    print("Mensagem:")
    print(message)


def ask_to_send_contact(contact, phone_number: str) -> bool:
    contact_name = contact.name or f"linha {contact.row_number}"
    answer = input(f"Enviar para {contact_name} ({phone_number})? [s/N]: ")
    return normalize_text(answer) in {"s", "sim", "y", "yes"}


def wait_between_contacts(delay_seconds: float) -> None:
    if delay_seconds > 0:
        time.sleep(delay_seconds)


def web_mode(args: argparse.Namespace) -> None:

    def reply_to(incoming_message: str) -> str:
        return args.message or build_reply(incoming_message)

    options = WhatsAppWebOptions(
        session_dir=args.web_session_dir,
        poll_interval_ms=int(args.poll_interval * 1000),
        print_only=args.print_only,
    )
    run_whatsapp_web_bot(reply_to, options)


def launch_gui() -> None:
    sys.modules.setdefault("main", sys.modules[__name__])

    from gui import main as gui_main

    gui_main()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera respostas e envia mensagens pelo WhatsApp Web."
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
    parser.add_argument(
        "--web",
        action="store_true",
        help="Le conversas pelo WhatsApp Web e responde sem usar API. Este ja e o modo padrao.",
    )
    parser.add_argument(
        "--manual",
        action="store_true",
        help="Usa o modo assistido antigo, digitando a mensagem recebida no terminal.",
    )
    parser.add_argument(
        "--web-session-dir",
        default=os.getenv("WHATSAPP_WEB_SESSION_DIR", DEFAULT_WEB_SESSION_DIR),
        help="Pasta usada para manter a sessao do navegador do WhatsApp Web.",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=DEFAULT_WEB_POLL_INTERVAL,
        help="Intervalo em segundos entre leituras do WhatsApp Web.",
    )
    parser.add_argument(
        "--contacts",
        help="Planilha .csv, .xlsx ou .xlsm com contatos para envio em lote.",
    )
    parser.add_argument(
        "--phone-column",
        default="",
        help="Nome da coluna de telefone, se nao quiser usar a deteccao automatica.",
    )
    parser.add_argument(
        "--name-column",
        default="",
        help="Nome da coluna de nome, se nao quiser usar a deteccao automatica.",
    )
    parser.add_argument(
        "--message-column",
        default="",
        help="Nome da coluna de mensagem, se cada contato tiver um texto proprio.",
    )
    parser.add_argument(
        "--default-country-code",
        default=DEFAULT_COUNTRY_CODE,
        help="DDI usado quando o telefone da planilha vier sem codigo do pais.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limita a quantidade de contatos lidos da planilha. 0 envia para todos.",
    )
    parser.add_argument(
        "--contact-delay",
        type=float,
        default=DEFAULT_CONTACT_DELAY,
        help="Pausa em segundos entre envios da planilha.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Envia mensagens da planilha sem perguntar contato por contato.",
    )
    return parser.parse_args()


def main() -> None:
    if len(sys.argv) == 1:
        launch_gui()
        return

    args = parse_args()

    if args.web and args.contacts:
        raise SystemExit("Use --web ou --contacts, nao os dois ao mesmo tempo.")

    if args.web and args.manual:
        raise SystemExit("Use --web ou --manual, nao os dois ao mesmo tempo.")

    if args.web:
        web_mode(args)
        return

    if args.contacts:
        contacts_mode(args)
        return

    if args.manual:
        interactive_mode(args)
        return

    if args.to and (args.incoming or args.message):
        # CORREÇÃO 4 (também no fluxo não-interativo)
        try:
            validate_phone(args.to)
        except ValueError as exc:
            raise SystemExit(f"Numero invalido: {exc}") from exc

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

    if args.incoming and not args.to:
        raise SystemExit("Use --incoming junto com --to, ou rode sem --incoming para o modo WhatsApp Web.")

    web_mode(args)


if __name__ == "__main__":
    main()
