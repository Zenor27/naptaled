import asyncio
from pathlib import Path
from io import BytesIO

from PIL import Image

from src.napta_matrix import MATRIX_SIZE, RGBMatrix, matrix_script

SNOW_PATH = Path(__file__).parent.resolve() / "../assets/snow02.gif"


@matrix_script
async def display_snow(matrix: RGBMatrix, image: bytes | None = None) -> None:
    # Use provided image if available, otherwise fallback to default snow gif
    if image:
        image_obj = Image.open(BytesIO(image))
    else:
        image_obj = Image.open(SNOW_PATH.resolve())

    double_buffer = matrix.CreateFrameCanvas()
    while True:
        try:
            # Check if image is animated (like a GIF)
            is_animated = hasattr(image_obj, "n_frames") and image_obj.n_frames > 1

            if is_animated:
                image_obj.seek(0)
                for keyframe in range(image_obj.n_frames):
                    image_obj.seek(keyframe)
                    img_cpy = image_obj.copy()
                    double_buffer.SetImage(
                        img_cpy.convert("RGB").resize((MATRIX_SIZE, MATRIX_SIZE))
                    )
                    double_buffer = matrix.SwapOnVSync(double_buffer)
                    await asyncio.sleep(0.01)
                await asyncio.sleep(5)
            else:
                # For static images, just display them continuously
                double_buffer.SetImage(
                    image_obj.convert("RGB").resize((MATRIX_SIZE, MATRIX_SIZE))
                )
                double_buffer = matrix.SwapOnVSync(double_buffer)
                await asyncio.sleep(5)  # Wait 5 seconds before refreshing

        except Exception as e:
            print(f"Error displaying image: {e}")
            await asyncio.sleep(1)  # Wait before retrying


if __name__ == "__main__":
    asyncio.run(display_snow())
