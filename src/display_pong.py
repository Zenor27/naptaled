import asyncio
import math
import random
import time
from typing import Literal

from src.helpers.control import control_server
from src.helpers.digits import DIGIT_PATTERNS
from src.helpers.draw import pattern_to_points
from src.helpers.fullscreen_message import fullscreen_message
from src.helpers.napta_colors import NaptaColor
from src.napta_matrix import KeyboardKeys, RGBMatrix, playable_matrix_script

BOARD_SIZE = 64
PADDLE_SIZE = 10
MAX_ANGLE = 70
BOOST_DIST = 24
BOOST_FRAMES = 30
BOOSTED_PADDLE_SIZE = 6
FPS = 40

BORDER_TOP = 3
BORDER_BOTTOM = BOARD_SIZE - 4
BORDER_LEFT = 3
BORDER_RIGHT = BOARD_SIZE - 4


def _decrease_boost(boost: int) -> int:
    return boost - 1 if boost else 0


def get_y_pos(y: int, input: bytes, prev_boost: int) -> tuple[int, int]:
    min_y = BORDER_TOP
    max_y = BORDER_BOTTOM - (BOOSTED_PADDLE_SIZE if prev_boost else PADDLE_SIZE)
    if b"\x1b[A" in input and y > min_y:
        return _decrease_boost(prev_boost), y - 1
    elif b"z" in input and y > min_y and not prev_boost:
        return BOOST_FRAMES, max(y - BOOST_DIST + (PADDLE_SIZE - BOOSTED_PADDLE_SIZE), min_y)
    elif b"\x1b[B" in input and y < max_y:
        return _decrease_boost(prev_boost), y + 1
    elif b"s" in input and y < max_y and not prev_boost:
        return BOOST_FRAMES, min(y + BOOST_DIST, max_y)
    elif prev_boost == 1:  # Last boost frame: re-center paddle
        return 0, max(y - (PADDLE_SIZE - BOOSTED_PADDLE_SIZE) // 2, min_y)
    return _decrease_boost(prev_boost), y


def get_x_pos(x: int, input: bytes, prev_boost: int) -> tuple[int, int]:
    min_x = BORDER_TOP
    max_x = BORDER_BOTTOM - (BOOSTED_PADDLE_SIZE if prev_boost else PADDLE_SIZE)
    if b"\x1b[D" in input and x > min_x:
        return _decrease_boost(prev_boost), x - 1
    elif b"q" in input and x > min_x and not prev_boost:
        return BOOST_FRAMES, max(x - BOOST_DIST + (PADDLE_SIZE - BOOSTED_PADDLE_SIZE), min_x)
    elif b"\x1b[C" in input and x < max_x:
        return _decrease_boost(prev_boost), x + 1
    elif b"d" in input and x < max_x and not prev_boost:
        return BOOST_FRAMES, min(x + BOOST_DIST, max_x)
    elif prev_boost == 1:  # Last boost frame: re-center paddle
        return 0, max(x - (PADDLE_SIZE - BOOSTED_PADDLE_SIZE) // 2, min_x)
    return _decrease_boost(prev_boost), x


# Adjust coeffs: https://www.desmos.com/calculator/t6ewhvgb9w
A = 0.4
B = 1.5
C = 0.85
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


def _paddle_points(z: int, p: Literal[1, 2, 3, 4], boost: int) -> set[tuple[int, int]]:
    x = 1 if p % 2 else BOARD_SIZE - 3
    paddle_size = BOOSTED_PADDLE_SIZE if boost else PADDLE_SIZE
    return {(xp, yp) if p <= 2 else (yp, xp) for yp in range(z, z + paddle_size) for xp in (x, x + 1)}


def _score_points(score: int, player: Literal[1, 2, 3, 4]) -> set[tuple[int, int]]:
    origin_x = (BOARD_SIZE * (3 if player % 2 == 0 else 1)) // 4 - 3 * len(str(score))
    origin_y = 6 if player <= 2 else 50
    return {
        point
        for i, digit in enumerate(x for x in str(score))
        for point in pattern_to_points(DIGIT_PATTERNS[digit], origin_x=origin_x + (6 * i), origin_y=origin_y)
    }


@playable_matrix_script(
    min_player_number=2,
    max_player_number=4,
    keys=[KeyboardKeys.UP, KeyboardKeys.DOWN, KeyboardKeys.LEFT, KeyboardKeys.RIGHT],
)
async def display_pong(matrix: RGBMatrix) -> None:
    def draw_point(pix: tuple[int, int], color: tuple[int, int, int]) -> None:
        matrix.SetPixel(*pix, *color)

    y1 = y2 = (BOARD_SIZE - PADDLE_SIZE) // 2
    x3 = x4 = (BOARD_SIZE - PADDLE_SIZE) // 2
    y1_points = y2_points = x3_points = x4_points = set[tuple[int, int]]()
    border_points = set[tuple[int, int]]()
    n_players = 2
    n_bounces = 0
    last_touch: Literal[0, 1, 2, 3, 4] = 0
    boost1 = boost2 = boost3 = boost4 = 0

    score1 = score2 = score3 = score4 = -1
    score1_points = score2_points = score3_points = score4_points = set[tuple[int, int]]()

    def place_ball() -> tuple[float, float, float, float, tuple[int, int]]:
        nonlocal y1, y2, y1_points, y2_points, xb, yb, dx, dy, n_bounces, last_touch

        xb = yb = BOARD_SIZE / 2
        pi_positions = [0.0, 1.0]  # Right & left
        if n_players >= 3:
            pi_positions.append(0.5)  # Top
        if n_players >= 4:
            pi_positions.append(1.5)  # Bottom

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

    def draw_border() -> None:
        nonlocal border_points
        border_points = {
            (x, y) for x in range(BORDER_LEFT - 1, BORDER_RIGHT + 2) for y in (BORDER_TOP - 1, BORDER_BOTTOM + 1)
        } | {(x, y) for y in range(BORDER_TOP - 1, BORDER_BOTTOM + 2) for x in (BORDER_LEFT - 1, BORDER_RIGHT + 1)}

        for dot in border_points:
            draw_point(dot, NaptaColor.BLUE)

    def update_paddles() -> None:
        nonlocal y1, y2, x3, x4, y1_points, y2_points, x3_points, x4_points

        new_y1_points, new_y2_points = _paddle_points(y1, 1, boost1), _paddle_points(y2, 2, boost2)
        new_x3_points = _paddle_points(x3, 3, boost3) if n_players >= 3 else set()
        new_x4_points = _paddle_points(x4, 4, boost4) if n_players >= 4 else set()

        for point in y1_points - new_y1_points:
            draw_point(point, NaptaColor.BLUE if point in border_points else NaptaColor.OFF)
        for point in new_y1_points - y1_points:
            draw_point(point, NaptaColor.BITTERSWEET)

        for point in y2_points - new_y2_points:
            draw_point(point, NaptaColor.BLUE if point in border_points else NaptaColor.OFF)
        for point in new_y2_points - y2_points:
            draw_point(point, NaptaColor.INDIGO)

        for point in x3_points - new_x3_points:
            draw_point(point, NaptaColor.BLUE if point in border_points else NaptaColor.OFF)
        for point in new_x3_points - x3_points:
            draw_point(point, NaptaColor.SPRAY)

        for point in x4_points - new_x4_points:
            draw_point(point, NaptaColor.BLUE if point in border_points else NaptaColor.OFF)
        for point in new_x4_points - x4_points:
            draw_point(point, NaptaColor.GORSE)

        y1_points, y2_points, x3_points, x4_points = (
            new_y1_points,
            new_y2_points,
            new_x3_points,
            new_x4_points,
        )

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
        if point in border_points:
            return NaptaColor.BLUE
        return NaptaColor.OFF

    def update_ball() -> None:
        nonlocal y1, y2, x3, x4, y1_points, y2_points, x3_points, x4_points, xb, yb, dx, dy, pt, n_bounces, last_touch

        new_xb = xb + dx
        new_yb = yb + dy
        new_pt = (int(round(new_xb)), int(round(new_yb)))

        if new_yb < BORDER_TOP:
            if n_players < 3:  # Bounce on top wall
                new_yb = BORDER_TOP - (new_yb - BORDER_TOP)
                dy = -dy
            elif x3 - 1 <= new_xb <= x3 + (BOOSTED_PADDLE_SIZE if boost3 else PADDLE_SIZE) + 1:  # Bounce on top paddle
                new_yb = BORDER_TOP - (new_yb - BORDER_TOP)
                n_bounces += 1
                dx, dy = get_post_x_bounce_speed(new_xb, x3, 1, n_bounces)
                last_touch = 3
            else:  # Point top
                goal(last_touch, 3)
                new_xb, new_yb, dx, dy, new_pt = place_ball()

        elif new_yb > BORDER_BOTTOM:
            if n_players < 4:  # Bounce on bottom wall
                new_yb = BORDER_BOTTOM - (new_yb - BORDER_BOTTOM)
                dy = -dy
            elif x4 - 1 <= new_xb <= x4 + (BOOSTED_PADDLE_SIZE if boost4 else PADDLE_SIZE) + 1:  # Bounce on bot paddle
                new_yb = BORDER_BOTTOM - (new_yb - BORDER_BOTTOM)
                n_bounces += 1
                dx, dy = get_post_x_bounce_speed(new_xb, x4, -1, n_bounces)
                last_touch = 4
            else:  # Point bottom
                goal(last_touch, 4)
                new_xb, new_yb, dx, dy, new_pt = place_ball()

        if new_xb < BORDER_LEFT:
            if y1 - 1 <= new_yb <= y1 + (BOOSTED_PADDLE_SIZE if boost1 else PADDLE_SIZE) + 1:  # Bounce on left paddle
                new_xb = BORDER_LEFT - (new_xb - BORDER_LEFT)
                n_bounces += 1
                dx, dy = get_post_y_bounce_speed(new_yb, y1, 1, n_bounces)
                last_touch = 1
            else:  # Point left
                goal(last_touch, 1)
                new_xb, new_yb, dx, dy, new_pt = place_ball()

        elif new_xb > BORDER_RIGHT:
            if y2 - 1 <= new_yb <= y2 + (BOOSTED_PADDLE_SIZE if boost2 else PADDLE_SIZE) + 1:  # Bounce on right paddle
                new_xb = BORDER_RIGHT - (new_xb - BORDER_RIGHT)
                n_bounces += 1
                dx, dy = get_post_y_bounce_speed(new_yb, y2, -1, n_bounces)
                last_touch = 2
            else:  # Point right
                goal(last_touch, 2)
                new_xb, new_yb, dx, dy, new_pt = place_ball()

        if new_pt != pt:
            draw_point(pt, _off_color(pt))
            draw_point(new_pt, NaptaColor.GREEN)

        xb, yb, pt = new_xb, new_yb, new_pt

    def goal(player: Literal[0, 1, 2, 3, 4], player_looser: Literal[0, 1, 2, 3, 4]) -> None:
        nonlocal score1, score2, score3, score4, score1_points, score2_points, score3_points, score4_points

        if player == 1:
            score1 += 2
        elif player == 2:
            score2 += 2
        elif player == 3:
            score3 += 2
        elif player == 4:
            score4 += 2

        if player_looser == 1:
            score1 -= 1
        elif player_looser == 2:
            score2 -= 1
        elif player_looser == 3:
            score3 -= 1
        elif player_looser == 4:
            score4 -= 1

        if player == 1 or player_looser == 1:
            new_points = _score_points(score1, 1)
            for point in score1_points - new_points:
                draw_point(point, NaptaColor.OFF)
            for point in new_points - score1_points:
                draw_point(point, NaptaColor.BITTERSWEET)
            score1_points = new_points
        if player == 2 or player_looser == 2:
            new_points = _score_points(score2, 2)
            for point in score2_points - new_points:
                draw_point(point, NaptaColor.OFF)
            for point in new_points - score2_points:
                draw_point(point, NaptaColor.INDIGO)
            score2_points = new_points
        if player == 3 or player_looser == 3:
            new_points = _score_points(score3, 3)
            for point in score3_points - new_points:
                draw_point(point, NaptaColor.OFF)
            for point in new_points - score3_points:
                draw_point(point, NaptaColor.SPRAY)
            score3_points = new_points
        if player == 4 or player_looser == 4:
            new_points = _score_points(score4, 4)
            for point in score4_points - new_points:
                draw_point(point, NaptaColor.OFF)
            for point in new_points - score4_points:
                draw_point(point, NaptaColor.GORSE)
            score4_points = new_points

    await fullscreen_message(matrix, ["Starting", "Pong game", "server..."])
    on_started = fullscreen_message(
        matrix,
        ["Waiting for", "players..."],
    )

    client_names = ["P1", "P2", "P3", "P4"]
    async with control_server(client_names=client_names, min_clients=2, on_started=on_started) as server:
        matrix.Clear()
        draw_middle_line()
        update_paddles()
        update_ball()
        goal(1, 0)
        goal(2, 0)
        timeout = 1 / FPS

        while True:
            t_start = time.time()
            try:
                tasks = [asyncio.create_task(client.read(32), name=p) for p, client in server.clients.items()]
                done, pending = await asyncio.wait(tasks, timeout=timeout)
                inputs = {task.get_name(): task.result() for task in done}
                for task in pending:
                    task.cancel()
                boost1, y1 = get_y_pos(y1, inputs.get("P1", b""), boost1)
                boost2, y2 = get_y_pos(y2, inputs.get("P2", b""), boost2)
                if "P3" in server.clients:
                    if n_players < 3:
                        n_players = 3
                        goal(3, 0)
                        y1_points = y2_points = set()
                        draw_middle_line(off=True)
                        draw_border()
                        middle_line = set()
                    boost3, x3 = get_x_pos(x3, inputs.get("P3", b""), boost3)
                if "P4" in server.clients:
                    if n_players < 4:
                        n_players = 4
                        goal(4, 0)
                    boost4, x4 = get_x_pos(x4, inputs.get("P4", b""), boost4)
            except asyncio.TimeoutError:
                pass

            update_paddles()
            update_ball()
            await asyncio.sleep(1 / FPS - (time.time() - t_start))


if __name__ == "__main__":
    asyncio.run(display_pong())
