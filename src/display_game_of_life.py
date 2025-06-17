import asyncio
import time
from PIL import Image
import numpy as np

from src.napta_matrix import RGBMatrix, matrix_script


def game_of_life_step(matrix_: np.ndarray) -> np.ndarray:
    """
    Apply one step of Conway's Game of Life to a 64x64 boolean matrix.
    
    :param matrix: np.ndarray of shape (64, 64) with boolean values (False or True)
    :return: np.ndarray of shape (64, 64) with the updated state
    """
    rows, cols = matrix_.shape

    # Create a padded version of the matrix to simplify neighbor calculations
    padded = np.pad(matrix_, pad_width=1, mode='constant', constant_values=False).astype(int)

    # Compute the number of live neighbors
    neighbors_count = (
        padded[:-2, :-2] + padded[:-2, 1:-1] + padded[:-2, 2:] +
        padded[1:-1, :-2] +                    padded[1:-1, 2:] +
        padded[2:, :-2] + padded[2:, 1:-1] + padded[2:, 2:]
    )

    # Apply the Game of Life rules
    new_matrix = ((neighbors_count == 3) | (matrix_ & (neighbors_count == 2))).astype(bool)

    return new_matrix

def draw_point(matrix: RGBMatrix, pix: tuple[int, int], color: tuple[int, int, int]) -> None:
    matrix.SetPixel(*pix, *color)

@matrix_script
async def display_game_of_life(matrix: RGBMatrix) -> None:
    state = np.random.choice([False, True], size=(64, 64), p=[0.8, 0.2])
    lifespan_matrix = state.astype(int)
    
    # Initialize two buffers to avoid flickering
    offscreen_canvas1 = matrix.CreateFrameCanvas()
    offscreen_canvas2 = matrix.CreateFrameCanvas()
    current_canvas = offscreen_canvas1
    
    while True:
        start = time.time()
        
        # Create an RGB array for the entire grid at once
        rgb_array = np.zeros((64, 64, 3), dtype=np.uint8)
        
        # Set colors for live cells based on lifespan
        mask = state
        r = np.maximum(255 - lifespan_matrix, 9) * mask
        g = np.maximum(255 - lifespan_matrix, 203) * mask
        b = np.maximum(255 - lifespan_matrix, 156) * mask
        
        # Assign colors to the RGB array
        rgb_array[..., 0] = r
        rgb_array[..., 1] = g
        rgb_array[..., 2] = b
        
        # Convert the numpy array to an image
        image = Image.fromarray(rgb_array.astype('uint8'), 'RGB')
        
        # Swap to the inactive canvas
        next_canvas = offscreen_canvas2 if current_canvas == offscreen_canvas1 else offscreen_canvas1
        
        # Set image directly without clearing first
        next_canvas.SetImage(image, 0, 0)
        
        # Swap immediately to minimize flicker
        current_canvas = matrix.SwapOnVSync(next_canvas)
        
        # Calculate next state
        state = game_of_life_step(state)
        lifespan_matrix = np.where(state, lifespan_matrix + 1, 0)
        
        elapsed = time.time() - start
        await asyncio.sleep(max(0, 0.3 - elapsed))


if __name__ == "__main__":
    asyncio.run(display_game_of_life())
