# Rules from https://rosettacode.org/wiki/2048

import enum
import random
from typing import NamedTuple, Optional, Self, Union


class Dir(enum.Enum):
    UP = enum.auto()
    DOWN = enum.auto()
    RIGHT = enum.auto()
    LEFT = enum.auto()


class Board:
    def __init__(self, data: Optional[list[list[int]]] = None) -> None:
        self._data = data or [
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]

    @classmethod
    def move_coords_to_row_col(cls, dir: Dir, non_moving_index: int, moving_to_index: int, /) -> tuple[int, int]:
        if dir is Dir.UP:
            return (moving_to_index, non_moving_index)
        if dir is Dir.DOWN:
            return (3 - moving_to_index, non_moving_index)
        if dir is Dir.LEFT:
            return (non_moving_index, moving_to_index)
        if dir is Dir.RIGHT:
            return (non_moving_index, 3 - moving_to_index)

    def __getitem__(self, tup: Union[tuple[int, int], tuple[Dir, int, int]], /) -> int:
        row, col = tup if len(tup) == 2 else self.move_coords_to_row_col(*tup)
        return self._data[row][col]

    def __setitem__(self, tup: Union[tuple[int, int], tuple[Dir, int, int]], value: int, /) -> None:
        row, col = tup if len(tup) == 2 else self.move_coords_to_row_col(*tup)
        self._data[row][col] = value

    def get_empty_slots(self) -> list[tuple[int, int]]:
        return [(y, x) for (y, row) in enumerate(self._data) for (x, val) in enumerate(row) if val == 0]

    def copy(self) -> Self:
        return type(self)(self._data)


class Move(NamedTuple):
    origin_yx: tuple[int, int]
    origin_tile: int
    dest_xy: tuple[int, int]
    dest_tile: int
    dist: int
    is_fusion: bool


def _spawn(board: Board) -> tuple[int, int, int]:
    empty_slots = board.get_empty_slots()
    assert empty_slots  # If _spawn was called, we just moved, so at least one case should be empty

    new_pos = random.choice(empty_slots)
    new_tile = 4 if random.random() <= 0.1 else 2
    board[new_pos] = new_tile

    if len(empty_slots) == 1:
        # We just filled the last case: check the game is not struck!
        if not any(compute_move(dir, board.copy()) for dir in Dir):
            raise ValueError("STEP BRO IM STUCK")

    return (*new_pos, new_tile)


def _shift(*values: int) -> tuple[int, ...]:
    if len(values) <= 1:
        return values

    first, second, *rest = values

    if first == 0:
        # Empty cell: shift all values
        return (*_shift(second, *rest), 0)

    if second == 0:
        # Empty cell next: shift following values and try to combine again
        return (*_shift(first, *rest), 0)

    if first == second:
        # Same value as next cell: combine them, process the rest
        return (first + second, *_shift(*rest), 0)

    # Else: cannot move
    return (first, *_shift(second, *rest))


def _find_moves(
    after: tuple[int, ...], before: tuple[int, ...], _offset_after: int = 0, _offset_before: int = 0
) -> list[tuple[int, int, bool]]:
    if not after:
        return []

    value = after[0]

    if value == 0:
        # End of possible moves
        assert all(val == 0 for val in before), "before not totally moved!!"
        return []

    _moves = list[tuple[int, int, bool]]()
    for ix, before_val in enumerate(before):
        if before_val == value:
            # Number has shifted from ix
            _moves.append((_offset_before + ix, _offset_after, False))
            break

        elif before_val == value // 2:
            # Number is a combination from ix and another number
            is_second_half = bool(_moves)
            _moves.append((_offset_before + ix, _offset_after, is_second_half))
            if is_second_half:
                break

        elif before_val != 0:
            raise ValueError("???")
    else:
        # Not broken
        raise ValueError("???")

    return [
        *((x, y, is_fusion) for (x, y, is_fusion) in _moves if x != y),  # Keep only real moves
        *_find_moves(after[1:], before[ix + 1 :], _offset_after + 1, _offset_before + ix + 1),  # Find next moves
    ]


def new_game() -> Board:
    board = Board()
    _spawn(board)
    return board


def compute_move(dir: Dir, board: Board) -> Optional[tuple[list[Move], tuple[int, int, int]]]:
    board_moves: list[Move] = []

    for nmi in range(4):  # non-moving index (column if moving up/down, row if moving left/right)
        values = tuple(board[dir, nmi, ix] for ix in range(4))
        shifted_values = _shift(*values)

        if shifted_values != values:
            row_moves = _find_moves(shifted_values, values)
            assert row_moves, "shifted but no moves??"
            board_moves.extend(
                Move(
                    origin_yx=Board.move_coords_to_row_col(dir, nmi, orig),
                    origin_tile=values[orig],
                    dest_xy=Board.move_coords_to_row_col(dir, nmi, dest),
                    dest_tile=shifted_values[dest],
                    dist=orig - dest,
                    is_fusion=is_fusion,
                )
                for orig, dest, is_fusion in row_moves
            )

            for ix, value in enumerate(shifted_values):
                board[dir, nmi, ix] = value

    if board_moves:
        new_tile = _spawn(board)
        return (board_moves, new_tile)
