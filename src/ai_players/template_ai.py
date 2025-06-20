# Template AI - Copy this file and modify it to create your own AI!
# 
# To use your custom AI:
# 1. Copy this file to a new name (e.g., my_awesome_ai.py)
# 2. Rename the class (e.g., MyAwesomeAI)
# 3. Implement the get_next_move() and should_boost() methods
# 4. Add your AI to the AI_CONFIG in display_slither_ai.py

from .base_ai import BaseAI, GameState, Dir


class TemplateAI(BaseAI):
    """
    Template AI class - implement your strategy here!
    
    This AI has access to:
    - game_state.snakes: Dict of all snakes (including yours)
    - game_state.apples: Set of apple positions  
    - game_state.my_snake: Your snake (deque of positions)
    - game_state.board_size: Size of the game board
    
    Useful methods from BaseAI:
    - self.get_valid_directions(game_state): Get safe directions
    - self.manhattan_distance(pos1, pos2): Calculate distance
    - self.get_neighbors(pos, board_size): Get neighboring positions
    """
    
    def __init__(self, name: str):
        super().__init__(name)
        # Add any initialization code here
        # Example: self.strategy_mode = "aggressive"
        pass
    
    def get_next_move(self, game_state: GameState) -> Dir:
        """
        Decide the next move for your snake.
        
        Args:
            game_state: Current state of the game
            
        Returns:
            Direction to move (Dir.UP, Dir.DOWN, Dir.LEFT, Dir.RIGHT)
        """
        
        # IMPLEMENT YOUR STRATEGY HERE!
        
        # Example 1: Simple safe movement
        head = game_state.get_my_head()
        if not head:
            return Dir.RIGHT
        
        valid_dirs = self.get_valid_directions(game_state)
        if not valid_dirs:
            return self.current_dir
        
        # Example 2: Move toward nearest apple
        if game_state.apples:
            nearest_apple = min(game_state.apples, 
                              key=lambda apple: self.manhattan_distance(head, apple))
            
            # Simple greedy approach - move in direction that gets closer to apple
            neighbors = self.get_neighbors(head, game_state.board_size)
            best_dir = None
            best_distance = float('inf')
            
            for direction in valid_dirs:
                next_pos = neighbors[direction]
                distance = self.manhattan_distance(next_pos, nearest_apple)
                if distance < best_distance:
                    best_distance = distance
                    best_dir = direction
            
            if best_dir:
                self.current_dir = best_dir
                return best_dir
        
        # Default: just pick first valid direction
        self.current_dir = valid_dirs[0]
        return valid_dirs[0]
    
    def should_boost(self, game_state: GameState) -> bool:
        """
        Decide whether to use boost.
        
        Boosting makes you move faster but shortens your snake.
        Use it strategically!
        
        Args:
            game_state: Current state of the game
            
        Returns:
            True if you want to boost, False otherwise
        """
        
        # IMPLEMENT YOUR BOOST STRATEGY HERE!
        
        # Example: Only boost if we're long enough and there are enemies nearby
        if len(game_state.my_snake) < 15:
            return False  # Too short to boost safely
        
        head = game_state.get_my_head()
        if not head:
            return False
        
        # Check if any other snake is nearby
        for other_snake in game_state.get_other_snakes().values():
            if other_snake:
                other_head = other_snake[0]
                distance = self.manhattan_distance(head, other_head)
                if distance < 8:  # Enemy is close
                    return True  # Boost to escape or chase
        
        return False


# Example of a more advanced AI strategy
class ExampleSmartAI(BaseAI):
    """Example of a more sophisticated AI with multiple strategies."""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.mode = "collecting"  # "collecting", "aggressive", "defensive"
        self.target_snake = None
        
    def get_next_move(self, game_state: GameState) -> Dir:
        """Advanced strategy that switches between modes."""
        head = game_state.get_my_head()
        if not head:
            return Dir.RIGHT
        
        # Switch strategies based on situation
        my_length = len(game_state.my_snake)
        other_snakes = game_state.get_other_snakes()
        
        if my_length < 10:
            self.mode = "collecting"
        elif any(len(snake) > my_length * 1.5 for snake in other_snakes.values() if snake):
            self.mode = "defensive"
        else:
            self.mode = "aggressive"
        
        if self.mode == "collecting":
            return self._collect_apples(game_state)
        elif self.mode == "aggressive":
            return self._attack_enemies(game_state)
        else:
            return self._play_defensive(game_state)
    
    def _collect_apples(self, game_state: GameState) -> Dir:
        """Focus on collecting apples safely."""
        # Implementation for apple collection strategy
        valid_dirs = self.get_valid_directions(game_state)
        return valid_dirs[0] if valid_dirs else Dir.RIGHT
    
    def _attack_enemies(self, game_state: GameState) -> Dir:
        """Aggressive strategy to cut off enemies."""
        # Implementation for aggressive strategy
        valid_dirs = self.get_valid_directions(game_state)
        return valid_dirs[0] if valid_dirs else Dir.RIGHT
    
    def _play_defensive(self, game_state: GameState) -> Dir:
        """Defensive strategy to avoid danger."""
        # Implementation for defensive strategy
        valid_dirs = self.get_valid_directions(game_state)
        return valid_dirs[0] if valid_dirs else Dir.RIGHT
    
    def should_boost(self, game_state: GameState) -> bool:
        """Smart boosting based on current mode."""
        if len(game_state.my_snake) < 12:
            return False
        
        if self.mode == "aggressive":
            return True  # Boost when attacking
        elif self.mode == "defensive":
            # Only boost if in immediate danger
            head = game_state.get_my_head()
            if head:
                for snake in game_state.get_other_snakes().values():
                    if snake and self.manhattan_distance(head, snake[0]) < 5:
                        return True
        
        return False 
