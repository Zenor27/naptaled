import asyncio
import enum
import time
from collections import deque
from random import randrange
from typing import Optional
import heapq

from PIL import Image, ImageDraw

from src.helpers.fullscreen_message import fullscreen_message
from src.helpers.napta_colors import NaptaColor
from src.napta_matrix import RGBMatrix, matrix_script

BOARD_SIZE = 64
INITIAL_SNAKE_LEN = 4
FPS = 10  # Slower for AI to be more visible


class Dir(enum.Enum):
    UP = enum.auto()
    DOWN = enum.auto()
    RIGHT = enum.auto()
    LEFT = enum.auto()


class SnakeAI:
    """AI player for the snake game using A* pathfinding."""
    
    def __init__(self, board_size: int):
        self.board_size = board_size
    
    def get_neighbors(self, pos: tuple[int, int]) -> list[tuple[int, int]]:
        """Get valid neighboring positions."""
        x, y = pos
        neighbors = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            new_x = (x + dx) % self.board_size
            new_y = (y + dy) % self.board_size
            neighbors.append((new_x, new_y))
        return neighbors
    
    def manhattan_distance(self, pos1: tuple[int, int], pos2: tuple[int, int]) -> int:
        """Calculate Manhattan distance between two positions."""
        x1, y1 = pos1
        x2, y2 = pos2
        # Handle wrapping around the board
        dx = min(abs(x2 - x1), self.board_size - abs(x2 - x1))
        dy = min(abs(y2 - y1), self.board_size - abs(y2 - y1))
        return dx + dy
    
    def find_path_astar(self, start: tuple[int, int], goal: tuple[int, int], 
                       obstacles: set[tuple[int, int]]) -> Optional[list[tuple[int, int]]]:
        """Find shortest path using A* algorithm."""
        heap = [(0, start, [start])]
        visited = set()
        
        while heap:
            f_score, current, path = heapq.heappop(heap)
            
            if current in visited:
                continue
            visited.add(current)
            
            if current == goal:
                return path
            
            for neighbor in self.get_neighbors(current):
                if neighbor in visited or neighbor in obstacles:
                    continue
                
                new_path = path + [neighbor]
                g_score = len(new_path) - 1
                h_score = self.manhattan_distance(neighbor, goal)
                f_score = g_score + h_score
                
                heapq.heappush(heap, (f_score, neighbor, new_path))
        
        return None
    
    def find_longest_path(self, start: tuple[int, int], 
                         obstacles: set[tuple[int, int]]) -> Optional[tuple[int, int]]:
        """Find direction that leads to the longest available path (survival mode)."""
        best_direction = None
        max_length = 0
        
        for neighbor in self.get_neighbors(start):
            if neighbor in obstacles:
                continue
            
            # Use BFS to find reachable area size
            queue = deque([neighbor])
            visited = {neighbor}
            length = 0
            
            while queue and length < 100:  # Limit search depth
                current = queue.popleft()
                length += 1
                
                for next_pos in self.get_neighbors(current):
                    if next_pos not in visited and next_pos not in obstacles:
                        visited.add(next_pos)
                        queue.append(next_pos)
            
            if length > max_length:
                max_length = length
                best_direction = neighbor
        
        return best_direction
    
    def get_next_move(self, snake: deque, apple: tuple[int, int]) -> Dir:
        """Determine the next move for the snake."""
        head = snake[0]
        snake_body = set(snake)
        
        # Try to find path to apple
        path = self.find_path_astar(head, apple, snake_body)
        
        if path and len(path) >= 2:
            next_pos = path[1]  # Next position in path
        else:
            # If no path to apple, try survival mode
            next_pos = self.find_longest_path(head, snake_body)
            if not next_pos:
                # Last resort: just pick any safe direction
                for neighbor in self.get_neighbors(head):
                    if neighbor not in snake_body:
                        next_pos = neighbor
                        break
        
        if not next_pos:
            # No safe move found, game over is imminent
            return Dir.RIGHT  # Default direction
        
        # Convert position to direction
        head_x, head_y = head
        next_x, next_y = next_pos
        
        # Handle wrapping
        dx = next_x - head_x
        if dx > self.board_size // 2:
            dx -= self.board_size
        elif dx < -self.board_size // 2:
            dx += self.board_size
            
        dy = next_y - head_y
        if dy > self.board_size // 2:
            dy -= self.board_size
        elif dy < -self.board_size // 2:
            dy += self.board_size
        
        if dx == 1:
            return Dir.RIGHT
        elif dx == -1:
            return Dir.LEFT
        elif dy == 1:
            return Dir.DOWN
        elif dy == -1:
            return Dir.UP
        else:
            return Dir.RIGHT  # Fallback


@matrix_script
async def display_snake_ai(matrix: RGBMatrix) -> None:
    """AI-controlled snake game."""
    snake = deque(((20 + i) % BOARD_SIZE, 40) for i in range(INITIAL_SNAKE_LEN, 0, -1))  # Head to queue
    ai = SnakeAI(BOARD_SIZE)
    score = 0

    def get_next_apple() -> tuple[int, int]:
        while (maybe_apple := (randrange(BOARD_SIZE), randrange(BOARD_SIZE))) in snake:
            continue
        return maybe_apple

    apple = get_next_apple()
    eating_apples = set[tuple[int, int]]()
    dir = Dir.RIGHT

    image = Image.new("RGB", (BOARD_SIZE, BOARD_SIZE))
    draw = ImageDraw.Draw(image)
    draw.point(snake, NaptaColor.BITTERSWEET.value)
    draw.point(apple, NaptaColor.GREEN.value)

    def draw_point(pix: tuple[int, int], color: tuple[int, int, int]) -> None:
        matrix.SetPixel(*pix, *color)

    def update_game() -> bool:
        """Update game state. Returns False if game over."""
        nonlocal apple, dir, score

        if snake[-1] in eating_apples:
            eating_apples.remove(snake[-1])
            score += 1
        else:
            poped = snake.pop()
            draw_point(poped, NaptaColor.OFF.value)

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
            draw_point(apple, NaptaColor.GREEN.value)

        for eating_apple in eating_apples:
            draw_point(eating_apple, NaptaColor.GORSE.value)

        if new_head in snake:
            return False  # Game over

        draw_point(new_head, NaptaColor.BITTERSWEET.value)
        snake.appendleft(new_head)
        return True

    await fullscreen_message(matrix, ["AI Snake", "Starting...", f"Watch the AI", "play Snake!"])
    
    matrix.SetImage(image, 0, 0)
    
    try:
        while True:
            t_start = time.time()
            
            # AI makes decision
            dir = ai.get_next_move(snake, apple)
            
            # Update game
            if not update_game():
                await fullscreen_message(matrix, ["Game Over!", f"AI Score: {score}", "Restarting..."])
                await asyncio.sleep(3)
                # Reset game
                snake = deque(((20 + i) % BOARD_SIZE, 40) for i in range(INITIAL_SNAKE_LEN, 0, -1))
                apple = get_next_apple()
                eating_apples = set()
                dir = Dir.RIGHT
                score = 0
                
                # Redraw initial state
                image = Image.new("RGB", (BOARD_SIZE, BOARD_SIZE))
                draw = ImageDraw.Draw(image)
                draw.point(snake, NaptaColor.BITTERSWEET.value)
                draw.point(apple, NaptaColor.GREEN.value)
                matrix.SetImage(image, 0, 0)
            
            # Control game speed
            elapsed = time.time() - t_start
            sleep_time = max(0, 1 / FPS - elapsed)
            await asyncio.sleep(sleep_time)
            
    except KeyboardInterrupt:
        await fullscreen_message(matrix, ["AI Snake", "Stopped"])


if __name__ == "__main__":
    asyncio.run(display_snake_ai()) 
