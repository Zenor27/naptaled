import asyncio
from pathlib import Path

from src.napta_matrix import RGBMatrix, graphics, matrix_script


@matrix_script
async def display_text(matrix: RGBMatrix, my_text: str, font_name: str = "7x13") -> None:
    offscreen_canvas = matrix.CreateFrameCanvas()

    font = graphics.Font()
    font_path = Path(__file__).parent.resolve() / f"../fonts/{font_name}.bdf"
    font.LoadFont(str(font_path.resolve()))

    text_color = graphics.Color(255, 255, 0)
    pos = offscreen_canvas.width

    while True:
        offscreen_canvas.Clear()
        len = graphics.DrawText(offscreen_canvas, font, pos, 10, text_color, my_text)
        pos -= 1
        if pos + len < 0:
            pos = offscreen_canvas.width
        offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
        await asyncio.sleep(0.05)


if __name__ == "__main__":
    asyncio.run(display_text("Hello Napta!"))
