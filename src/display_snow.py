import asyncio
from io import BytesIO
from pathlib import Path

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
    try:
        # Check if image is animated (like a GIF)
        is_animated = hasattr(image_obj, "n_frames") and image_obj.n_frames > 1  # type: ignore[attr-defined]

        if is_animated:
            frames = [
                image_obj.seek(keyframe) or image_obj.copy().convert("RGB").resize((MATRIX_SIZE, MATRIX_SIZE))
                for keyframe in range(image_obj.n_frames) # type: ignore[attr-defined]
            ]

            double_buffer = matrix.CreateFrameCanvas()

            while True:
                image_obj.seek(0)
                for frame in frames:
                    double_buffer.SetImage(frame)
                    double_buffer = matrix.SwapOnVSync(double_buffer)
                    await asyncio.sleep(0.01)

        else:
            # For static images, just display them
            double_buffer.SetImage(
                image_obj.convert("RGB").resize((MATRIX_SIZE, MATRIX_SIZE))
            )
            double_buffer = matrix.SwapOnVSync(double_buffer)

    except Exception as e:
        print(f"Error displaying image: {e}")
        await asyncio.sleep(1)  # Wait before retrying


if __name__ == "__main__":
    asyncio.run(display_snow())
