import asyncio
import enum
import itertools
import time
from collections import deque
from pathlib import Path
from random import randrange

from PIL import Image, ImageDraw

from src.helpers.control import control_server
from src.helpers.napta_colors import NaptaColor
from src.napta_matrix import RGBMatrix, graphics, matrix_script

BOARD_SIZE = 64
INITIAL_SNAKE_LEN = 4
FPS = 20


class Dir(enum.Enum):
    UP = enum.auto()
    DOWN = enum.auto()
    RIGHT = enum.auto()
    LEFT = enum.auto()


def get_dir(current_dir: Dir, input: bytes) -> Dir:
    last_press = input[-3:]
    if last_press == b"\x1b[A" and current_dir in (Dir.LEFT, Dir.RIGHT):
        return Dir.UP
    elif last_press == b"\x1b[B" and current_dir in (Dir.LEFT, Dir.RIGHT):
        return Dir.DOWN
    elif last_press == b"\x1b[C" and current_dir in (Dir.UP, Dir.DOWN):
        return Dir.RIGHT
    elif last_press == b"\x1b[D" and current_dir in (Dir.UP, Dir.DOWN):
        return Dir.LEFT

    return current_dir


async def display_wait_for_message(matrix: RGBMatrix):
    offscreen_canvas = matrix.CreateFrameCanvas()

    font = graphics.Font()
    font_path = Path(__file__).parent.parent / "fonts" / "5x7.bdf"
    font.LoadFont(str(font_path.resolve()))

    for text, line in zip(
        ["Connect to", "play Snake:", "ssh 192.168", ".128.175", "-p 1030", "-l piku run", "naptaled co"],
        itertools.count(10, 8),
    ):
        graphics.DrawText(offscreen_canvas, font, 3, line, NaptaColor.GORSE, text)
    offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)


@matrix_script
async def display_snake(matrix: RGBMatrix) -> None:
    snake = deque(((20 + i) % BOARD_SIZE, 40) for i in range(INITIAL_SNAKE_LEN, 0, -1))  # Head to queue

    def get_next_apple() -> tuple[int, int]:
        while (maybe_apple := (randrange(BOARD_SIZE), randrange(BOARD_SIZE))) in snake:
            continue
        return maybe_apple

    apple = get_next_apple()
    eating_apples = set[tuple[int, int]]()
    dir = Dir.RIGHT

    image = Image.new("RGB", (BOARD_SIZE, BOARD_SIZE))
    draw = ImageDraw.Draw(image)
    draw.point(snake, NaptaColor.BITTERSWEET)
    draw.point(apple, NaptaColor.GREEN)

    def draw_point(pix: tuple[int, int], color: tuple[int, int, int]) -> None:
        matrix.SetPixel(*pix, *color)

    def update_game() -> None:
        nonlocal apple, dir

        if snake[-1] in eating_apples:
            eating_apples.remove(snake[-1])
        else:
            poped = snake.pop()
            draw_point(poped, (0, 0, 0))

        head_x, head_y = snake[0]
        if dir == Dir.UP:
            new_head = head_x, (head_y - 1) % BOARD_SIZE
        elif dir == Dir.DOWN:
            new_head = head_x, (head_y + 1) % BOARD_SIZE
        elif dir == Dir.RIGHT:
            new_head = (head_x + 1) % BOARD_SIZE, head_y
        else:
            new_head = (head_x - 1) % BOARD_SIZE, head_y

        if new_head == apple:
            eating_apples.add(apple)
            apple = get_next_apple()
            draw_point(apple, NaptaColor.GREEN)

        for eating_apple in eating_apples:
            draw_point(eating_apple, NaptaColor.GORSE)

        if new_head in snake:
            raise RuntimeError("U NOOB")

        draw_point(new_head, NaptaColor.BITTERSWEET)
        snake.appendleft(new_head)

    await display_wait_for_message(matrix)

    async with control_server(n_clients=1) as server:
        matrix.SetImage(image, 0, 0)

        while True:
            t_start = time.time()
            try:
                input = await asyncio.wait_for(server.clients[-1].read(1000), timeout=1 / FPS)
                dir = get_dir(dir, input)
            except TimeoutError:
                pass

            update_game()
            await asyncio.sleep(1 / FPS - (time.time() - t_start))


if __name__ == "__main__":
    asyncio.run(display_snake())
