# AI Snake Battle System

This system allows you to create and test different AI strategies for the snake/slither game. Multiple AI players compete simultaneously on the LED matrix display.

## Quick Start

1. **Run the AI battle:**
   ```bash
   python -m src.display_slither_ai
   ```

2. **Watch the AI snakes compete** - they'll appear in different colors and automatically respawn when they die.

## How to Create Your Own AI

### Step 1: Copy the Template

1. Copy `src/ai_players/template_ai.py` to a new file:
   ```bash
   cp src/ai_players/template_ai.py src/ai_players/my_awesome_ai.py
   ```

2. Rename the class inside your new file:
   ```python
   class MyAwesomeAI(BaseAI):  # Change from TemplateAI
   ```

### Step 2: Implement Your Strategy

You need to implement two methods:

#### `get_next_move(self, game_state: GameState) -> Dir`
This method decides where your snake moves next. You have access to:

- `game_state.my_snake` - Your snake positions (head at index 0)
- `game_state.snakes` - All snakes in the game 
- `game_state.apples` - All apple positions
- `game_state.board_size` - Size of the game board (64x64)

**Example strategies:**
```python
# Strategy 1: Always go for nearest apple
if game_state.apples:
    head = game_state.get_my_head()
    nearest_apple = min(game_state.apples, 
                       key=lambda apple: self.manhattan_distance(head, apple))
    # Move toward nearest apple...

# Strategy 2: Avoid other snakes
other_snakes = game_state.get_other_snakes()
# Calculate safe directions...

# Strategy 3: Cut off enemy snakes
# Predict where enemies will go and intercept them...
```

#### `should_boost(self, game_state: GameState) -> bool`
This method decides when to boost (move faster but lose length).

**Example boost strategies:**
```python
# Boost when chasing enemies
# Boost when escaping danger  
# Boost when you're long enough
return len(game_state.my_snake) > 15 and enemy_nearby
```

### Step 3: Add Your AI to the Battle

Edit `src/display_slither_ai.py` and modify the `AI_CONFIG` list:

```python
AI_CONFIG = [
    {"name": "AI1", "module": "src.ai_players.greedy_ai", "class": "GreedyAI"},
    {"name": "AI2", "module": "src.ai_players.aggressive_ai", "class": "AggressiveAI"},
    {"name": "AI3", "module": "src.ai_players.my_awesome_ai", "class": "MyAwesomeAI"},  # Your AI!
    {"name": "AI4", "module": "src.ai_players.defensive_ai", "class": "DefensiveAI"},
]
```

### Step 4: Test Your AI

Run the battle and watch your AI compete:
```bash
python -m src.display_slither_ai
```

## Available AI Strategies

The system comes with several example AIs:

### GreedyAI (`src/ai_players/greedy_ai.py`)
- **Strategy:** Always moves toward the nearest apple using A* pathfinding
- **Boost:** When other snakes are nearby and it's long enough
- **Strengths:** Good at collecting apples efficiently
- **Weaknesses:** Predictable, doesn't avoid enemies well

### AggressiveAI (`src/ai_players/aggressive_ai.py`) 
- **Strategy:** Tries to cut off and attack other snakes
- **Boost:** When chasing enemies within optimal range
- **Strengths:** Good at eliminating competition
- **Weaknesses:** Can be reckless, might die from overconfidence

### DefensiveAI (`src/ai_players/defensive_ai.py`)
- **Strategy:** Prioritizes survival, avoids other snakes
- **Boost:** Only when in immediate danger
- **Strengths:** Survives longer, good at avoiding conflicts
- **Weaknesses:** Slow growth, might miss opportunities

## Useful Methods from BaseAI

Your AI inherits useful methods:

```python
# Get safe directions you can move
valid_dirs = self.get_valid_directions(game_state)

# Calculate distance between two points
distance = self.manhattan_distance(pos1, pos2)

# Get neighboring positions for each direction
neighbors = self.get_neighbors(position, board_size)

# Check if a position is safe to move to
is_safe = game_state.is_position_safe(position)
```

## Game Rules

- **Objective:** Eat apples to grow and survive longer than other snakes
- **Death:** Hitting borders, yourself, or other snakes kills you
- **Respawn:** Dead snakes respawn after 8 seconds
- **Boost:** Press boost to move faster but lose 1 body segment per boost
- **Scoring:** Each apple eaten = 1 point

## Advanced Tips

### 1. Pathfinding
Use A* or BFS to find optimal paths to apples while avoiding obstacles:

```python
def find_path_to_apple(self, start, goal, obstacles):
    # Implement A* pathfinding
    # Return list of positions to reach goal
```

### 2. Prediction
Predict where enemy snakes will move:

```python
def predict_enemy_position(self, enemy_snake):
    # Analyze enemy's recent moves
    # Predict their next 2-3 positions
```

### 3. Area Control
Control territory by positioning strategically:

```python
def calculate_territory_score(self, position):
    # How much space can you reach from this position?
    # BFS to count reachable empty spaces
```

### 4. Dynamic Strategy
Switch strategies based on game state:

```python
if len(self.my_snake) < 10:
    return self.collect_apples_safely()
elif enemy_nearby:
    return self.aggressive_mode()
else:
    return self.defensive_mode()
```

## Competition Ideas

1. **Tournament Mode:** Run battles and track wins/losses
2. **Specific Challenges:** Create maps with obstacles
3. **Team Battles:** Coordinate multiple AI snakes
4. **Learning AIs:** Use reinforcement learning
5. **Evolutionary AIs:** Evolve strategies over generations

## Debugging Your AI

Add print statements to see what your AI is thinking:

```python
def get_next_move(self, game_state):
    head = game_state.get_my_head()
    print(f"{self.name}: Head at {head}, found {len(game_state.apples)} apples")
    
    # Your strategy here...
```

## File Structure

```
src/
├── ai_players/
│   ├── __init__.py
│   ├── base_ai.py          # Abstract base class
│   ├── greedy_ai.py        # Example: greedy strategy
│   ├── aggressive_ai.py    # Example: aggressive strategy  
│   ├── defensive_ai.py     # Example: defensive strategy
│   ├── template_ai.py      # Template for your AI
│   └── your_custom_ai.py   # Your custom AI here!
├── display_slither_ai.py   # Main battle script
└── display_snake_ai.py     # Single AI snake (original)
```

Happy coding! Create the ultimate snake AI! 🐍🤖 
