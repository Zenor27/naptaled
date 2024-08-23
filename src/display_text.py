import asyncio
from pathlib import Path

from napta_matrix import RGBMatrix, graphics, matrix_script


@matrix_script
async def display_text(matrix: RGBMatrix) -> None:
    offscreen_canvas = matrix.CreateFrameCanvas()

    font = graphics.Font()
    font_path = Path(__file__).parent.resolve() / "../fonts/7x13.bdf"
    font.LoadFont(str(font_path.resolve()))

    text_color = graphics.Color(255, 255, 0)
    pos = offscreen_canvas.width
    my_text = "Hello Napta!"
    while True:
        offscreen_canvas.Clear()
        len = graphics.DrawText(offscreen_canvas, font, pos, 10, text_color, my_text)
        pos -= 1
        if pos + len < 0:
            pos = offscreen_canvas.width
        await asyncio.sleep(0.05)
        offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)


if __name__ == "__main__":
    asyncio.run(display_text())
