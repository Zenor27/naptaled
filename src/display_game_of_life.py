import asyncio
import time

from src.napta_matrix import RGBMatrix, matrix_script


import numpy as np


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
    # state = np.zeros((64, 64), dtype=bool)
    # state[30, 30:33] = True  # A simple blinker pattern
    while True:
        start = time.time()
        double_buffer = matrix.CreateFrameCanvas()
        for y in range(64):
            for x in range(64):
                GREEN = (9, 203, 156)
                
                double_buffer.SetPixel(x, y, max(255- lifespan_matrix[y, x], 9), max(255 - lifespan_matrix[y, x], 203),  max(255 - lifespan_matrix[y, x], 156)) if state[y, x] else double_buffer.SetPixel(x, y, 0, 0, 0)
                
        # count all True in the matrix 
        matrix.SwapOnVSync(double_buffer)

        state = game_of_life_step(state)
        lifespan_matrix = np.where(state, lifespan_matrix + 1, 0)

        await asyncio.sleep(max(0, 0.3 - (time.time() - start)))



if __name__ == "__main__":
    asyncio.run(display_game_of_life())
