import asyncio
import enum
import importlib
import os
import random
import time
from collections import deque
from collections.abc import Collection
from pathlib import Path
from random import choice, randrange
from typing import Dict, Any, List

from PIL import Image

from src.helpers.fullscreen_message import fullscreen_message
from src.helpers.napta_colors import NaptaColor
from src.napta_matrix import RGBMatrix, matrix_script
from src.ai_players.base_ai import BaseAI, GameState, Dir

# Game configuration
BOARD_SIZE = 64
INITIAL_SNAKE_LEN = 4
SPAWN_SAFE_ZONE = 5
APPLES_COUNT = 30
DEAD_TO_APPLE_RATE = 0.5
BOOST_TIME = 10
BOOST_RATIO = 3

FPS = 15  # Slightly slower for AI visibility

BORDER_TOP = 0
BORDER_BOTTOM = BOARD_SIZE - 1
BORDER_LEFT = 0
BORDER_RIGHT = BOARD_SIZE - 1

# Snake colors for different AI players
SNAKE_COLORS = {
    "AI1": NaptaColor.GREEN,
    "AI2": NaptaColor.BLUE, 
    "AI3": NaptaColor.BITTERSWEET,
    "AI4": NaptaColor.GORSE,
    "AI5": NaptaColor.INDIGO,
    "AI6": NaptaColor.CORN_FIELD,
}

# Default AI configuration - you can modify this to load different AIs
AI_CONFIG = [
    {"name": "AI1", "module": "src.ai_players.greedy_ai", "class": "GreedyAI"},
    {"name": "AI2", "module": "src.ai_players.aggressive_ai", "class": "AggressiveAI"},
    {"name": "AI3", "module": "src.ai_players.defensive_ai", "class": "DefensiveAI"},
    {"name": "AI4", "module": "src.ai_players.greedy_ai", "class": "GreedyAI"},  # Another greedy AI
]


class AILoader:
    """Loads AI implementations dynamically from modules."""
    
    @staticmethod
    def load_ai(config: Dict[str, Any]) -> BaseAI:
        """Load an AI from the given configuration."""
        try:
            module = importlib.import_module(config["module"])
            ai_class = getattr(module, config["class"])
            return ai_class(config["name"])
        except (ImportError, AttributeError) as e:
            print(f"Failed to load AI {config['name']}: {e}")
            # Fallback to a simple random AI
            return RandomAI(config["name"])


class RandomAI(BaseAI):
    """Simple fallback AI that moves randomly but safely."""
    
    def get_next_move(self, game_state: GameState) -> Dir:
        """Move randomly but safely."""
        valid_dirs = self.get_valid_directions(game_state)
        if valid_dirs:
            self.current_dir = random.choice(valid_dirs)
        return self.current_dir
    
    def should_boost(self, game_state: GameState) -> bool:
        """Randomly boost sometimes."""
        return len(game_state.my_snake) > 15 and random.random() < 0.1


@matrix_script
async def display_slither_ai(matrix: RGBMatrix) -> None:
    """Run AI-controlled slither game."""
    
    # Load AI players
    ai_players: Dict[str, BaseAI] = {}
    for config in AI_CONFIG:
        ai = AILoader.load_ai(config)
        ai_players[config["name"]] = ai
    
    # Game state
    snakes = dict[str, deque[tuple[int, int]]]()
    boosts = dict[str, int]()
    apples = set[tuple[int, int]]()
    eating_apples = set[tuple[int, int]]()
    dirs = dict[str, Dir]()
    scores = dict[str, int]()
    
    # Initialize scores
    for name in ai_players.keys():
        scores[name] = 0

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
        draw_point(maybe_apple, choice(list(SNAKE_COLORS.values())).value)

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
        
        color = SNAKE_COLORS.get(name, NaptaColor.GREEN).value
        for point in snakes[name]:
            draw_point(point, color)

        apples.difference_update(maybe_new_snake)

    def pop_tails(snake_names: Collection[str]) -> None:
        # Pop tails
        for name in snake_names:
            snake = snakes.get(name)
            if not snake:
                continue

            if snake[-1] in eating_apples:
                eating_apples.remove(snake[-1])
                scores[name] = scores.get(name, 0) + 1  # Increment score
            else:
                poped = snake.pop()
                draw_point(poped, NaptaColor.OFF.value)

    def compute_heads(snake_names: Collection[str]) -> None:
        dead_snakes = set[str]()

        # Compute new heads
        for name in snake_names:
            snake = snakes.get(name)
            if not snake:
                continue

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

            color = SNAKE_COLORS.get(name, NaptaColor.GREEN).value
            draw_point(new_head, color)
            snake.appendleft(new_head)

        # Remove dead snakes
        for dead_snake in dead_snakes:
            for point in snakes[dead_snake]:
                if random.random() < DEAD_TO_APPLE_RATE:
                    apples.add(point)
                    draw_point(point, choice(list(SNAKE_COLORS.values())).value)
                else:
                    draw_point(point, NaptaColor.OFF.value)

            del snakes[dead_snake]
            del dirs[dead_snake]

    # Show startup message
    await fullscreen_message(matrix, ["AI Slither", "Battle", "Starting..."])
    
    # Initialize all AI snakes
    for name in ai_players.keys():
        spawn_snake(name)
    
    matrix.SetImage(image, 0, 0)
    frame_duration = 1 / FPS
    frame_count = 0

    try:
        while True:
            frame_count += 1
            t_start = time.time()
            
            # Get AI decisions for each snake
            for name, ai in ai_players.items():
                if name not in snakes:
                    continue  # Snake is dead
                
                # Create game state for this AI
                game_state = GameState(snakes, apples, BOARD_SIZE, name)
                
                # Get AI decision
                try:
                    new_dir = ai.get_next_move(game_state)
                    dirs[name] = new_dir
                    
                    # Check if AI wants to boost
                    if (ai.should_boost(game_state) and 
                        name not in boosts and 
                        len(snakes[name]) > BOOST_TIME + INITIAL_SNAKE_LEN):
                        boosts[name] = BOOST_TIME
                        
                except Exception as e:
                    print(f"Error with AI {name}: {e}")
                    # Keep current direction on error

            # Update game state
            pop_tails(snakes.keys())
            compute_heads(snakes.keys())

            # Boost: pop 1 for tail than heads 1 time on 2
            if boosts:
                for _ in range(BOOST_RATIO - 1):
                    pop_tails(boosts.keys())
                    compute_heads(boosts.keys())
                pop_tails([name for name, boost in boosts.items() if boost % 2])
                boosts = {name: boost - 1 for name, boost in boosts.items() if boost > 1}

            # Respawn dead snakes after a delay
            if frame_count % 120 == 0:  # Every 8 seconds at 15 FPS
                for name in ai_players.keys():
                    if name not in snakes:
                        spawn_snake(name)

            # Maintain apple count
            for _ in range(APPLES_COUNT - len(apples)):
                spawn_new_apple()

            # Show scores periodically
            if frame_count % 300 == 0:  # Every 20 seconds
                score_lines = ["Scores:"]
                for name, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
                    score_lines.append(f"{name}: {score}")
                await fullscreen_message(matrix, score_lines[:6])  # Show top scores
                matrix.SetImage(image, 0, 0)

            await asyncio.sleep(max(0, frame_duration - (time.time() - t_start)))
            
    except KeyboardInterrupt:
        # Show final scores
        score_lines = ["Final Scores:"]
        for name, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            score_lines.append(f"{name}: {score}")
        await fullscreen_message(matrix, score_lines)


if __name__ == "__main__":
    asyncio.run(display_slither_ai()) 
