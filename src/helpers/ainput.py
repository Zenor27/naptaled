# Implementation derived from https://stackoverflow.com/a/32382950

import os
import sys
import termios
from contextlib import contextmanager


@contextmanager
def capture_terminal():
    fd = sys.stdin.fileno()
    free_term = termios.tcgetattr(fd)

    captured_term = termios.tcgetattr(fd)
    captured_term[3] = captured_term[3] & ~termios.ICANON & ~termios.ECHO
    captured_term[6][termios.VMIN] = 0
    captured_term[6][termios.VTIME] = 0

    _captured = False

    def _get_input() -> bytes:
        if not _captured:
            raise RuntimeError("capture_terminal result cannot be used outside of context manager!")

        ret = b""
        while ch := os.read(fd, 1):
            ret += ch
        return ret

    termios.tcsetattr(fd, termios.TCSAFLUSH, captured_term)
    try:
        _captured = True
        yield _get_input
    finally:
        termios.tcsetattr(fd, termios.TCSAFLUSH, free_term)
        _captured = False
