"""Terminal chat interface for the MeshBot simulator."""

from __future__ import annotations

import curses
import logging
import queue
from collections import deque
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime
from threading import Event, Thread

from meshbot.application.bot import MeshBot
from meshbot.application.runtime import RuntimeWorker
from meshbot.domain.messages import OutgoingMessage
from meshbot.infrastructure.simulator import SimulatorTransport


@dataclass(frozen=True, slots=True)
class ChatEntry:
    """A single line in the simulator chat history."""

    timestamp: str
    sender: str
    text: str
    kind: str


class SimulatorLogHandler(logging.Handler):
    """Forward application logs to the simulator chat."""

    def __init__(self, on_message: Callable[[str], None]) -> None:
        super().__init__()
        self._on_message = on_message

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._on_message(record.getMessage())
        except Exception:
            self.handleError(record)


def format_recipient(recipient_id: str) -> str:
    """Format a transport recipient for the chat display."""
    if recipient_id == "^all":
        return "TODOS"
    return recipient_id


def parse_input(line: str) -> tuple[str, str] | None:
    """Parse simulator input in the form '<node_id> <message>'."""
    stripped = line.strip()
    if not stripped:
        return None

    try:
        node_id, text = stripped.split(maxsplit=1)
    except ValueError:
        return None

    return node_id, text


class SimulatorChatUI:
    """Interactive terminal UI for the local simulator."""

    _MAX_HISTORY = 1000
    _POLL_DELAY_MS = 100

    def __init__(
        self,
        transport: SimulatorTransport,
        bot: MeshBot,
        workers: tuple[RuntimeWorker, ...] = (),
    ) -> None:
        self._transport = transport
        self._bot = bot
        self._workers = workers
        self._stop_event = Event()
        self._threads: list[Thread] = []
        self._message_queue: queue.Queue[None] = queue.Queue()
        self._events: queue.Queue[ChatEntry] = queue.Queue()
        self._history: deque[ChatEntry] = deque(maxlen=self._MAX_HISTORY)
        self._input = ""
        self._cursor = 0
        self._running = True

    def run(self) -> None:
        """Run the interactive terminal interface."""
        try:
            curses.wrapper(self._run)
        finally:
            self._stop_workers()

    def _run(self, screen: curses.window) -> None:
        self._setup_colors()
        screen.keypad(True)
        screen.timeout(self._POLL_DELAY_MS)

        self._add_entry("SYSTEM", "Simulator iniciado.", "system")
        self._add_entry(
            "SYSTEM",
            "Digite <node_id> <mensagem>  •  'exit' para sair",
            "system",
        )

        self._start_workers()
        self._start_message_processor()

        while self._running:
            self._drain_events()
            self._draw(screen)

            try:
                key = screen.get_wch()
            except curses.error:
                continue

            self._handle_key(key)

    def _start_message_processor(self) -> None:
        thread = Thread(
            target=self._process_messages,
            name="MeshBotSimulatorMessageProcessor",
            daemon=True,
        )
        thread.start()
        self._threads.append(thread)

    def _process_messages(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._message_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if self._stop_event.is_set():
                return

            try:
                self._bot.process_next_message()
            except Exception as exc:
                self.add_system_message(f"Falha ao processar mensagem: {exc}", "error")

    def _start_workers(self) -> None:
        for index, worker in enumerate(self._workers, start=1):
            thread = Thread(
                target=worker.run,
                args=(self._stop_event,),
                name=f"MeshBotBackgroundWorker-{index}",
                daemon=True,
            )
            thread.start()
            self._threads.append(thread)

    def _stop_workers(self) -> None:
        self._stop_event.set()
        self._message_queue.put(None)
        for thread in self._threads:
            thread.join()

    def _handle_key(self, key: str | int) -> None:
        if key in ("\n", "\r", curses.KEY_ENTER):
            self._submit_input()
            return

        if key in ("\x03",):
            self._running = False
            return

        if key in ("\x7f", "\b", curses.KEY_BACKSPACE):
            if self._cursor > 0:
                self._input = (
                    self._input[: self._cursor - 1] + self._input[self._cursor :]
                )
                self._cursor -= 1
            return

        if key == curses.KEY_LEFT:
            self._cursor = max(0, self._cursor - 1)
            return

        if key == curses.KEY_RIGHT:
            self._cursor = min(len(self._input), self._cursor + 1)
            return

        if key == curses.KEY_HOME:
            self._cursor = 0
            return

        if key == curses.KEY_END:
            self._cursor = len(self._input)
            return

        if isinstance(key, str) and key.isprintable():
            self._input = self._input[: self._cursor] + key + self._input[self._cursor :]
            self._cursor += len(key)

    def _submit_input(self) -> None:
        line = self._input.strip()
        self._input = ""
        self._cursor = 0

        if not line:
            return

        if line.lower() == "exit":
            self._running = False
            return

        parsed = parse_input(line)
        if parsed is None:
            self._add_entry(
                "SYSTEM",
                "Formato inválido. Use: <node_id> <mensagem>",
                "error",
            )
            return

        node_id, text = parsed
        self._add_entry(node_id, text, "incoming")
        self._transport.inject_message(node_id, text)
        self._message_queue.put(None)

    def add_outgoing_message(self, message: OutgoingMessage) -> None:
        """Queue a transport message for display in the UI thread."""
        self._events.put(
            ChatEntry(
                timestamp=self._timestamp(),
                sender=f"MeshBot → {format_recipient(message.recipient_id)}",
                text=message.text,
                kind="outgoing",
            )
        )

    def add_system_message(self, text: str, kind: str = "system") -> None:
        """Queue a system message for display in the UI thread."""
        self._events.put(
            ChatEntry(
                timestamp=self._timestamp(),
                sender="SYSTEM",
                text=text,
                kind=kind,
            )
        )

    def _drain_events(self) -> None:
        while True:
            try:
                entry = self._events.get_nowait()
            except queue.Empty:
                return
            self._history.append(entry)

    def _add_entry(self, sender: str, text: str, kind: str) -> None:
        self._history.append(
            ChatEntry(
                timestamp=self._timestamp(),
                sender=sender,
                text=text,
                kind=kind,
            )
        )

    @staticmethod
    def _timestamp() -> str:
        return datetime.now().strftime("%H:%M:%S")

    @staticmethod
    def _setup_colors() -> None:
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)
        curses.init_pair(4, curses.COLOR_RED, -1)
        curses.init_pair(5, curses.COLOR_WHITE, -1)
        curses.init_pair(6, curses.COLOR_MAGENTA, -1)

    def _draw(self, screen: curses.window) -> None:
        screen.erase()
        height, width = screen.getmaxyx()
        if height < 7 or width < 50:
            self._draw_too_small(screen, height, width)
            screen.refresh()
            return

        self._draw_header(screen, width)
        self._draw_history(screen, height - 4, width)
        self._draw_input(screen, height - 2, width)
        screen.refresh()

    def _draw_too_small(self, screen: curses.window, height: int, width: int) -> None:
        message = "Terminal muito pequeno. Aumente a janela para continuar."
        y = max(0, height // 2)
        x = max(0, (width - len(message)) // 2)
        self._safe_addstr(screen, y, x, message, curses.color_pair(4) | curses.A_BOLD)

    def _draw_header(self, screen: curses.window, width: int) -> None:
        title = " MeshBot Simulator "
        status = "● CONECTADO "
        line = "─" * width
        self._safe_addstr(screen, 0, 0, title, curses.color_pair(1) | curses.A_BOLD)
        status_x = max(0, width - len(status))
        self._safe_addstr(screen, 0, status_x, status, curses.color_pair(2) | curses.A_BOLD)
        self._safe_addstr(screen, 1, 0, line, curses.color_pair(6))

    def _draw_history(self, screen: curses.window, bottom: int, width: int) -> None:
        usable = max(1, bottom - 2)
        lines: list[tuple[str, int]] = []

        for entry in self._history:
            prefix = f"{entry.timestamp}  {entry.sender:<12} "
            color = self._color_for(entry.kind)
            available = max(1, width - len(prefix))
            chunks = [
                entry.text[index : index + available]
                for index in range(0, len(entry.text), available)
            ] or [""]
            lines.extend(
                [
                    (
                        (prefix if index == 0 else " " * len(prefix)) + chunk,
                        color,
                    )
                    for index, chunk in enumerate(chunks)
                ]
            )

        visible = lines[-usable:]
        for y, item in enumerate(visible, start=2):
            text, color = item
            self._safe_addstr(screen, y, 0, text, color)

    @staticmethod
    def _color_for(kind: str) -> int:
        return {
            "incoming": curses.color_pair(5),
            "outgoing": curses.color_pair(2),
            "system": curses.color_pair(3),
            "error": curses.color_pair(4) | curses.A_BOLD,
        }.get(kind, curses.color_pair(5))

    def _draw_input(self, screen: curses.window, y: int, width: int) -> None:
        self._safe_addstr(screen, y, 0, "─" * width, curses.color_pair(6))
        prompt = "Para: > "
        available = max(1, width - len(prompt))
        start = max(0, self._cursor - available + 1)
        visible = self._input[start : start + available]
        cursor_x = len(prompt) + self._cursor - start

        self._safe_addstr(screen, y + 1, 0, prompt, curses.color_pair(1) | curses.A_BOLD)
        self._safe_addstr(screen, y + 1, len(prompt), visible, curses.color_pair(5))
        screen.move(y + 1, min(width - 1, cursor_x))

    @staticmethod
    def _safe_addstr(
        screen: curses.window,
        y: int,
        x: int,
        text: str,
        attributes: int = 0,
    ) -> None:
        height, width = screen.getmaxyx()
        if y < 0 or y >= height or x >= width:
            return
        with suppress(curses.error):
            screen.addnstr(y, max(0, x), text, max(0, width - max(0, x) - 1), attributes)


def run_simulator_chat(
    transport: SimulatorTransport,
    bot: MeshBot,
    workers: tuple[RuntimeWorker, ...] = (),
) -> None:
    """Run the simulator with the interactive chat UI."""
    ui = SimulatorChatUI(transport, bot, workers=workers)
    log_handler = SimulatorLogHandler(ui.add_system_message)
    root_logger = logging.getLogger()
    previous_handlers = root_logger.handlers[:]
    root_logger.handlers.clear()
    root_logger.addHandler(log_handler)

    try:
        transport.set_observer(ui.add_outgoing_message)
        ui.run()
    finally:
        root_logger.removeHandler(log_handler)
        for handler in previous_handlers:
            root_logger.addHandler(handler)
