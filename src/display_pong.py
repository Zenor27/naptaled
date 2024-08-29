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
MAX_ANGLE = 70
FPS = 40

BORDER_TOP = 4
BORDER_BOTTOM = BOARD_SIZE - 4
BORDER_LEFT = 4
BORDER_RIGHT = BOARD_SIZE - 4


def get_y_pos(y: int, input: Optional[bytes]) -> int:
    last_press = (input or b"")[-3:]
    if last_press == b"\x1b[A" and y > BORDER_TOP:
        return y - 1
    elif last_press == b"\x1b[B" and y < BORDER_BOTTOM - PADDLE_SIZE:
        return y + 1
    return y


def get_x_pos(x: int, input: Optional[bytes]) -> int:
    last_press = (input or b"")[-3:]
    if last_press == b"\x1b[D" and x > BORDER_LEFT:
        return x - 1
    elif last_press == b"\x1b[C" and x < BORDER_RIGHT - PADDLE_SIZE:
        return x + 1
    return x


# Adjust coeffs: https://www.desmos.com/calculator/t6ewhvgb9w
A = 0.5
B = 1.5
C = 0.75
D = 0.5


def get_ball_speed(n_bounces: int) -> float:
    return A * math.log(B * n_bounces + D) + C


def get_post_y_bounce_speed(yb: float, y_paddle: int, dx_sign: Literal[1, -1], n_bounces: int) -> tuple[float, float]:
    dist_from_paddle_mid = yb - (y_paddle + PADDLE_SIZE / 2)
    new_angle = (dist_from_paddle_mid / PADDLE_SIZE) * MAX_ANGLE / 180 * math.pi
    speed = get_ball_speed(n_bounces)
    dx = math.cos(new_angle) * speed * dx_sign
    dy = math.sin(new_angle) * speed
    return dx, dy


def get_post_x_bounce_speed(xb: float, x_paddle: int, dy_sign: Literal[1, -1], n_bounces: int) -> tuple[float, float]:
    dist_from_paddle_mid = xb - (x_paddle + PADDLE_SIZE / 2)
    new_angle = (dist_from_paddle_mid / PADDLE_SIZE) * MAX_ANGLE / 180 * math.pi
    speed = get_ball_speed(n_bounces)
    dx = math.sin(new_angle) * speed
    dy = math.cos(new_angle) * speed * dy_sign
    return dx, dy


def _paddle_points(z: int, p: Literal[1, 2, 3, 4]) -> set[tuple[int, int]]:
    x = 1 if p % 2 else BOARD_SIZE - 3
    return {(xp, yp) if p <= 2 else (yp, xp) for yp in range(z, z + PADDLE_SIZE) for xp in (x, x + 1)}


def _score_points(score: int, player: Literal[1, 2, 3, 4]) -> set[tuple[int, int]]:
    origin_x = (BOARD_SIZE * (3 if player % 2 == 0 else 1)) // 4 - 3 * len(str(score))
    origin_y = 6 if player <= 2 else 50
    return {
        point
        for i, digit in enumerate(int(x) for x in str(score))
        for point in pattern_to_points(DIGIT_PATTERNS[digit], origin_x=origin_x + (6 * i), origin_y=origin_y)
    }


@matrix_script
async def display_pong(matrix: RGBMatrix) -> None:
    def draw_point(pix: tuple[int, int], color: tuple[int, int, int]) -> None:
        matrix.SetPixel(*pix, *color)

    y1 = y2 = (BOARD_SIZE - PADDLE_SIZE) // 2
    x3 = x4 = (BOARD_SIZE - PADDLE_SIZE) // 2
    y1_points = y2_points = x3_points = x4_points = set[tuple[int, int]]()
    n_players = 2
    n_bounces = 0
    last_touch: Literal[0, 1, 2, 3, 4] = 0

    score1 = score2 = score3 = score4 = -1
    score1_points = score2_points = score3_points = score4_points = set[tuple[int, int]]()

    def place_ball() -> tuple[float, float, float, float, tuple[int, int]]:
        nonlocal y1, y2, y1_points, y2_points, xb, yb, dx, dy, n_bounces, last_touch

        xb = yb = BOARD_SIZE / 2
        pi_positions = [0.0, 1.0]  # Right & left
        if n_players >= 3:
            pi_positions.append(1.5)  # Bottom
        if n_players >= 4:
            pi_positions.append(1.5)  # Top

        angle = (random.uniform(-MAX_ANGLE / 360, MAX_ANGLE / 360) + random.choice(pi_positions)) * math.pi

        n_bounces = 0
        last_touch = 0
        speed = get_ball_speed(n_bounces)
        dx = math.cos(angle) * speed
        dy = math.sin(angle) * speed
        pt = (int(round(xb)), int(round(yb)))
        return xb, yb, dx, dy, pt

    xb, yb, dx, dy, pt = place_ball()

    middle_line = {(pt[0], y) for y in range(BOARD_SIZE + 1) if 0 < y % 4 < 3}

    def draw_middle_line(off: bool = False) -> None:
        for dot in middle_line:
            draw_point(dot, NaptaColor.OFF if off else NaptaColor.CORN_FIELD)

    def update_paddles() -> None:
        nonlocal y1, y2, x3, x4, y1_points, y2_points, x3_points, x4_points

        new_y1_points, new_y2_points = _paddle_points(y1, 1), _paddle_points(y2, 2)
        new_x3_points = _paddle_points(x3, 3) if n_players >= 3 else set()
        new_x4_points = _paddle_points(x4, 4) if n_players >= 4 else set()

        for point in y1_points - new_y1_points:
            draw_point(point, NaptaColor.OFF)
        for point in new_y1_points - y1_points:
            draw_point(point, NaptaColor.BITTERSWEET)

        for point in y2_points - new_y2_points:
            draw_point(point, NaptaColor.OFF)
        for point in new_y2_points - y2_points:
            draw_point(point, NaptaColor.INDIGO)

        for point in x3_points - new_x3_points:
            draw_point(point, NaptaColor.OFF)
        for point in new_x3_points - x3_points:
            draw_point(point, NaptaColor.SPRAY)

        for point in x4_points - new_x4_points:
            draw_point(point, NaptaColor.OFF)
        for point in new_x4_points - x4_points:
            draw_point(point, NaptaColor.GORSE)

        y1_points, y2_points, x3_points, x4_points = new_y1_points, new_y2_points, new_x3_points, new_x4_points

    def _off_color(point: tuple[int, int]) -> tuple[int, int, int]:
        if point in middle_line:
            return NaptaColor.CORN_FIELD
        if point in y1_points or point in score1_points:
            return NaptaColor.BITTERSWEET
        if point in y2_points or point in score2_points:
            return NaptaColor.INDIGO
        if point in x3_points or point in score3_points:
            return NaptaColor.SPRAY
        if point in x4_points or point in score4_points:
            return NaptaColor.GORSE
        return NaptaColor.OFF

    def update_ball() -> None:
        nonlocal y1, y2, x3, x4, y1_points, y2_points, x3_points, x4_points, xb, yb, dx, dy, pt, n_bounces, last_touch

        new_xb = xb + dx
        new_yb = yb + dy
        new_pt = (int(round(new_xb)), int(round(new_yb)))

        if new_yb < BORDER_TOP:
            if n_players < 3 or x3 <= new_xb <= x3 + PADDLE_SIZE:  # Bounce top
                new_yb = BORDER_TOP - (new_yb - BORDER_TOP)
                n_bounces += 1
                dx, dy = get_post_x_bounce_speed(new_xb, x3, 1, n_bounces)
                last_touch = 3
            else:
                goal(last_touch)
                new_xb, new_yb, dx, dy, new_pt = place_ball()

        elif new_yb > BORDER_BOTTOM:
            if n_players < 4 or x4 <= new_xb <= x4 + PADDLE_SIZE:  # Bounce bottom
                new_yb = BORDER_BOTTOM - (new_yb - BORDER_BOTTOM)
                n_bounces += 1
                dx, dy = get_post_x_bounce_speed(new_xb, x4, -1, n_bounces)
                last_touch = 4
            else:
                goal(last_touch)
                new_xb, new_yb, dx, dy, new_pt = place_ball()

        if new_xb < BORDER_LEFT:
            if y1 <= new_yb <= y1 + PADDLE_SIZE:  # Bounce left
                new_xb = BORDER_LEFT - (new_xb - BORDER_LEFT)
                n_bounces += 1
                dx, dy = get_post_y_bounce_speed(new_yb, y1, 1, n_bounces)
                last_touch = 1
            else:  # Point left
                goal(last_touch)
                new_xb, new_yb, dx, dy, new_pt = place_ball()

        elif new_xb > BORDER_RIGHT:
            if y2 <= new_yb <= y2 + PADDLE_SIZE:  # Bounce right
                new_xb = BORDER_RIGHT - (new_xb - BORDER_RIGHT)
                n_bounces += 1
                dx, dy = get_post_y_bounce_speed(new_yb, y2, -1, n_bounces)
                last_touch = 2
            else:  # Point right
                goal(last_touch)
                new_xb, new_yb, dx, dy, new_pt = place_ball()

        if new_pt != pt:
            draw_point(pt, _off_color(pt))
            draw_point(new_pt, NaptaColor.GREEN)

        xb, yb, pt = new_xb, new_yb, new_pt

    def goal(player: Literal[0, 1, 2, 3, 4]) -> None:
        nonlocal score1, score2, score3, score4, score1_points, score2_points, score3_points, score4_points

        if player == 1:
            score1 += 1
            new_points = _score_points(score1, 1)
            for point in score1_points - new_points:
                draw_point(point, NaptaColor.OFF)
            for point in new_points - score1_points:
                draw_point(point, NaptaColor.BITTERSWEET)
            score1_points = new_points
        elif player == 2:
            score2 += 1
            new_points = _score_points(score2, 2)
            for point in score2_points - new_points:
                draw_point(point, NaptaColor.OFF)
            for point in new_points - score2_points:
                draw_point(point, NaptaColor.INDIGO)
            score2_points = new_points
        elif player == 3:
            score3 += 1
            new_points = _score_points(score3, 3)
            for point in score3_points - new_points:
                draw_point(point, NaptaColor.OFF)
            for point in new_points - score3_points:
                draw_point(point, NaptaColor.SPRAY)
            score3_points = new_points
        elif player == 4:
            score4 += 1
            new_points = _score_points(score4, 4)
            for point in score4_points - new_points:
                draw_point(point, NaptaColor.OFF)
            for point in new_points - score4_points:
                draw_point(point, NaptaColor.GORSE)
            score4_points = new_points

    await fullscreen_message(matrix, ["Starting", "Pong game", "server..."])
    on_started = fullscreen_message(
        matrix, ["Connect to", "play Pong:", "./play.sh", "in the repo", "(Web client", "incoming)"]
    )

    client_names = ["P1", "P2", "P3", "P4"]
    async with control_server(client_names=client_names, min_clients=2, on_started=on_started) as server:
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
                tasks = [asyncio.create_task(client.read(32), name=p) for p, client in server.clients.items()]
                done, pending = await asyncio.wait(tasks, timeout=timeout)
                inputs = {task.get_name(): task.result() for task in done}
                for task in pending:
                    task.cancel()
                y1 = get_y_pos(y1, inputs.get("P1"))
                y2 = get_y_pos(y2, inputs.get("P2"))
                if "P3" in server.clients:
                    if n_players < 3:
                        n_players = 3
                        goal(3)
                        draw_middle_line(off=True)
                        middle_line = set()
                    x3 = get_x_pos(x3, inputs.get("P3"))
                if "P4" in server.clients:
                    if n_players < 4:
                        n_players = 4
                        goal(4)
                    x4 = get_x_pos(x4, inputs.get("P4"))
            except asyncio.TimeoutError:
                pass

            update_paddles()
            update_ball()
            await asyncio.sleep(1 / FPS - (time.time() - t_start))


if __name__ == "__main__":
    asyncio.run(display_pong())
