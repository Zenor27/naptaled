import asyncio
import math
from collections.abc import Iterator
from io import BytesIO
from pathlib import Path
from time import time
from typing import Any, Union

from PIL import Image, ImageFile

from src.helpers.napta_colors import NaptaColor
from src.napta_matrix import MATRIX_SIZE, RGBMatrix, graphics, matrix_script

SNOW_PATH = Path(__file__).parent.resolve() / "../assets/snow02.gif"


def get_frame(image_obj: ImageFile.ImageFile)->Image.Image:
    return image_obj.convert("RGB").resize((MATRIX_SIZE, MATRIX_SIZE))


def loader_screen_range(matrix: RGBMatrix, n_steps: int) -> Iterator[int]:
    font = graphics.Font()
    font_path = Path(__file__).parent.parent / "fonts" / "5x7.bdf"
    font.LoadFont(str(font_path.resolve()))

    loader_buffer = matrix.CreateFrameCanvas()
    graphics.DrawText(loader_buffer, font, 5, 25, graphics.Color(*NaptaColor.CORN_FIELD), "Loading G")
    graphics.DrawText(loader_buffer, font, 49, 25, graphics.Color(*NaptaColor.CORN_FIELD), "IF")

    X_MIN = 5
    X_MAX = MATRIX_SIZE - 8
    Y_MIN = 30
    Y_MAX = 40

    for x in range(X_MIN, X_MAX + 1):
        loader_buffer.SetPixel(x, Y_MIN, *NaptaColor.CORN_FIELD)
        loader_buffer.SetPixel(x, Y_MAX, *NaptaColor.CORN_FIELD)
    for y in range(Y_MIN, Y_MAX + 1):
        loader_buffer.SetPixel(X_MIN, y, *NaptaColor.CORN_FIELD)
        loader_buffer.SetPixel(X_MAX, y, *NaptaColor.CORN_FIELD)

    matrix.SwapOnVSync(loader_buffer)

    progress_size = (X_MAX - X_MIN - 1)
    old_progress = 0
    for step in range(n_steps):
        yield step

        progress = math.ceil((step / n_steps) * progress_size)
        for new_progress in range(old_progress, progress):
            for y in range(Y_MIN + 1, Y_MAX):
                loader_buffer.SetPixel(X_MIN + new_progress + 1, y, *NaptaColor.GREEN)

        matrix.SwapOnVSync(loader_buffer)
        old_progress = progress


@matrix_script
async def display_choose_image(
    matrix: RGBMatrix, image: Union[bytes, None] = None
) -> None:
    # Use provided image if available, otherwise fallback to default snow gif
    if image:
        image_obj = Image.open(BytesIO(image))
    else:
        image_obj = Image.open(SNOW_PATH.resolve())

    # Check if image is animated (like a GIF)
    n_frames = getattr(image_obj, "n_frames", 1)

    if n_frames > 1:
        # Load GIF frames in memory
        frames = list[tuple[Any, float]]()
        for keyframe in loader_screen_range(matrix, n_steps=n_frames):
            image_obj.seek(keyframe)
            frame_buffer = matrix.CreateFrameCanvas()
            frame_buffer.SetImage(get_frame(image_obj))
            duration_in_ms = image_obj.info["duration"]
            frames.append((frame_buffer, duration_in_ms / 1000))

        # Display frames
        while True:
            for frame_buffer, frame_duration in frames:
                t0 = time()
                matrix.SwapOnVSync(frame_buffer)
                elapsed_time = time() - t0
                await asyncio.sleep(frame_duration - elapsed_time)

    else:
        # For static images, just display them
        double_buffer = matrix.CreateFrameCanvas()
        double_buffer.SetImage(get_frame(image_obj))
        matrix.SwapOnVSync(double_buffer)



if __name__ == "__main__":
    asyncio.run(display_choose_image())
