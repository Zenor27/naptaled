import random
from collections import deque
from typing import Optional, Tuple, List

from .base_ai import BaseAI, GameState, Dir


class AggressiveAI(BaseAI):
    """AI that tries to cut off other snakes and plays aggressively."""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.target_snake: Optional[str] = None
        self.last_boost_time = 0
        self.boost_cooldown = 30  # frames
        self.frame_count = 0
    
    def get_next_move(self, game_state: GameState) -> Dir:
        """Make aggressive moves to cut off other snakes."""
        self.frame_count += 1
        head = game_state.get_my_head()
        if not head:
            return Dir.RIGHT
        
        # Find a target snake to chase/cut off
        target = self.find_target_snake(game_state)
        
        if target and target in game_state.snakes:
            target_snake = game_state.snakes[target]
            target_head = target_snake[0] if target_snake else None
            
            if target_head:
                # Try to intercept the target snake
                intercept_pos = self.predict_intercept_position(target_head, target_snake, game_state)
                if intercept_pos:
                    direction = self.move_toward_position(head, intercept_pos, game_state)
                    if direction:
                        self.current_dir = direction
                        return direction
        
        # If no good aggressive move, go for nearest apple
        nearest_apple = self.find_nearest_apple(head, game_state.apples)
        if nearest_apple:
            direction = self.move_toward_position(head, nearest_apple, game_state)
            if direction:
                self.current_dir = direction
                return direction
        
        # Fall back to safe movement
        valid_dirs = self.get_valid_directions(game_state)
        if valid_dirs:
            self.current_dir = valid_dirs[0]
            return valid_dirs[0]
        
        return self.current_dir
    
    def should_boost(self, game_state: GameState) -> bool:
        """Boost strategically when chasing or escaping."""
        if len(game_state.my_snake) < 12:  # Need some length to boost
            return False
        
        if self.frame_count - self.last_boost_time < self.boost_cooldown:
            return False
        
        head = game_state.get_my_head()
        if not head:
            return False
        
        # Boost when chasing a nearby snake
        for other_name, other_snake in game_state.get_other_snakes().items():
            if not other_snake:
                continue
            
            other_head = other_snake[0]
            distance = self.manhattan_distance(head, other_head)
            
            # Boost if we're close and can potentially cut them off
            if 3 <= distance <= 8:
                self.last_boost_time = self.frame_count
                return True
        
        return False
    
    def find_target_snake(self, game_state: GameState) -> Optional[str]:
        """Find the best snake to target."""
        head = game_state.get_my_head()
        if not head:
            return None
        
        other_snakes = game_state.get_other_snakes()
        if not other_snakes:
            return None
        
        # Prefer targeting snakes that are close and smaller than us
        best_target = None
        best_score = float('inf')
        
        for name, snake in other_snakes.items():
            if not snake:
                continue
            
            other_head = snake[0]
            distance = self.manhattan_distance(head, other_head)
            size_diff = len(game_state.my_snake) - len(snake)
            
            # Score: prefer closer snakes, especially if we're bigger
            score = distance - (size_diff * 2)
            
            if score < best_score:
                best_score = score
                best_target = name
        
        return best_target
    
    def predict_intercept_position(self, target_head: Tuple[int, int], 
                                 target_snake: deque[Tuple[int, int]], 
                                 game_state: GameState) -> Optional[Tuple[int, int]]:
        """Predict where to intercept the target snake."""
        # Simple prediction: assume target continues in current direction
        if len(target_snake) < 2:
            return target_head
        
        # Get target's current direction
        curr_x, curr_y = target_head
        prev_x, prev_y = target_snake[1]
        dx = curr_x - prev_x
        dy = curr_y - prev_y
        
        # Predict 2-3 steps ahead
        steps_ahead = 3
        pred_x = (curr_x + dx * steps_ahead) % game_state.board_size
        pred_y = (curr_y + dy * steps_ahead) % game_state.board_size
        
        # Clamp to board boundaries (no wrapping in slither)
        pred_x = max(0, min(game_state.board_size - 1, pred_x))
        pred_y = max(0, min(game_state.board_size - 1, pred_y))
        
        return (pred_x, pred_y)
    
    def move_toward_position(self, from_pos: Tuple[int, int], 
                           to_pos: Tuple[int, int], 
                           game_state: GameState) -> Optional[Dir]:
        """Move toward a target position safely."""
        neighbors = self.get_neighbors(from_pos, game_state.board_size)
        
        # Calculate which direction gets us closer
        best_dir = None
        best_distance = float('inf')
        
        for direction, pos in neighbors.items():
            if not game_state.is_position_safe(pos):
                continue
            
            distance = self.manhattan_distance(pos, to_pos)
            if distance < best_distance:
                best_distance = distance
                best_dir = direction
        
        return best_dir
    
    def find_nearest_apple(self, head: Tuple[int, int], apples: set[Tuple[int, int]]) -> Optional[Tuple[int, int]]:
        """Find the nearest apple to the head."""
        if not apples:
            return None
        
        nearest = min(apples, key=lambda apple: self.manhattan_distance(head, apple))
        return nearest 
