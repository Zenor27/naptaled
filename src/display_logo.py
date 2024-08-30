import asyncio
from pathlib import Path

from PIL import Image

from src.napta_matrix import MATRIX_SIZE, RGBMatrix, matrix_script

TRAIN_PATH = Path(__file__).parent.resolve() / "../assets/naptaled64.gif"


@matrix_script
async def display_logo(matrix: RGBMatrix) -> None:
    image = Image.open(TRAIN_PATH.resolve())

    double_buffer = matrix.CreateFrameCanvas()
    while True:
        image.seek(0)
        for keyframe in range(image.n_frames):  # type: ignore[attr-defined]
            image.seek(keyframe)
            img_cpy = image.copy()
            double_buffer.SetImage(img_cpy.convert("RGB").resize((MATRIX_SIZE, MATRIX_SIZE)))
            double_buffer = matrix.SwapOnVSync(double_buffer)
            await asyncio.sleep(0.01)
        await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(display_logo())
