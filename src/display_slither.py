import asyncio
import enum
import random
import time
from collections import deque
from random import choice, randrange

from PIL import Image

from src.helpers.control import control_server
from src.helpers.fullscreen_message import fullscreen_message
from src.helpers.napta_colors import NaptaColor
from src.napta_matrix import RGBMatrix, matrix_script

BOARD_SIZE = 64
INITIAL_SNAKE_LEN = 4
SPAWN_SAFE_ZONE = 5
APPLES_COUNT = 20
DEAD_TO_APPLE_RATE = 0.3
FPS = 20

BORDER_TOP = 0
BORDER_BOTTOM = BOARD_SIZE - 1
BORDER_LEFT = 0
BORDER_RIGHT = BOARD_SIZE - 1


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


SNAKES = {
    "P1": NaptaColor.GREEN,
    "P2": NaptaColor.BLUE,
    "P3": NaptaColor.BITTERSWEET,
    "P4": NaptaColor.GORSE,
    "P5": NaptaColor.INDIGO,
    "P6": NaptaColor.CORN_FIELD,
}


@matrix_script
async def display_slither(matrix: RGBMatrix) -> None:
    snakes = dict[str, deque[tuple[int, int]]]()
    apples = set[tuple[int, int]]()
    eating_apples = set[tuple[int, int]]()

    dirs = dict[str, Dir]()

    image = Image.new("RGB", (BOARD_SIZE, BOARD_SIZE))

    def draw_point(pix: tuple[int, int], color: tuple[int, int, int]) -> None:
        matrix.SetPixel(*pix, *color)

    def spawn_new_apple():
        def _maybe_apple():
            return (randrange(BOARD_SIZE), randrange(BOARD_SIZE))

        unsuitable_points = set().union(*snakes.values(), apples)
        maybe_apple = _maybe_apple()
        while maybe_apple in unsuitable_points:
            maybe_apple = _maybe_apple()

        apples.add(maybe_apple)
        draw_point(maybe_apple, choice(list(SNAKES.values())))

    def spawn_snake(name: str) -> None:
        def _maybe_new_snake():
            x = randrange(BORDER_LEFT, BORDER_RIGHT - (INITIAL_SNAKE_LEN + SPAWN_SAFE_ZONE))
            y = randrange(BORDER_TOP, BORDER_BOTTOM)
            return {(x + i, y) for i in range(INITIAL_SNAKE_LEN + SPAWN_SAFE_ZONE)}

        unsuitable_points = set().union(*snakes.values())
        maybe_new_snake = _maybe_new_snake()
        while maybe_new_snake & unsuitable_points:
            maybe_new_snake = _maybe_new_snake()

        new_snake_points = sorted(maybe_new_snake, key=lambda pt: -pt[0])  # Head to queue
        snakes[name] = deque(new_snake_points[:-SPAWN_SAFE_ZONE])
        dirs[name] = Dir.RIGHT
        for point in snakes[name]:
            draw_point(point, SNAKES[name])

        apples.difference_update(maybe_new_snake)

    def update_game() -> None:
        # Pop tails
        for snake in snakes.values():
            if snake[-1] in eating_apples:
                eating_apples.remove(snake[-1])
            else:
                poped = snake.pop()
                draw_point(poped, NaptaColor.OFF)

        dead_snakes = set[str]()

        # Compute new heads
        for name, snake in snakes.items():
            head_x, head_y = snake[0]
            dir = dirs[name]
            if dir == Dir.UP:
                if head_y == BORDER_TOP:
                    dead_snakes.add(name)
                    continue
                new_head = head_x, (head_y - 1)
            elif dir == Dir.DOWN:
                if head_y == BORDER_BOTTOM:
                    dead_snakes.add(name)
                    continue
                new_head = head_x, (head_y + 1)
            elif dir == Dir.RIGHT:
                if head_x == BORDER_RIGHT:
                    dead_snakes.add(name)
                    continue
                new_head = (head_x + 1), head_y
            else:
                if head_x == BORDER_LEFT:
                    dead_snakes.add(name)
                    continue
                new_head = (head_x - 1), head_y

            if new_head in apples:
                apples.remove(new_head)
                eating_apples.add(new_head)

            if any(new_head in other_snake for other_snake in snakes.values()):
                dead_snakes.add(name)
                continue

            draw_point(new_head, SNAKES[name])
            snake.appendleft(new_head)

        # Remove dead snakes
        for dead_snake in dead_snakes:
            for point in snakes[dead_snake]:
                if random.random() < DEAD_TO_APPLE_RATE:
                    apples.add(point)
                    draw_point(point, choice(list(SNAKES.values())))
                else:
                    draw_point(point, NaptaColor.OFF)

            del snakes[dead_snake]
            del dirs[dead_snake]


    await fullscreen_message(matrix, ["Starting", "Slither game", "server..."])
    on_started = fullscreen_message(
        matrix, ["Connect to", "play Slither:", "./play.sh", "in the repo", "(Web client", "incoming)"]
    )

    async with control_server(client_names=SNAKES.keys(), min_clients=1, on_started=on_started) as server:
        matrix.SetImage(image, 0, 0)
        frame_duration = 1 / FPS

        while True:
            t_start = time.time()

            done, pending = await asyncio.wait(
                (asyncio.create_task(client.read(32), name=name) for name, client in server.clients.items()),
                timeout=frame_duration,
            )
            for task in done:
                name = task.get_name()
                if name not in snakes:
                    spawn_snake(name)
                dirs[name] = get_dir(dirs[name], task.result())
            for task in pending:
                task.cancel()

            update_game()

            for _ in range(APPLES_COUNT - len(apples)):
                spawn_new_apple()

            await asyncio.sleep(frame_duration - (time.time() - t_start))


if __name__ == "__main__":
    asyncio.run(display_slither())
