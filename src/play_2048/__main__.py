# Play 2048 in the console (mostly for debugging)


import time
from typing import Optional

from src.helpers import ainput
from src.play_2048.algorithm import Board, Dir, compute_move, new_game


def _input_to_dir(input_: bytes) -> Optional[Dir]:
    last_press = input_[-3:]
    if last_press == b"\x1b[A":
        return Dir.UP
    elif last_press == b"\x1b[B":
        return Dir.DOWN
    elif last_press == b"\x1b[C":
        return Dir.RIGHT
    elif last_press == b"\x1b[D":
        return Dir.LEFT
    return None


def _print_board(board: Board) -> None:
    print("\n\n" + "\n".join(" ".join(str(val) for val in row) for row in board._data))


if __name__ == "__main__":
    board = new_game()
    _print_board(board)

    with ainput.capture_terminal() as get_input:
        while True:
            if dir := _input_to_dir(get_input()):
                moves = compute_move(dir, board)
                if moves:
                    _print_board(board)

            time.sleep(0.01)
