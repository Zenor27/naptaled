from random import choice, randrange
from PIL import Image
from PIL import ImageDraw
import time
from napta_matrix import RGBMatrix, matrix_script

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
    # Napta
    draw.line((0, 1, 0, 11), fill=NAPTA_GREEN)
    draw.line((1, 0, 1, 11), fill=NAPTA_GREEN)
    draw.line((2, 0, 2, 11), fill=NAPTA_GREEN)
    draw.line((3, 1, 3, 3), fill=NAPTA_GREEN)
    draw.line((4, 2, 4, 4), fill=NAPTA_GREEN)
    draw.line((5, 4, 5, 5), fill=NAPTA_GREEN)
    draw.line((6, 7, 6, 8), fill=NAPTA_GREEN)
    draw.line((7, 8, 7, 10), fill=NAPTA_GREEN)
    draw.line((8, 9, 8, 11), fill=NAPTA_GREEN)
    draw.line((9, 0, 9, 11), fill=NAPTA_GREEN)
    draw.line((10, 0, 10, 11), fill=NAPTA_GREEN)
    draw.line((11, 0, 11, 10), fill=NAPTA_GREEN)
    # L
    draw.line((13, 0, 13, 0), fill=NAPTA_SPRAY)
    draw.line((13, 1, 13, 1), fill=NAPTA_SPRAY)
    draw.line((13, 2, 15, 2), fill=NAPTA_SPRAY)
    # E
    draw.line((13, 3, 15, 3), fill=NAPTA_INDIGO)
    draw.line((13, 4, 13, 4), fill=NAPTA_INDIGO)
    draw.line((13, 5, 14, 5), fill=NAPTA_INDIGO)
    draw.line((13, 6, 13, 6), fill=NAPTA_INDIGO)
    draw.line((13, 7, 15, 7), fill=NAPTA_INDIGO)
    # D
    draw.line((13, 8, 14, 8), fill=NAPTA_GORSE)
    draw.line((13, 9, 13, 10), fill=NAPTA_GORSE)
    draw.line((15, 9, 15, 10), fill=NAPTA_GORSE)
    draw.line((13, 11, 14, 11), fill=NAPTA_GORSE)

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
