"""Transferable Windows console input, exercised without a native console."""

import asyncio
from collections import deque

import pytest

from loushang.tui.terminal_backends import native_terminal_input_backend
from loushang.tui.terminal_backends.windows import WindowsConsoleInput


class Console:
    def __init__(self, chars=()):
        self.chars = deque(chars)

    def kbhit(self):
        return bool(self.chars)

    def getwch(self):
        assert self.chars, "getwch must never wait for a missing native unit"
        return self.chars.popleft()


def test_backend_selection_shares_posix_reader_for_linux_and_macos():
    assert native_terminal_input_backend("linux") is native_terminal_input_backend(
        "darwin"
    )
    assert isinstance(native_terminal_input_backend("win32"), WindowsConsoleInput)


@pytest.mark.parametrize(
    "head,tail,expected",
    [
        (["\ud83d"], ["\udc4b"], "👋"),
        (["\x00"], ["H"], "\x1b[A"),
        (["\xe0"], ["/"], "\x1bv"),
        (["\x1b", "[", "2"], list("00~draft\x1b[201~"), "\x1b[200~draft\x1b[201~"),
    ],
)
def test_partial_native_input_survives_cancel_and_new_loop(head, tail, expected):
    console = Console(head)
    reader = WindowsConsoleInput(module_loader=lambda: console).open_reader(None)
    assert not reader.at_input_boundary()

    async def pause():
        task = asyncio.create_task(reader.read_chunk())
        await asyncio.sleep(0)
        assert not console.chars and not task.done()
        with pytest.raises(RuntimeError, match="already active"):
            await reader.read_chunk()
        with pytest.raises(RuntimeError, match="read is active"):
            reader.at_input_boundary()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(pause())
    assert not reader.at_input_boundary()
    console.chars.extend(tail)
    assert asyncio.run(reader.read_chunk()) == expected
    assert reader.at_input_boundary()


@pytest.mark.parametrize(
    "chars,expected",
    [
        (list("draft\r"), "draft\r"),
        (["\ud83d", "x"], "\ufffdx"),
        (["\udc4b"], "\ufffd"),
        (["\ud83d", "\ud83d", "\udc4b"], "\ufffd👋"),
        (["\x1b", "[", "I"], "\x1b[I"),
        (["\x03"], "\x03"),
    ],
)
def test_complete_input_and_empty_boundary(chars, expected):
    console = Console(chars)
    reader = WindowsConsoleInput(module_loader=lambda: console).open_reader(None)
    assert not reader.at_input_boundary()
    assert list(console.chars) == chars, "boundary probe must not consume input"
    assert asyncio.run(reader.read_chunk()) == expected
    assert reader.at_input_boundary()


def test_plain_alt_v_recovery_is_preserved(monkeypatch):
    monkeypatch.setattr(
        "loushang.tui.terminal_backends.windows._windows_pending_alt_modifier",
        lambda: True,
    )
    reader = WindowsConsoleInput(module_loader=lambda: Console(["v"])).open_reader(None)
    assert asyncio.run(reader.read_chunk()) == "\x1bv"


def test_idle_read_cancels_without_leaving_a_background_reader():
    reader = WindowsConsoleInput(module_loader=Console).open_reader(None)

    async def scenario():
        task = asyncio.create_task(reader.read_chunk())
        await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(scenario())
    assert reader.at_input_boundary()
