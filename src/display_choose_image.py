import asyncio
from io import BytesIO
from pathlib import Path
from time import time
from typing import Union

from PIL import Image, ImageFile

from src.napta_matrix import MATRIX_SIZE, RGBMatrix, matrix_script

SNOW_PATH = Path(__file__).parent.resolve() / "../assets/snow02.gif"


def get_frame(image_obj: ImageFile.ImageFile)->Image.Image:
    return image_obj.convert("RGB").resize((MATRIX_SIZE, MATRIX_SIZE))


@matrix_script
async def display_choose_image(
    matrix: RGBMatrix, image: Union[bytes, None] = None
) -> None:
    # Use provided image if available, otherwise fallback to default snow gif
    if image:
        image_obj = Image.open(BytesIO(image))
    else:
        image_obj = Image.open(SNOW_PATH.resolve())

    double_buffer = matrix.CreateFrameCanvas()

    # Check if image is animated (like a GIF)
    is_animated = hasattr(image_obj, "n_frames") and image_obj.n_frames > 1  # type: ignore[attr-defined]

    if is_animated:
        frames = [
            image_obj.seek(keyframe) or (get_frame(image_obj), image_obj.info["duration"])
            for keyframe in range(image_obj.n_frames)  # type: ignore[attr-defined]
        ]

        while True:
            for frame, duration_in_ms in frames:
                t0 = time()
                double_buffer.SetImage(frame)  # TODO: use a different buffer for each frame to optimize?
                double_buffer = matrix.SwapOnVSync(double_buffer)
                elapsed_time = time() - t0
                await asyncio.sleep(duration_in_ms / 1000 - elapsed_time)

    else:
        # For static images, just display them
        double_buffer.SetImage(get_frame(image_obj))
        double_buffer = matrix.SwapOnVSync(double_buffer)



if __name__ == "__main__":
    asyncio.run(display_choose_image())
