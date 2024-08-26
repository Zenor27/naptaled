import asyncio
from random import choice, randrange

from PIL import Image, ImageDraw

from src.helpers.draw import draw_pattern
from src.helpers.napta_colors import NaptaColor
from src.napta_matrix import RGBMatrix, matrix_script

LOGO_HEIGHT = 12
LOGO_WIDTH = 16


@matrix_script
async def display_screensaver(matrix: RGBMatrix) -> None:
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
            "🟩": NaptaColor.GREEN,
            "🟦": NaptaColor.SPRAY,
            "🟪": NaptaColor.INDIGO,
            "🟨": NaptaColor.GORSE,
        },
    )

    x = randrange(64 - LOGO_WIDTH)
    y = randrange(64 - LOGO_HEIGHT)
    dx = choice([-1, 1])
    dy = choice([-1, 1])

    while True:
        matrix.Clear()
        matrix.SetImage(image, x, y)
        await asyncio.sleep(0.05)
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
    asyncio.run(display_screensaver())
