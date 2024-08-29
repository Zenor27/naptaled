import asyncio

from PIL import Image, ImageDraw

from src.helpers.fullscreen_message import fullscreen_message
from src.napta_matrix import RGBMatrix, matrix_script


@matrix_script
async def off(matrix: RGBMatrix) -> None:
    fullscreen_message(
        matrix,
        [
            "Deployment",
            "    in    ",
            "progress!",
        ],
    )


if __name__ == "__main__":
    asyncio.run(off())
