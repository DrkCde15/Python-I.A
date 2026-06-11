"""Le mensagens pelo WhatsApp Web usando Playwright."""

from __future__ import annotations
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import Any

WHATSAPP_WEB_URL = "https://web.whatsapp.com"
READY_SELECTOR = "div[role='grid'], div[contenteditable='true'][role='textbox']"
CHAT_ROW_SELECTOR = "div[role='listitem']"
INCOMING_MESSAGE_SELECTOR = "div.message-in, div[data-id^='false_']"
MESSAGE_TEXT_SELECTOR = "span.selectable-text"
COMPOSER_SELECTOR = "footer div[contenteditable='true'][role='textbox'], footer div[contenteditable='true']"
UNREAD_BADGE_SELECTOR = (
    "span[aria-label*='unread' i], "
    "div[aria-label*='unread' i], "
    "span[aria-label*='n\\00e3o lida' i], "
    "div[aria-label*='n\\00e3o lida' i]"
)
MAX_CHAT_ROWS_TO_SCAN = 30

@dataclass(frozen=True)
class WhatsAppWebOptions:
    session_dir: str
    poll_interval_ms: int
    print_only: bool = False
    message_history_limit: int = 30
    stop_event: Event | None = None
    log_message: Callable[[str], None] | None = None


@dataclass(frozen=True)
class WhatsAppMessage:
    key: str
    text: str


def run_whatsapp_web_bot(
    build_reply: Callable[[str], str],
    options: WhatsAppWebOptions,
) -> None:
    sync_playwright = load_playwright()

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(Path(options.session_dir)),
            headless=False,
            no_viewport=True,
            args=["--start-maximized"],
        )
        page = context.pages[0] if context.pages else context.new_page()
        client = WhatsAppWebClient(page, build_reply, options)

        try:
            client.run()
        except KeyboardInterrupt:
            print("\nBot encerrado.")
        finally:
            context.close()


def load_playwright() -> Any:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        message = (
            "Playwright nao esta instalado. Rode: "
            "pip install -r requirements.txt "
            "e depois python -m playwright install chromium"
        )
        raise SystemExit(message) from exc

    return sync_playwright


class WhatsAppWebClient:
    def __init__(
        self,
        page: Any,
        build_reply: Callable[[str], str],
        options: WhatsAppWebOptions,
    ) -> None:
        self.page = page
        self.build_reply = build_reply
        self.options = options
        self.handled_message_keys: set[str] = set()

    def run(self) -> None:
        self.open_whatsapp()
        if not self.wait_until_logged_in():
            return

        self.remember_visible_messages()
        self.print_ready_message()

        while not self.should_stop():
            self.answer_next_message()
            self.wait_for_next_poll()

    def open_whatsapp(self) -> None:
        self.page.goto(WHATSAPP_WEB_URL, wait_until="domcontentloaded")

    def wait_until_logged_in(self) -> bool:
        self.log("Se aparecer QR Code, escaneie pelo WhatsApp do celular.")

        while not self.should_stop():
            if safe_count(self.page.locator(READY_SELECTOR)) > 0:
                return True

            self.page.wait_for_timeout(1000)

        return False

    def remember_visible_messages(self) -> None:
        for message in self.read_visible_incoming_messages():
            self.handled_message_keys.add(message.key)

    def print_ready_message(self) -> None:
        mode = "somente leitura" if self.options.print_only else "resposta automatica"
        self.log(f"WhatsApp Web pronto em modo {mode}.")

    def answer_next_message(self) -> None:
        self.open_first_unread_chat()
        message = self.read_last_incoming_message()

        if message is None or message.key in self.handled_message_keys:
            return

        self.answer_message(message)

    def open_first_unread_chat(self) -> bool:
        chats = self.page.locator(CHAT_ROW_SELECTOR)
        chat_count = min(safe_count(chats), MAX_CHAT_ROWS_TO_SCAN)

        for index in range(chat_count):
            chat = chats.nth(index)
            if self.is_unread_chat(chat):
                chat.click()
                self.page.wait_for_timeout(500)
                return True

        return False

    def is_unread_chat(self, chat: Any) -> bool:
        if safe_count(chat.locator(UNREAD_BADGE_SELECTOR)) > 0:
            return True

        return contains_unread_marker(safe_inner_text(chat))

    def read_visible_incoming_messages(self) -> list[WhatsAppMessage]:
        messages = self.page.locator(INCOMING_MESSAGE_SELECTOR)
        message_count = safe_count(messages)
        first_index = max(0, message_count - self.options.message_history_limit)

        return [
            message
            for index in range(first_index, message_count)
            if (message := self.read_incoming_message(messages.nth(index), index))
        ]

    def read_last_incoming_message(self) -> WhatsAppMessage | None:
        messages = self.read_visible_incoming_messages()
        return messages[-1] if messages else None

    def read_incoming_message(self, message: Any, index: int) -> WhatsAppMessage | None:
        text = read_message_text(message)
        if not text:
            return None

        return WhatsAppMessage(
            key=message_key(message, index, text),
            text=text,
        )

    def answer_message(self, message: WhatsAppMessage) -> None:
        reply = self.build_reply(message.text)
        self.log(f"\nMensagem recebida: {message.text}")
        self.log(f"Resposta gerada: {reply}")

        if not self.options.print_only:
            self.send_message(reply)

        self.handled_message_keys.add(message.key)

    def send_message(self, text: str) -> None:
        composer = self.find_composer()
        composer.click()
        self.page.keyboard.insert_text(text)
        self.page.keyboard.press("Enter")

    def find_composer(self) -> Any:
        composers = self.page.locator(COMPOSER_SELECTOR)
        composer_count = safe_count(composers)

        if composer_count == 0:
            raise RuntimeError("Campo de mensagem do WhatsApp Web nao encontrado.")

        return composers.nth(composer_count - 1)

    def should_stop(self) -> bool:
        return bool(self.options.stop_event and self.options.stop_event.is_set())

    def wait_for_next_poll(self) -> None:
        remaining_ms = self.options.poll_interval_ms

        while remaining_ms > 0 and not self.should_stop():
            delay_ms = min(250, remaining_ms)
            self.page.wait_for_timeout(delay_ms)
            remaining_ms -= delay_ms

    def log(self, message: str) -> None:
        if self.options.log_message:
            self.options.log_message(message)
            return

        print(message)


def read_message_text(message: Any) -> str:
    spans = message.locator(MESSAGE_TEXT_SELECTOR)
    texts = [safe_inner_text(spans.nth(index)) for index in range(safe_count(spans))]
    return "\n".join(text for text in texts if text).strip()


def message_key(message: Any, index: int, text: str) -> str:
    data_id = safe_get_attribute(message, "data-id")
    if data_id:
        return data_id

    return f"{index}:{normalize_text(text)}"


def contains_unread_marker(value: str) -> bool:
    text = normalize_text(value)
    return "unread" in text or "nao lida" in text


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_text.lower().split())


def safe_count(locator: Any) -> int:
    try:
        return locator.count()
    except Exception:
        return 0


def safe_inner_text(locator: Any) -> str:
    try:
        return locator.inner_text(timeout=500).strip()
    except Exception:
        return ""


def safe_get_attribute(locator: Any, attribute_name: str) -> str:
    try:
        return locator.get_attribute(attribute_name, timeout=500) or ""
    except Exception:
        return ""
