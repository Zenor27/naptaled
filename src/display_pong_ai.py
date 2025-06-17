import asyncio
import math
import random
import time
from typing import Literal

from src.helpers.digits import DIGIT_PATTERNS
from src.helpers.draw import pattern_to_points
from src.helpers.fullscreen_message import fullscreen_message
from src.helpers.napta_colors import NaptaColor
from src.napta_matrix import RGBMatrix, matrix_script

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

# AI Configuration
AI_REACTION_DELAY = 3  # frames of delay for AI reaction
AI_PREDICTION_FACTOR = 0.7  # how much to predict ball movement (0=reactive, 1=perfect prediction)
AI_ERROR_MARGIN = 5  # random error in pixels
AI_BOOST_THRESHOLD = 20  # distance threshold for using boost


def _decrease_boost(boost: int) -> int:
    return boost - 1 if boost else 0


class AIPlayer:
    """Simple AI player that tracks the ball and moves paddle accordingly"""
    
    def __init__(self, player_id: Literal[1, 2, 3, 4]):
        self.player_id = player_id
        self.reaction_counter = 0
        self.last_decision = ""
        self.boost_cooldown = 0
        
    def decide_move(self, paddle_pos: int, ball_x: float, ball_y: float, 
                   ball_dx: float, ball_dy: float, boost_active: int) -> str:
        """Decide the next move for the AI paddle"""
        
        # Add reaction delay
        self.reaction_counter += 1
        if self.reaction_counter < AI_REACTION_DELAY:
            return self.last_decision
        self.reaction_counter = 0
        
        # Reduce boost cooldown
        if self.boost_cooldown > 0:
            self.boost_cooldown -= 1
            
        # Predict where ball will be
        if self.player_id in [1, 2]:  # Vertical paddles (left/right)
            target_y = ball_y + ball_dy * AI_PREDICTION_FACTOR * 10
            # Add some error
            target_y += random.uniform(-AI_ERROR_MARGIN, AI_ERROR_MARGIN)
            
            paddle_center = paddle_pos + (BOOSTED_PADDLE_SIZE if boost_active else PADDLE_SIZE) / 2
            diff = target_y - paddle_center
            
            # Decide on boost usage
            should_boost = (abs(diff) > AI_BOOST_THRESHOLD and 
                          not boost_active and 
                          self.boost_cooldown == 0 and
                          random.random() < 0.3)  # 30% chance to boost when needed
            
            if should_boost:
                self.boost_cooldown = BOOST_FRAMES + 10  # Cooldown after boost
                if diff > 0:
                    self.last_decision = "boost_down"
                    return "boost_down"
                else:
                    self.last_decision = "boost_up"
                    return "boost_up"
            elif abs(diff) > 2:  # Dead zone to prevent jittering
                if diff > 0:
                    self.last_decision = "down"
                    return "down"
                else:
                    self.last_decision = "up" 
                    return "up"
                    
        else:  # Horizontal paddles (top/bottom)
            target_x = ball_x + ball_dx * AI_PREDICTION_FACTOR * 10
            target_x += random.uniform(-AI_ERROR_MARGIN, AI_ERROR_MARGIN)
            
            paddle_center = paddle_pos + (BOOSTED_PADDLE_SIZE if boost_active else PADDLE_SIZE) / 2
            diff = target_x - paddle_center
            
            should_boost = (abs(diff) > AI_BOOST_THRESHOLD and 
                          not boost_active and 
                          self.boost_cooldown == 0 and
                          random.random() < 0.3)
            
            if should_boost:
                self.boost_cooldown = BOOST_FRAMES + 10
                if diff > 0:
                    self.last_decision = "boost_right"
                    return "boost_right"
                else:
                    self.last_decision = "boost_left"
                    return "boost_left"
            elif abs(diff) > 2:
                if diff > 0:
                    self.last_decision = "right"
                    return "right"
                else:
                    self.last_decision = "left"
                    return "left"
        
        self.last_decision = "none"
        return "none"


def ai_get_y_pos(y: int, ai_decision: str, prev_boost: int) -> tuple[int, int]:
    """Modified get_y_pos function that takes AI decisions instead of input bytes"""
    min_y = BORDER_TOP
    max_y = BORDER_BOTTOM - (BOOSTED_PADDLE_SIZE if prev_boost else PADDLE_SIZE)
    
    if ai_decision == "up" and y >= min_y:
        return _decrease_boost(prev_boost), y - 1
    elif ai_decision == "boost_up" and y >= min_y and not prev_boost:
        return BOOST_FRAMES, max(y - BOOST_DIST + (PADDLE_SIZE - BOOSTED_PADDLE_SIZE), min_y)
    elif ai_decision == "down" and y <= max_y:
        return _decrease_boost(prev_boost), y + 1
    elif ai_decision == "boost_down" and y <= max_y and not prev_boost:
        return BOOST_FRAMES, min(y + BOOST_DIST, max_y)
    elif prev_boost == 1:  # Last boost frame: re-center paddle
        return 0, max(y - (PADDLE_SIZE - BOOSTED_PADDLE_SIZE) // 2, min_y)
    return _decrease_boost(prev_boost), y


def ai_get_x_pos(x: int, ai_decision: str, prev_boost: int) -> tuple[int, int]:
    """Modified get_x_pos function that takes AI decisions instead of input bytes"""
    min_x = BORDER_TOP
    max_x = BORDER_BOTTOM - (BOOSTED_PADDLE_SIZE if prev_boost else PADDLE_SIZE)
    
    if ai_decision == "left" and x >= min_x:
        return _decrease_boost(prev_boost), x - 1
    elif ai_decision == "boost_left" and x >= min_x and not prev_boost:
        return BOOST_FRAMES, max(x - BOOST_DIST + (PADDLE_SIZE - BOOSTED_PADDLE_SIZE), min_x)
    elif ai_decision == "right" and x <= max_x:
        return _decrease_boost(prev_boost), x + 1
    elif ai_decision == "boost_right" and x <= max_x and not prev_boost:
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


@matrix_script
async def display_pong_ai(matrix: RGBMatrix) -> None:
    def draw_point(pix: tuple[int, int], color: NaptaColor) -> None:
        matrix.SetPixel(*pix, *color.value)

    y1 = y2 = (BOARD_SIZE - PADDLE_SIZE) // 2
    x3 = x4 = (BOARD_SIZE - PADDLE_SIZE) // 2
    y1_points = y2_points = x3_points = x4_points = set[tuple[int, int]]()
    border_points = set[tuple[int, int]]()
    n_players = random.choice([2, 4])
    n_bounces = 0
    last_touch: Literal[0, 1, 2, 3, 4] = 0
    boost1 = boost2 = boost3 = boost4 = 0

    score1 = score2 = score3 = score4 = -1
    score1_points = score2_points = score3_points = score4_points = set[tuple[int, int]]()

    # Initialize AI players
    ai_player1 = AIPlayer(1)
    ai_player2 = AIPlayer(2)
    ai_player3 = AIPlayer(3)
    ai_player4 = AIPlayer(4)

    def place_ball() -> tuple[float, float, float, float, tuple[int, int]]:
        nonlocal n_bounces, last_touch

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

    def _off_color(point: tuple[int, int]) -> NaptaColor:
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

    await fullscreen_message(matrix, ["Starting", "AI Pong", "game..."])
    await asyncio.sleep(2)

    matrix.Clear()
    draw_middle_line()
    update_paddles()
    update_ball()
    goal(1, 0)
    goal(2, 0)
    if n_players >= 3:
        goal(3, 0)
    if n_players >= 4:
        goal(4, 0)
    timeout = 1 / FPS

    while True:
        t_start = time.time()
        
        # AI decision making
        ai1_decision = ai_player1.decide_move(y1, xb, yb, dx, dy, boost1)
        ai2_decision = ai_player2.decide_move(y2, xb, yb, dx, dy, boost2)
        
        boost1, y1 = ai_get_y_pos(y1, ai1_decision, boost1)
        boost2, y2 = ai_get_y_pos(y2, ai2_decision, boost2)
        
        # Handle additional players if needed
        if n_players >= 3:
            ai3_decision = ai_player3.decide_move(x3, xb, yb, dx, dy, boost3)
            boost3, x3 = ai_get_x_pos(x3, ai3_decision, boost3)
        if n_players >= 4:
            ai4_decision = ai_player4.decide_move(x4, xb, yb, dx, dy, boost4)
            boost4, x4 = ai_get_x_pos(x4, ai4_decision, boost4)

        update_paddles()
        update_ball()
        await asyncio.sleep(max(0, timeout - (time.time() - t_start)))


if __name__ == "__main__":
    asyncio.run(display_pong_ai()) 
