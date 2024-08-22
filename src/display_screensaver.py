from random import choice, randrange
from PIL import Image
from PIL import ImageDraw
import time
from napta_matrix import RGBMatrix, matrix_script
from helpers.draw import draw_pattern

NAPTA_GREEN = (9, 203, 156)
NAPTA_SPRAY = (117, 221, 221)
NAPTA_INDIGO = (84, 5, 255)
NAPTA_GORSE = (249, 229, 64)
RED = (255, 0, 0)

LOGO_HEIGHT = 12
LOGO_WIDTH = 16


@matrix_script
def display_image(matrix: RGBMatrix) -> None:
    image = Image.new("RGB", (LOGO_WIDTH, LOGO_HEIGHT))
    draw = ImageDraw.Draw(image)

    draw_pattern(
        draw,
        """
            ⬛🟩🟩⬛⬛⬛⬛⬛⬛🟩🟩🟩⬛🟦⬛⬛
            🟩🟩🟩🟩⬛⬛⬛⬛⬛🟩🟩🟩⬛🟦⬛⬛
            🟩🟩🟩🟩🟩⬛⬛⬛⬛🟩🟩🟩⬛🟦🟦🟦
            🟩🟩🟩🟩🟩⬛⬛⬛⬛🟩🟩🟩⬛🟪🟪🟪
            🟩🟩🟩⬛🟩🟩⬛⬛⬛🟩🟩🟩⬛🟪⬛⬛
            🟩🟩🟩⬛⬛🟩⬛⬛⬛🟩🟩🟩⬛🟪🟪⬛
            🟩🟩🟩⬛⬛⬛⬛⬛⬛🟩🟩🟩⬛🟪⬛⬛
            🟩🟩🟩⬛⬛⬛🟩⬛⬛🟩🟩🟩⬛🟪🟪🟪
            🟩🟩🟩⬛⬛⬛🟩🟩⬛🟩🟩🟩⬛🟨🟨⬛
            🟩🟩🟩⬛⬛⬛⬛🟩🟩🟩🟩🟩⬛🟨⬛🟨
            🟩🟩🟩⬛⬛⬛⬛🟩🟩🟩🟩🟩⬛🟨⬛🟨
            🟩🟩🟩⬛⬛⬛⬛⬛🟩🟩🟩⬛⬛🟨🟨⬛
        """,
        {
            "🟩": NAPTA_GREEN,
            "🟦": NAPTA_SPRAY,
            "🟪": NAPTA_INDIGO,
            "🟨": NAPTA_GORSE,
        },
    )

    x = randrange(64 - LOGO_WIDTH)
    y = randrange(64 - LOGO_HEIGHT)
    dx = choice([-1, 1])
    dy = choice([-1, 1])

    while True:
        matrix.Clear()
        matrix.SetImage(image, x, y)
        time.sleep(0.05)
        x += dx
        y += dy
        if x < 0:
            x = 0
            dx = -dx
        if x > 64 - LOGO_WIDTH:
            x = 64 - LOGO_WIDTH
            dx = -dx
        if y < 0:
            y = 0
            dy = -dy
        if y > 64 - LOGO_HEIGHT:
            y = 64 - LOGO_HEIGHT
            dy = -dy


if __name__ == "__main__":
    display_image()
