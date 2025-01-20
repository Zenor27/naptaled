import asyncio
from itertools import zip_longest
from typing import Callable, Iterator, Optional

from PIL import Image, ImageDraw

from src.helpers.control import control_server
from src.helpers.draw import draw_pattern, pattern_to_color_by_point
from src.helpers.fullscreen_message import fullscreen_message
from src.helpers.napta_colors import NaptaColor
from src.napta_matrix import RGBMatrix, matrix_script
from src.play_2048.algorithm import Board, Dir, Move, compute_move, new_game
from src.play_2048.tiles import TILE_PATTERNS

BOARD_SIZE = 64
TILE_START = [1, 17, 33, 49]


def get_dir(input: bytes) -> Optional[Dir]:
    last_press = input[-3:]
    if last_press == b"\x1b[A":
        return Dir.UP
    elif last_press == b"\x1b[B":
        return Dir.DOWN
    elif last_press == b"\x1b[C":
        return Dir.RIGHT
    elif last_press == b"\x1b[D":
        return Dir.LEFT

    return None


def draw_board(draw: ImageDraw.ImageDraw, board: Board) -> None:
    for row in range(4):
        for col in range(4):
            pattern = TILE_PATTERNS[board[row, col]]
            draw_pattern(
                draw,
                pattern.pattern,
                pattern.color_map,
                origin_x=TILE_START[col],
                origin_y=TILE_START[row],
            )


def _shift(
    color_by_point: dict[tuple[int, int], tuple[int, int, int]], dir: Dir
) -> dict[tuple[int, int], tuple[int, int, int]]:
    if dir is Dir.UP:
        return {(x, y - 1): color for (x, y), color in color_by_point.items()}
    if dir is Dir.DOWN:
        return {(x, y + 1): color for (x, y), color in color_by_point.items()}
    if dir is Dir.LEFT:
        return {(x - 1, y): color for (x, y), color in color_by_point.items()}
    if dir is Dir.RIGHT:
        return {(x + 1, y): color for (x, y), color in color_by_point.items()}


empty_pattern = TILE_PATTERNS[0]
empty_grid = {
    pt: color
    for x in TILE_START
    for y in TILE_START
    for pt, color in pattern_to_color_by_point(
        empty_pattern.pattern, empty_pattern.color_map, origin_x=x, origin_y=y
    ).items()
    if color != NaptaColor.OFF
}


def draw_move(
    dir: Dir, move: Move, draw_point: Callable[[tuple[int, int], tuple[int, int, int]], None]
) -> Iterator[None]:
    y, x = move.origin_yx
    pattern = TILE_PATTERNS[move.origin_tile]
    cbp = pattern_to_color_by_point(pattern.pattern, pattern.color_map, origin_x=TILE_START[x], origin_y=TILE_START[y])

    if move.is_fusion:  # Move + transform tile
        y, x = move.dest_xy
        dest_pattern = TILE_PATTERNS[move.dest_tile]
        dest_cbp = pattern_to_color_by_point(
            dest_pattern.pattern, dest_pattern.color_map, origin_x=TILE_START[x], origin_y=TILE_START[y]
        )
    else:
        dest_cbp = {}

    for _step in range(move.dist * 16):
        new_cbp = _shift(cbp, dir)
        # print(cbp, new_cbp)
        for pt, color in new_cbp.items():  # Points to (re)-draw
            if (dest_color := dest_cbp.get(pt)) and dest_color != color:
                draw_point(pt, dest_color)
            elif cbp.get(pt) != color:
                draw_point(pt, color)

        for pt in cbp.keys() - new_cbp.keys():  # Points to reset to empty tile
            draw_point(pt, empty_grid.get(pt, NaptaColor.OFF))

        cbp = new_cbp
        yield


def draw_new_tile(
    new_tile: tuple[int, int, int], draw_point: Callable[[tuple[int, int], tuple[int, int, int]], None]
) -> None:
    y, x, tile = new_tile
    pattern = TILE_PATTERNS[tile]
    for pt, color in pattern_to_color_by_point(
        pattern.pattern, pattern.color_map, origin_x=TILE_START[x], origin_y=TILE_START[y]
    ).items():
        draw_point(pt, color)


@matrix_script
async def display_2048(matrix: RGBMatrix) -> None:
    canvas = matrix.CreateFrameCanvas()

    board = new_game()

    image = Image.new("RGB", (BOARD_SIZE, BOARD_SIZE))
    draw_board(ImageDraw.Draw(image), board)
    canvas.SetImage(image, 0, 0)

    def draw_point(pix: tuple[int, int], color: tuple[int, int, int]) -> None:
        canvas.SetPixel(*pix, *color)

    def flush() -> None:
        matrix.SwapOnVSync(canvas)

    await fullscreen_message(matrix, ["Starting", "2048 game", "server..."])
    on_started = fullscreen_message(
        matrix, ["Connect to", "play 2048:", "./play.sh", "in the repo", "(Web client", "incoming)"]
    )

    async with control_server(client_names=["P"], on_started=on_started) as server:
        flush()

        while True:
            input = await asyncio.wait_for(server.clients["P"].read(32), timeout=None)
            dir = get_dir(input)
            if not dir:
                continue

            updates = compute_move(dir, board)
            if not updates:
                continue

            moves, new_tile = updates
            for _ in zip_longest(*(draw_move(dir, move, draw_point) for move in moves)):
                flush()

            draw_new_tile(new_tile, draw_point)
            flush()


if __name__ == "__main__":
    asyncio.run(display_2048())
