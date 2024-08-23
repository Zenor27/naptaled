import asyncio
import random
import time
from math import ceil
from pathlib import Path

from PIL import Image

from napta_matrix import MATRIX_SIZE, RGBMatrix, graphics, matrix_script

RESTAURANTS = [
    "Picard",
    "Pontochoux (" "Curry jap" ")",
    "Les Poireaux de Marguerite",
    "Café JOA",
    "Maison Montagu",
    "Thaï Kok",
    "Aujourd'hui demain",
    "Café Mignon",
    "Grazie",
    "Bao Express",
    "Land&Monkeys",
    "Super Bao",
    "Amore Basta",
    "BANOI Amelot",
    "Séoul Lab",
    "Pasta Linea",
    "Piadineria 14.07",
    "Hua Li (traiteur chinois à saint ambroise)",
    "Babylone",
]
WHEEL_PATH = Path(__file__).parent.resolve() / "../assets/wheel.gif"


@matrix_script
async def display_random_restaurant(matrix: RGBMatrix) -> None:
    offscreen_canvas = matrix.CreateFrameCanvas()

    font = graphics.Font()
    font_path = Path(__file__).parent.resolve() / "../fonts/7x13.bdf"
    font.LoadFont(str(font_path.resolve()))
    text_color = graphics.Color(255, 255, 255)
    pos = offscreen_canvas.width

    image = Image.open(WHEEL_PATH.resolve())
    double_buffer = matrix.CreateFrameCanvas()

    start = time.time()

    def _elapsed_seconds() -> float:
        now = time.time()
        return now - start

    wheel_velocity = 0.5
    while _elapsed_seconds() < 9:
        image.seek(0)
        for keyframe in range(image.n_frames):  # type: ignore[attr-defined]
            image.seek(keyframe)
            img_cpy = image.copy()
            double_buffer.SetImage(
                img_cpy.convert("RGB").resize((MATRIX_SIZE, MATRIX_SIZE))
            )
            double_buffer = matrix.SwapOnVSync(double_buffer)
            velocity_by_elapsed_time = {
                1: 0.1,
                2: 0.05,
                3: 0.03,
                4: 0.01,
                5: 0.01,
                6: 0.03,
                7: 0.05,
                8: 0.1,
            }
            wheel_velocity = velocity_by_elapsed_time.get(ceil(_elapsed_seconds()), 0.1)
            await asyncio.sleep(wheel_velocity)

    restaurant = random.choice(RESTAURANTS)
    while True:
        offscreen_canvas.Clear()
        len = graphics.DrawText(offscreen_canvas, font, pos, 32, text_color, restaurant)
        pos -= 1
        if pos + len < 0:
            pos = offscreen_canvas.width
        await asyncio.sleep(0.05)
        offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)


if __name__ == "__main__":
    asyncio.run(display_random_restaurant())
