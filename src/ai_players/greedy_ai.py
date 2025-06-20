import heapq
from collections import deque
from typing import Optional, List, Set, Tuple

from .base_ai import BaseAI, GameState, Dir


class GreedyAI(BaseAI):
    """AI that always moves toward the nearest apple using A* pathfinding."""
    
    def get_next_move(self, game_state: GameState) -> Dir:
        """Move toward the nearest apple."""
        head = game_state.get_my_head()
        if not head:
            return Dir.RIGHT
        
        # Find nearest apple
        nearest_apple = self.find_nearest_apple(head, game_state.apples)
        if not nearest_apple:
            # No apples, just move safely
            valid_dirs = self.get_valid_directions(game_state)
            return valid_dirs[0] if valid_dirs else self.current_dir
        
        # Try to find path to nearest apple
        path = self.find_path_astar(head, nearest_apple, game_state)
        if path and len(path) >= 2:
            next_pos = path[1]
            direction = self.pos_to_direction(head, next_pos)
            self.current_dir = direction
            return direction
        
        # If no path found, move safely
        valid_dirs = self.get_valid_directions(game_state)
        if valid_dirs:
            self.current_dir = valid_dirs[0]
            return valid_dirs[0]
        
        return self.current_dir
    
    def should_boost(self, game_state: GameState) -> bool:
        """Boost when we're long enough and there are other snakes nearby."""
        if len(game_state.my_snake) < 15:  # Don't boost if too short
            return False
        
        head = game_state.get_my_head()
        if not head:
            return False
        
        # Check if other snakes are nearby
        for other_snake in game_state.get_other_snakes().values():
            if other_snake and self.manhattan_distance(head, other_snake[0]) < 10:
                return True
        
        return False
    
    def find_nearest_apple(self, head: Tuple[int, int], apples: Set[Tuple[int, int]]) -> Optional[Tuple[int, int]]:
        """Find the nearest apple to the head."""
        if not apples:
            return None
        
        nearest = min(apples, key=lambda apple: self.manhattan_distance(head, apple))
        return nearest
    
    def find_path_astar(self, start: Tuple[int, int], goal: Tuple[int, int], 
                       game_state: GameState) -> Optional[List[Tuple[int, int]]]:
        """Find shortest path using A* algorithm."""
        heap = [(0, start, [start])]
        visited: set[Tuple[int, int]] = set()
        obstacles = game_state.get_all_snake_positions()
        
        while heap:
            f_score, current, path = heapq.heappop(heap)
            
            if current in visited:
                continue
            visited.add(current)
            
            if current == goal:
                return path
            
            neighbors = self.get_neighbors(current, game_state.board_size)
            for direction, neighbor in neighbors.items():
                if (neighbor in visited or 
                    neighbor in obstacles or 
                    not game_state.is_position_safe(neighbor)):
                    continue
                
                new_path = path + [neighbor]
                g_score = len(new_path) - 1
                h_score = self.manhattan_distance(neighbor, goal)
                f_score = g_score + h_score
                
                heapq.heappush(heap, (f_score, neighbor, new_path))
        
        return None
    
    def pos_to_direction(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> Dir:
        """Convert position difference to direction."""
        dx = to_pos[0] - from_pos[0]
        dy = to_pos[1] - from_pos[1]
        
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
