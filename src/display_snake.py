import asyncio
import enum
import sys
from collections import deque
from random import randrange

from PIL import Image, ImageDraw

from src.helpers.napta_colors import NaptaColor
from src.napta_matrix import RGBMatrix, matrix_script

BOARD_SIZE = 64
INITIAL_SNAKE_LEN = 4


class Dir(enum.Enum):
    UP = enum.auto()
    DOWN = enum.auto()
    RIGHT = enum.auto()
    LEFT = enum.auto()


async def ainput() -> bytes:
    """Cf. https://stackoverflow.com/a/76183977"""
    return await asyncio.to_thread(sys.stdin.buffer.readline)


async def get_dir(current_dir: Dir) -> Dir:
    while True:
        inp = await ainput()
        last_press = inp[-4:-1]
        if last_press == b"\x1b[A" and current_dir in (Dir.LEFT, Dir.RIGHT):
            return Dir.UP
        elif last_press == b"\x1b[B" and current_dir in (Dir.LEFT, Dir.RIGHT):
            return Dir.DOWN
        elif last_press == b"\x1b[C" and current_dir in (Dir.UP, Dir.DOWN):
            return Dir.RIGHT
        elif last_press == b"\x1b[D" and current_dir in (Dir.UP, Dir.DOWN):
            return Dir.LEFT


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
    matrix.SetImage(image, 0, 0)

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

    print("=========================================================================")
    print("Prepare your next direction with arrow keys, then press Enter to apply it")
    print("=========================================================================")

    get_dir_task = asyncio.create_task(get_dir(dir))

    while True:
        await asyncio.wait([get_dir_task], timeout=0.05)
        if get_dir_task.done():
            dir = get_dir_task.result()
            get_dir_task = asyncio.create_task(get_dir(dir))

        update_game()


if __name__ == "__main__":
    asyncio.run(display_snake())
