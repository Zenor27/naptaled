#!/usr/bin/env python
from doctest import debug
import os
import random
import time
import sys
from typing import Iterable

from napta_matrix import RGBMatrix, matrix_script, graphics
from PIL import Image

def image_pixel_by_pixel(image_pixels: list[tuple[int, int, int]]) -> Iterable[list[tuple[int, int, int]]]:
    image_pixel_len = len(image_pixels)
    black_mask = [(0, 0, 0)] * image_pixel_len
    new_pixels = []

    non_white_count = 0

    for i in range(image_pixel_len):
        pixel = image_pixels[i]
        new_pixels.append(pixel)  # Add the pixel to the list

        if pixel != (255, 255, 255):  # Check if the pixel is not white
            non_white_count += 1
            
            if non_white_count % 2 == 0:
                # Add remaining black pixels to complete the image
                completed_image = new_pixels + black_mask[len(new_pixels):]
                yield completed_image
            non_white_count = 0

    yield image_pixels
        
def get_random_image():
    png_dir = "./pokemon_images"
    png_files = [f for f in os.listdir(png_dir) if f.endswith(".png")]
    if not png_files:
        sys.exit("No PNG files found in the directory")
    return os.path.join(png_dir, random.choice(png_files))

def print_first_text(matrix: RGBMatrix) -> None:
    offscreen_canvas = matrix.CreateFrameCanvas()
    font = graphics.Font()
    font.LoadFont("fonts/pokemon2.bdf")
    text_color = graphics.Color(255, 255, 0)
    
    offscreen_canvas.Clear()
    graphics.DrawText(offscreen_canvas, font, -2, 15, text_color, "Who's")
    graphics.DrawText(offscreen_canvas, font, -2, 30, text_color, "that")
    graphics.DrawText(offscreen_canvas, font, -2, 45, text_color, "Pokemon ?")

    offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)


@matrix_script
def whos_that_pokemon(matrix: RGBMatrix) -> None:
    print_first_text(matrix)
    
    time.sleep(2)
    
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
        matrix.SetImage(dst_image)
        time.sleep(0.01)
    
    input("Press Enter to exit\n")

if __name__ == "__main__":
    whos_that_pokemon()
