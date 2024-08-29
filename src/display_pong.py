import asyncio
import math
import random
import time
from typing import Literal, Optional

from src.helpers.control import control_server
from src.helpers.digits import DIGIT_PATTERNS
from src.helpers.draw import pattern_to_points
from src.helpers.fullscreen_message import fullscreen_message
from src.helpers.napta_colors import NaptaColor
from src.napta_matrix import RGBMatrix, matrix_script

BOARD_SIZE = 64
PADDLE_SIZE = 10
BALL_SPEED = 0.5
MAX_ANGLE = 70
FPS = 40

BORDER_TOP = 0
BORDER_BOTTOM = BOARD_SIZE
BORDER_LEFT = 4
BORDER_RIGHT = BOARD_SIZE - 4


def get_pos(y: int, input: Optional[bytes]) -> int:
    last_press = (input or b"")[-3:]
    if last_press == b"\x1b[A" and y > BORDER_TOP:
        return y - 1
    elif last_press == b"\x1b[B" and y < BORDER_BOTTOM - PADDLE_SIZE:
        return y + 1
    return y


def get_post_bounce_speed(yb: float, y_paddle: int, dx_sign: Literal[1, -1], speed: float) -> tuple[float, float]:
    dist_from_paddle_mid = yb - (y_paddle + PADDLE_SIZE / 2)
    new_angle = (dist_from_paddle_mid / PADDLE_SIZE) * MAX_ANGLE / 180 * math.pi
    dx = math.cos(new_angle) * speed * dx_sign
    dy = math.sin(new_angle) * speed
    return dx, dy


def _paddle_points(y: int, p: Literal[1, 2]) -> set[tuple[int, int]]:
    x = 1 if p == 1 else BOARD_SIZE - 3
    return {(xp, yp) for yp in range(y, y + PADDLE_SIZE) for xp in (x, x + 1)}


def _score_points(score: int, player: Literal[1, 2]) -> set[tuple[int, int]]:
    origin_x = (BOARD_SIZE * (3 if player == 2 else 1)) // 4 - 3 * len(str(score))
    return {
        point
        for i, digit in enumerate(int(x) for x in str(score))
        for point in pattern_to_points(DIGIT_PATTERNS[digit], origin_x=origin_x + (6 * i), origin_y=2)
    }


@matrix_script
async def display_pong(matrix: RGBMatrix) -> None:
    def draw_point(pix: tuple[int, int], color: tuple[int, int, int]) -> None:
        matrix.SetPixel(*pix, *color)

    y1 = y2 = (BOARD_SIZE - PADDLE_SIZE) // 2
    y1_points = y2_points = set[tuple[int, int]]()
    speed = BALL_SPEED

    score1 = score2 = -1
    score1_points = score2_points = set[tuple[int, int]]()

    def place_ball() -> tuple[float, float, float, float, tuple[int, int]]:
        nonlocal y1, y2, y1_points, y2_points, xb, yb, dx, dy, speed

        xb = yb = BOARD_SIZE / 2
        angle = (random.uniform(-MAX_ANGLE / 360, MAX_ANGLE / 360) + random.randrange(2)) * math.pi
        speed = BALL_SPEED
        dx = math.cos(angle) * speed
        dy = math.sin(angle) * speed
        pt = (int(round(xb)), int(round(yb)))
        return xb, yb, dx, dy, pt

    xb, yb, dx, dy, pt = place_ball()

    middle_line = {(pt[0], y) for y in range(BOARD_SIZE + 1) if 0 < y % 4 < 3}

    def draw_middle_line() -> None:
        for dot in middle_line:
            draw_point(dot, NaptaColor.CORN_FIELD)

    def update_paddles() -> None:
        nonlocal y1, y2, y1_points, y2_points

        new_y1_points, new_y2_points = _paddle_points(y1, 1), _paddle_points(y2, 2)

        for point in y1_points - new_y1_points:
            draw_point(point, NaptaColor.OFF)
        for point in new_y1_points - y1_points:
            draw_point(point, NaptaColor.BITTERSWEET)

        for point in y2_points - new_y2_points:
            draw_point(point, NaptaColor.OFF)
        for point in new_y2_points - y2_points:
            draw_point(point, NaptaColor.INDIGO)

        y1_points, y2_points = new_y1_points, new_y2_points

    def _off_color(point: tuple[int, int]) -> tuple[int, int, int]:
        if point in middle_line:
            return NaptaColor.CORN_FIELD
        if point in y1_points or point in score1_points:
            return NaptaColor.BITTERSWEET
        if point in y2_points or point in score2_points:
            return NaptaColor.INDIGO
        return NaptaColor.OFF

    def update_ball() -> None:
        nonlocal y1, y2, y1_points, y2_points, xb, yb, dx, dy, pt, speed

        new_xb = xb + dx
        new_yb = yb + dy
        new_pt = (int(round(new_xb)), int(round(new_yb)))

        if new_yb < BORDER_TOP:  # Bounce top
            new_yb = BORDER_TOP - (new_yb - BORDER_TOP)
            dy = -dy
        elif new_yb > BORDER_BOTTOM:  # Bounce bottom
            new_yb = BORDER_BOTTOM - (new_yb - BORDER_BOTTOM)
            dy = -dy

        if new_xb < BORDER_LEFT:
            if y1 <= new_yb <= y1 + PADDLE_SIZE:  # Bounce left
                new_xb = BORDER_LEFT - (new_xb - BORDER_LEFT)
                speed += 0.25
                dx, dy = get_post_bounce_speed(new_yb, y1, 1, speed)
            else:  # Point left
                goal(2)
                new_xb, new_yb, dx, dy, new_pt = place_ball()
        elif new_xb > BORDER_RIGHT:
            if y2 <= new_yb <= y2 + PADDLE_SIZE:  # Bounce right
                new_xb = BORDER_RIGHT - (new_xb - BORDER_RIGHT)
                speed += 0.25
                dx, dy = get_post_bounce_speed(new_yb, y2, -1, speed)
            else:  # Point right
                goal(1)
                new_xb, new_yb, dx, dy, new_pt = place_ball()

        if new_pt != pt:
            draw_point(pt, _off_color(pt))
            draw_point(new_pt, NaptaColor.GREEN)

        xb, yb, pt = new_xb, new_yb, new_pt

    def goal(player: Literal[1, 2]) -> None:
        nonlocal score1, score2, score1_points, score2_points

        if player == 1:
            score1 += 1
            new_points = _score_points(score1, 1)
            for point in score1_points - new_points:
                draw_point(point, NaptaColor.OFF)
            for point in new_points - score1_points:
                draw_point(point, NaptaColor.BITTERSWEET)
            score1_points = new_points
        else:
            score2 += 1
            new_points = _score_points(score2, 2)
            for point in score2_points - new_points:
                draw_point(point, NaptaColor.OFF)
            for point in new_points - score2_points:
                draw_point(point, NaptaColor.INDIGO)
            score2_points = new_points

    await fullscreen_message(matrix, ["Starting", "Pong game", "server..."])
    on_started = fullscreen_message(
        matrix, ["Connect to", "play Pong:", "./play.sh", "in the repo", "(Web client", "incoming)"]
    )

    client_names = ["P1", "P2"]
    async with control_server(client_names=client_names, on_started=on_started) as server:
        matrix.Clear()
        draw_middle_line()
        update_paddles()
        update_ball()
        goal(1)
        goal(2)
        timeout = 1 / FPS

        while True:
            t_start = time.time()
            try:
                t1, t2 = (asyncio.create_task(server.clients[p].read(32), name=p) for p in client_names)
                done, pending = await asyncio.wait([t1, t2], timeout=timeout)
                inputs = {task.get_name(): task.result() for task in done}
                for task in pending:
                    task.cancel()
                y1 = get_pos(y1, inputs.get("P1"))
                y2 = get_pos(y2, inputs.get("P2"))
            except asyncio.TimeoutError:
                pass

            update_paddles()
            update_ball()
            await asyncio.sleep(1 / FPS - (time.time() - t_start))


if __name__ == "__main__":
    asyncio.run(display_pong())
