"""Interface Tkinter para controlar o bot sem comandos argparse."""

from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from contact_reader import ContactSheetError, load_contact_rows
from main import (
    DEFAULT_CLOSE_TIME,
    DEFAULT_CONTACT_DELAY,
    DEFAULT_COUNTRY_CODE,
    DEFAULT_WAIT_TIME,
    build_reply,
    format_contact_phone,
    render_contact_template,
    send_whatsapp_message,
    wait_between_contacts,
)
from reader_msg import WhatsAppWebOptions, run_whatsapp_web_bot


DEFAULT_SESSION_DIR = os.getenv("WHATSAPP_WEB_SESSION_DIR", "whatsapp_session")
DEFAULT_POLL_INTERVAL = "2"


class BotGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Robot6 WhatsApp")
        self.geometry("860x640")
        self.minsize(760, 560)

        self.worker_thread: threading.Thread | None = None
        self.stop_event: threading.Event | None = None
        self.output_queue: queue.Queue[str] = queue.Queue()

        self.create_variables()
        self.create_widgets()
        self.after(100, self.flush_output)
        self.protocol("WM_DELETE_WINDOW", self.close_window)

    def create_variables(self) -> None:
        self.session_dir = tk.StringVar(value=DEFAULT_SESSION_DIR)
        self.poll_interval = tk.StringVar(value=DEFAULT_POLL_INTERVAL)
        self.fixed_reply = tk.StringVar()
        self.print_only = tk.BooleanVar(value=False)
        self.contacts_path = tk.StringVar()
        self.contacts_message = tk.StringVar()
        self.contacts_limit = tk.StringVar(value="0")

    def create_widgets(self) -> None:
        container = ttk.Frame(self, padding=16)
        container.pack(fill=tk.BOTH, expand=True)

        self.create_web_controls(container)
        self.create_contact_controls(container)
        self.create_log(container)

    def create_web_controls(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="WhatsApp Web sem API", padding=12)
        frame.pack(fill=tk.X)

        ttk.Label(frame, text="Sessao").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(frame, textvariable=self.session_dir).grid(row=0, column=1, sticky=tk.EW, padx=8)

        ttk.Label(frame, text="Intervalo").grid(row=0, column=2, sticky=tk.W)
        ttk.Entry(frame, textvariable=self.poll_interval, width=8).grid(row=0, column=3, padx=8)

        ttk.Label(frame, text="Resposta fixa").grid(row=1, column=0, sticky=tk.W, pady=(8, 0))
        ttk.Entry(frame, textvariable=self.fixed_reply).grid(
            row=1,
            column=1,
            columnspan=3,
            sticky=tk.EW,
            padx=8,
            pady=(8, 0),
        )

        ttk.Checkbutton(frame, text="Somente testar", variable=self.print_only).grid(
            row=2,
            column=0,
            sticky=tk.W,
            pady=(10, 0),
        )
        ttk.Button(frame, text="Iniciar", command=self.start_web_bot).grid(row=2, column=2, pady=(10, 0))
        ttk.Button(frame, text="Parar", command=self.stop_worker).grid(row=2, column=3, pady=(10, 0))

        frame.columnconfigure(1, weight=1)

    def create_contact_controls(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Planilha de contatos", padding=12)
        frame.pack(fill=tk.X, pady=(12, 0))

        ttk.Label(frame, text="Arquivo").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(frame, textvariable=self.contacts_path).grid(row=0, column=1, sticky=tk.EW, padx=8)
        ttk.Button(frame, text="Escolher", command=self.choose_contacts_file).grid(row=0, column=2)

        ttk.Label(frame, text="Mensagem").grid(row=1, column=0, sticky=tk.W, pady=(8, 0))
        ttk.Entry(frame, textvariable=self.contacts_message).grid(
            row=1,
            column=1,
            sticky=tk.EW,
            padx=8,
            pady=(8, 0),
        )

        ttk.Label(frame, text="Limite").grid(row=1, column=2, sticky=tk.W, pady=(8, 0))
        ttk.Entry(frame, textvariable=self.contacts_limit, width=8).grid(row=1, column=3, pady=(8, 0))

        ttk.Button(frame, text="Testar", command=self.test_contacts).grid(row=2, column=1, sticky=tk.E, pady=(10, 0))
        ttk.Button(frame, text="Enviar", command=self.send_contacts).grid(row=2, column=2, sticky=tk.W, pady=(10, 0))

        frame.columnconfigure(1, weight=1)

    def create_log(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Saida", padding=8)
        frame.pack(fill=tk.BOTH, expand=True, pady=(12, 0))

        self.log_text = tk.Text(frame, wrap=tk.WORD, height=14)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def start_web_bot(self) -> None:
        if self.worker_is_running():
            messagebox.showwarning("Bot em execucao", "Pare a tarefa atual antes de iniciar outra.")
            return

        try:
            poll_interval_ms = self.read_poll_interval_ms()
        except ValueError as exc:
            messagebox.showwarning("Intervalo invalido", str(exc))
            return

        self.stop_event = threading.Event()
        options = WhatsAppWebOptions(
            session_dir=self.session_dir.get().strip() or DEFAULT_SESSION_DIR,
            poll_interval_ms=poll_interval_ms,
            print_only=self.print_only.get(),
            stop_event=self.stop_event,
            log_message=self.queue_log,
        )
        fixed_reply = self.fixed_reply.get().strip()

        def reply_to(incoming_message: str) -> str:
            return fixed_reply or build_reply(incoming_message)

        self.start_worker("WhatsApp Web", lambda: run_whatsapp_web_bot(reply_to, options))

    def read_poll_interval_ms(self) -> int:
        try:
            seconds = float(self.poll_interval.get().strip() or DEFAULT_POLL_INTERVAL)
        except ValueError as exc:
            raise ValueError("Informe um numero para o intervalo.") from exc

        if seconds <= 0:
            raise ValueError("O intervalo precisa ser maior que zero.")

        return int(seconds * 1000)

    def choose_contacts_file(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Escolher planilha",
            filetypes=[
                ("Planilhas", "*.csv *.xlsx *.xlsm"),
                ("CSV", "*.csv"),
                ("Excel", "*.xlsx *.xlsm"),
                ("Todos os arquivos", "*.*"),
            ],
        )

        if file_path:
            self.contacts_path.set(file_path)

    def test_contacts(self) -> None:
        self.start_contacts_task(print_only=True)

    def send_contacts(self) -> None:
        if not messagebox.askyesno("Confirmar envio", "Enviar mensagens para os contatos da planilha?"):
            return

        self.start_contacts_task(print_only=False)

    def start_contacts_task(self, print_only: bool) -> None:
        if self.worker_is_running():
            messagebox.showwarning("Bot em execucao", "Pare a tarefa atual antes de iniciar outra.")
            return

        try:
            settings = self.read_contact_settings(print_only)
        except ValueError as exc:
            messagebox.showwarning("Planilha", str(exc))
            return

        self.stop_event = threading.Event()
        task_name = "Teste de planilha" if print_only else "Envio de planilha"
        self.start_worker(task_name, lambda: self.run_contacts_task(settings))

    def read_contact_settings(self, print_only: bool) -> dict[str, object]:
        contacts_path = self.contacts_path.get().strip()
        if not contacts_path:
            raise ValueError("Escolha uma planilha de contatos.")

        try:
            limit = int(self.contacts_limit.get().strip() or "0")
        except ValueError as exc:
            raise ValueError("O limite precisa ser um numero inteiro.") from exc

        if limit < 0:
            raise ValueError("O limite nao pode ser negativo.")

        return {
            "contacts_path": contacts_path,
            "message_template": self.contacts_message.get().strip(),
            "limit": limit,
            "print_only": print_only,
        }

    def run_contacts_task(self, settings: dict[str, object]) -> None:
        contacts = self.load_contacts(str(settings["contacts_path"]))
        selected_contacts = self.limit_contacts(contacts, int(settings["limit"]))

        if not selected_contacts:
            self.queue_log("Nenhum contato encontrado na planilha.")
            return

        for contact in selected_contacts:
            if self.should_stop():
                self.queue_log("Tarefa de planilha interrompida.")
                return

            self.handle_contact(contact, str(settings["message_template"]), bool(settings["print_only"]))

    def load_contacts(self, contacts_path: str) -> list:
        try:
            return load_contact_rows(contacts_path)
        except ContactSheetError as exc:
            self.queue_log(f"Erro na planilha: {exc}")
            return []

    def limit_contacts(self, contacts: list, limit: int) -> list:
        if limit <= 0:
            return contacts

        return contacts[:limit]

    def handle_contact(self, contact, message_template: str, print_only: bool) -> None:
        try:
            phone_number = format_contact_phone(contact.phone_number, DEFAULT_COUNTRY_CODE)
            message = self.build_contact_message(contact, message_template)
        except ValueError as exc:
            self.queue_log(f"Linha {contact.row_number} ignorada: {exc}")
            return

        self.log_contact_message(contact, phone_number, message)
        if print_only:
            return

        send_whatsapp_message(phone_number, message, DEFAULT_WAIT_TIME, None, DEFAULT_CLOSE_TIME)
        wait_between_contacts(DEFAULT_CONTACT_DELAY)

    def build_contact_message(self, contact, message_template: str) -> str:
        template = message_template or contact.message

        if not template:
            raise ValueError("sem mensagem; preencha a mensagem na interface ou na coluna mensagem.")

        return render_contact_template(template, contact)

    def log_contact_message(self, contact, phone_number: str, message: str) -> None:
        contact_name = contact.name or "sem nome"
        self.queue_log(f"\nLinha {contact.row_number}: {contact_name} ({phone_number})")
        self.queue_log("Mensagem:")
        self.queue_log(message)

    def start_worker(self, task_name: str, target) -> None:
        self.queue_log(f"\n[{task_name} iniciado]\n")
        self.worker_thread = threading.Thread(
            target=self.run_worker,
            args=(task_name, target),
            daemon=True,
        )
        self.worker_thread.start()

    def run_worker(self, task_name: str, target) -> None:
        try:
            target()
        except Exception as exc:
            self.queue_log(f"\nErro: {exc}")
        finally:
            self.queue_log(f"\n[{task_name} encerrado]\n")

    def worker_is_running(self) -> bool:
        return self.worker_thread is not None and self.worker_thread.is_alive()

    def should_stop(self) -> bool:
        return bool(self.stop_event and self.stop_event.is_set())

    def stop_worker(self) -> None:
        if not self.worker_is_running():
            return

        self.queue_log("\n> solicitando parada...\n")
        if self.stop_event:
            self.stop_event.set()

    def flush_output(self) -> None:
        while not self.output_queue.empty():
            self.write_log(self.output_queue.get())

        self.after(100, self.flush_output)

    def queue_log(self, text: str) -> None:
        self.output_queue.put(f"{text}\n")

    def write_log(self, text: str) -> None:
        self.log_text.insert(tk.END, text)
        self.log_text.see(tk.END)

    def close_window(self) -> None:
        if self.worker_is_running():
            if not messagebox.askyesno("Sair", "O bot esta em execucao. Encerrar mesmo assim?"):
                return

            self.stop_worker()

        self.destroy()


def main() -> None:
    app = BotGui()
    app.mainloop()


if __name__ == "__main__":
    main()
