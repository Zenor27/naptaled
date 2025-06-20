from collections import deque
from typing import Optional, Tuple, Set

from .base_ai import BaseAI, GameState, Dir


class DefensiveAI(BaseAI):
    """AI that prioritizes survival and avoiding other snakes."""
    
    def get_next_move(self, game_state: GameState) -> Dir:
        """Make safe, defensive moves."""
        head = game_state.get_my_head()
        if not head:
            return Dir.RIGHT
        
        # Get all valid directions
        valid_dirs = self.get_valid_directions(game_state)
        if not valid_dirs:
            return self.current_dir
        
        # Score each direction based on safety
        scored_dirs = []
        for direction in valid_dirs:
            neighbors = self.get_neighbors(head, game_state.board_size)
            next_pos = neighbors[direction]
            
            safety_score = self.calculate_safety_score(next_pos, game_state)
            scored_dirs.append((safety_score, direction))
        
        # Sort by safety score (higher is safer)
        scored_dirs.sort(key=lambda x: x[0], reverse=True)
        
        # Choose the safest direction
        best_direction = scored_dirs[0][1]
        self.current_dir = best_direction
        return best_direction
    
    def should_boost(self, game_state: GameState) -> bool:
        """Only boost when in immediate danger and we have enough length."""
        if len(game_state.my_snake) < 20:  # Need good length to boost safely
            return False
        
        head = game_state.get_my_head()
        if not head:
            return False
        
        # Check if we're in immediate danger
        danger_level = self.assess_danger_level(head, game_state)
        return danger_level > 0.7  # High danger threshold
    
    def calculate_safety_score(self, pos: Tuple[int, int], game_state: GameState) -> float:
        """Calculate how safe a position is (higher = safer)."""
        if not game_state.is_position_safe(pos):
            return -1000  # Unsafe position
        
        score = 100  # Base safety score
        
        # Penalty for being close to borders
        x, y = pos
        border_distance = min(x, y, game_state.board_size - 1 - x, game_state.board_size - 1 - y)
        score += border_distance * 2  # Prefer staying away from borders
        
        # Penalty for being close to other snakes
        for other_snake in game_state.get_other_snakes().values():
            if not other_snake:
                continue
            
            for snake_pos in other_snake:
                distance = self.manhattan_distance(pos, snake_pos)
                if distance <= 5:  # Close to snake
                    score -= (6 - distance) * 10  # Bigger penalty for closer positions
        
        # Bonus for being near apples (but not primary concern)
        if game_state.apples:
            nearest_apple_dist = min(self.manhattan_distance(pos, apple) for apple in game_state.apples)
            score += max(0, 10 - nearest_apple_dist)  # Small bonus for being near apples
        
        # Bonus for open space (how many positions are reachable)
        open_space_score = self.calculate_open_space(pos, game_state)
        score += open_space_score * 5
        
        return score
    
    def assess_danger_level(self, head: Tuple[int, int], game_state: GameState) -> float:
        """Assess current danger level (0 = safe, 1 = extreme danger)."""
        danger = 0.0
        
        # Check proximity to other snakes
        for other_snake in game_state.get_other_snakes().values():
            if not other_snake:
                continue
            
            other_head = other_snake[0]
            distance = self.manhattan_distance(head, other_head)
            
            if distance <= 3:
                danger += 0.3  # Close snake
            elif distance <= 6:
                danger += 0.1  # Nearby snake
        
        # Check if cornered (few escape routes)
        valid_dirs = self.get_valid_directions(game_state)
        if len(valid_dirs) <= 1:
            danger += 0.5  # Very few options
        elif len(valid_dirs) <= 2:
            danger += 0.2  # Limited options
        
        # Check border proximity
        x, y = head
        border_distance = min(x, y, game_state.board_size - 1 - x, game_state.board_size - 1 - y)
        if border_distance <= 2:
            danger += 0.2  # Close to border
        
        return min(1.0, danger)  # Cap at 1.0
    
    def calculate_open_space(self, pos: Tuple[int, int], game_state: GameState) -> int:
        """Calculate how much open space is reachable from a position."""
        visited: set[Tuple[int, int]] = set()
        queue = deque([pos])
        visited.add(pos)
        
        obstacles = game_state.get_all_snake_positions()
        
        # BFS to find reachable area (limited depth for performance)
        depth = 0
        max_depth = 8
        
        while queue and depth < max_depth:
            current_level_size = len(queue)
            
            for _ in range(current_level_size):
                current = queue.popleft()
                neighbors = self.get_neighbors(current, game_state.board_size)
                
                for neighbor in neighbors.values():
                    if (neighbor not in visited and 
                        neighbor not in obstacles and
                        0 <= neighbor[0] < game_state.board_size and
                        0 <= neighbor[1] < game_state.board_size):
                        visited.add(neighbor)
                        queue.append(neighbor)
            
            depth += 1
        
        return len(visited) 
