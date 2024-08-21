#!/usr/bin/env python
from doctest import debug
import os
import random
import time
import sys
from typing import Iterable

from napta_matrix import RGBMatrix, RGBMatrixOptions, matrix_script
from PIL import Image

def image_pixel_by_pixel(image_pixels: list[tuple[int, int, int]]) -> Iterable[list[tuple[int, int, int]]]:
    image_pixel_len = len(image_pixels)
    black_mask = [(0, 0, 0)] * image_pixel_len
    for i in range(1, image_pixel_len, 5):
        new_pixels = image_pixels[0:i]
        new_pixels.extend(black_mask[i:image_pixel_len])
        yield new_pixels

def get_random_image():
    png_dir = "./pokemon_images"
    png_files = [f for f in os.listdir(png_dir) if f.endswith(".png")]
    if not png_files:
        sys.exit("No PNG files found in the directory")
    return os.path.join(png_dir, random.choice(png_files))


@matrix_script
def whos_that_pokemon(matrix: RGBMatrix) -> None:
    image_file = get_random_image()
    image = Image.open(image_file)

    # Make image fit our screen.
    image.thumbnail((matrix.width, matrix.height), Image.Resampling.LANCZOS)
    converted_image = image.convert('RGB')
    # Get the RGB data from the converted image pixel by pixel.
    converted_image_pixels: list[tuple[int, int, int]] = list(converted_image.getdata())
    
    for image_pixels in image_pixel_by_pixel(converted_image_pixels):
        dst_image = Image.new('RGB', (matrix.width, matrix.height))
        dst_image.putdata(image_pixels)  # Place pixels in the new image.
        matrix.Clear()
        matrix.SetImage(dst_image)
        time.sleep(0.05)
    
    # converted_image = list(converted_image)
    
    
    
    # print(converted_image)
    # matrix.SetImage(converted_image)

    try:
        print("Press CTRL-C to stop.")
        while True:
            time.sleep(100)
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    whos_that_pokemon()
