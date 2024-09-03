import asyncio
import os
import random
import re
import sys
from typing import Iterable, Optional

import requests
from PIL import Image

from src.napta_matrix import RGBMatrix, graphics, matrix_script


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

            if non_white_count % 5 == 0:
                # Add remaining black pixels to complete the image
                completed_image = new_pixels + black_mask[len(new_pixels) :]
                yield completed_image
                non_white_count = 0

    yield image_pixels


def image_bottom_to_top(image_pixels: list[tuple[int, int, int]]) -> Iterable[list[tuple[int, int, int]]]:
    image_pixel_len = len(image_pixels)
    new_pixels: list[Optional[tuple[int, int, int]]] = [None] * image_pixel_len  # Start with a list of None

    non_white_count = 0

    # Iterate through the pixels in reverse order (bottom left to top right)
    for i in range(image_pixel_len - 1, -1, -1):
        pixel = image_pixels[i]
        new_pixels[i] = pixel  # Add the pixel to the appropriate position

        if pixel != (255, 255, 255):  # Check if the pixel is not white
            non_white_count += 1

            if non_white_count % 5 == 0:
                # Add remaining black pixels to complete the image
                completed_image = [(p if p is not None else (0, 0, 0)) for p in new_pixels]
                yield completed_image
                non_white_count = 0

    yield image_pixels  # Finally, yield the complete image


def image_shadow(image_pixels: list[tuple[int, int, int]]) -> Iterable[list[tuple[int, int, int]]]:
    image_pixel_len = len(image_pixels)
    new_pixels = []

    for i in range(image_pixel_len):
        pixel = image_pixels[i]

        if pixel != (255, 255, 255):  # Check if the pixel is not white
            new_pixels.append((0, 0, 0))  # Add the pixel to the list
        else:
            new_pixels.append(pixel)  # Add the pixel to the list

    yield new_pixels


image_heuristic = [image_pixel_by_pixel, image_bottom_to_top, image_shadow]


def extract_number(s: str) -> int:
    match = re.match(r"(\d+)", s)
    assert match
    return int(match.group(1))


def get_random_image():
    png_dir = "./assets/pokemon_images"
    png_files = [f for f in os.listdir(png_dir) if f.endswith(".png")]
    if not png_files:
        sys.exit("No PNG files found in the directory")
    png_file = random.choice(png_files)
    pkmn_nbr = extract_number(png_file)
    return os.path.join(png_dir, png_file), pkmn_nbr


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
async def whos_that_pokemon(matrix: RGBMatrix) -> None:
    print_first_text(matrix)

    await asyncio.sleep(2)

    image_file, pkmn_nbr = get_random_image()
    image = Image.open(image_file)

    # Make image fit our screen.
    image.thumbnail((matrix.width, matrix.height), Image.Resampling.LANCZOS)
    converted_image = image.convert("RGB")
    # Get the RGB data from the converted image pixel by pixel.
    converted_image_pixels: list[tuple[int, int, int]] = list(converted_image.getdata())  # pyright: ignore[reportArgumentType]

    for image_pixels in random.choice(image_heuristic)(converted_image_pixels):
        dst_image = Image.new("RGB", (matrix.width, matrix.height))
        dst_image.putdata(image_pixels)  # Place pixels in the new image.
        matrix.SetImage(dst_image)
        await asyncio.sleep(0.01)

    await asyncio.sleep(3)

    pkmn_json = requests.get(f"https://tyradex.vercel.app/api/v1/pokemon/{pkmn_nbr}").json()
    name = pkmn_json["name"]["fr"]

    offscreen_canvas = matrix.CreateFrameCanvas()
    font = graphics.Font()
    font.LoadFont("fonts/7x13.bdf")
    text_color = graphics.Color(255, 255, 0)

    offscreen_canvas.Clear()
    graphics.DrawText(offscreen_canvas, font, -2, 15, text_color, "It's")
    graphics.DrawText(offscreen_canvas, font, 0, 30, text_color, name)

    offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)

    await asyncio.sleep(2)


async def display_whos_that_pokemon() -> None:
    for i in range(5):
        await whos_that_pokemon()


if __name__ == "__main__":
    asyncio.run(display_whos_that_pokemon())
