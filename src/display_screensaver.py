from random import choice, randrange
from PIL import Image
from PIL import ImageDraw
import time
from napta_matrix import RGBMatrix, matrix_script

NAPTA_GREEN = (9, 203, 156)
LOGO_SIZE = 12

@matrix_script
def display_image(matrix: RGBMatrix) -> None:
    image = Image.new("RGB", (LOGO_SIZE, LOGO_SIZE))
    draw = ImageDraw.Draw(image)
    # draw.rectangle((0, 0, 64, 64), fill=(0, 55, 85), outline=(0, 0, 255))
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

    matrix.Clear()
    matrix.SetImage(image)

    x = randrange(64 - LOGO_SIZE)
    y = randrange(64 - LOGO_SIZE)
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
        if x > 64 - LOGO_SIZE:
            x = 64 - LOGO_SIZE
            dx = -dx
        if y < 0:
            y = 0
            dy = -dy
        if y > 64 - LOGO_SIZE:
            y = 64 - LOGO_SIZE
            dy = -dy



if __name__ == "__main__":
    display_image()
