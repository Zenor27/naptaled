from PIL import Image
from PIL import ImageDraw
import time
from napta_matrix import RGBMatrix, matrix_script


@matrix_script
def display_image(matrix: RGBMatrix) -> None:
    image = Image.new("RGB", (64, 64))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 64, 64), fill=(0, 0, 0), outline=(0, 0, 255))
    draw.line((0, 0, 64, 64), fill=(255, 0, 0))
    draw.line((0, 64, 64, 0), fill=(0, 255, 0))

    while True:
        for n in range(-64, 64):
            matrix.Clear()
            matrix.SetImage(image, n, n)
            time.sleep(0.05)


if __name__ == "__main__":
    display_image()
