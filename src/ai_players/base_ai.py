import enum
from abc import ABC, abstractmethod
from collections import deque
from typing import Dict, Set, Tuple, Optional


class Dir(enum.Enum):
    UP = enum.auto()
    DOWN = enum.auto()
    RIGHT = enum.auto()
    LEFT = enum.auto()


class GameState:
    """Represents the current state of the game."""
    
    def __init__(
        self,
        snakes: Dict[str, deque[Tuple[int, int]]],
        apples: Set[Tuple[int, int]],
        board_size: int,
        my_name: str
    ):
        self.snakes = snakes
        self.apples = apples
        self.board_size = board_size
        self.my_name = my_name
        self.my_snake = snakes.get(my_name, deque())
    
    def get_my_head(self) -> Optional[Tuple[int, int]]:
        """Get the position of my snake's head."""
        return self.my_snake[0] if self.my_snake else None
    
    def get_all_snake_positions(self) -> Set[Tuple[int, int]]:
        """Get all positions occupied by any snake."""
        positions: set[Tuple[int, int]] = set()
        for snake in self.snakes.values():
            positions.update(snake)
        return positions
    
    def get_other_snakes(self) -> Dict[str, deque[Tuple[int, int]]]:
        """Get all snakes except mine."""
        return {name: snake for name, snake in self.snakes.items() if name != self.my_name}
    
    def is_position_safe(self, pos: Tuple[int, int]) -> bool:
        """Check if a position is safe to move to."""
        x, y = pos
        
        # Check bounds
        if x < 0 or x >= self.board_size or y < 0 or y >= self.board_size:
            return False
        
        # Check collision with any snake
        all_positions = self.get_all_snake_positions()
        return pos not in all_positions


class BaseAI(ABC):
    """Abstract base class for AI players."""
    
    def __init__(self, name: str):
        self.name = name
        self.current_dir = Dir.RIGHT
    
    @abstractmethod
    def get_next_move(self, game_state: GameState) -> Dir:
        """
        Determine the next move for the snake.
        
        Args:
            game_state: Current state of the game
            
        Returns:
            Direction for the next move
        """
        pass
    
    @abstractmethod
    def should_boost(self, game_state: GameState) -> bool:
        """
        Determine whether to use boost.
        
        Args:
            game_state: Current state of the game
            
        Returns:
            True if should boost, False otherwise
        """
        pass
    
    def get_neighbors(self, pos: Tuple[int, int], board_size: int) -> Dict[Dir, Tuple[int, int]]:
        """Get neighboring positions for each direction."""
        x, y = pos
        return {
            Dir.UP: (x, y - 1),
            Dir.DOWN: (x, y + 1),
            Dir.LEFT: (x - 1, y),
            Dir.RIGHT: (x + 1, y)
        }
    
    def manhattan_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """Calculate Manhattan distance between two positions."""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def get_valid_directions(self, game_state: GameState) -> list[Dir]:
        """Get all valid directions from current position."""
        if not game_state.my_snake:
            return [Dir.RIGHT]
        
        head = game_state.get_my_head()
        if not head:
            return [Dir.RIGHT]
        
        neighbors = self.get_neighbors(head, game_state.board_size)
        valid_dirs = []
        
        for direction, pos in neighbors.items():
            if game_state.is_position_safe(pos):
                valid_dirs.append(direction)
        
        return valid_dirs if valid_dirs else [Dir.RIGHT] 
