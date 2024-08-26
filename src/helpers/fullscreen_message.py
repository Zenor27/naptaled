import itertools
from pathlib import Path

from src.helpers.napta_colors import NaptaColor
from src.napta_matrix import RGBMatrix, graphics


async def fullscreen_message(
    matrix: RGBMatrix, lines: list[str], color: tuple[int, int, int] = NaptaColor.GORSE
) -> None:
    offscreen_canvas = matrix.CreateFrameCanvas()

    font = graphics.Font()
    font_path = Path(__file__).parent.parent.parent / "fonts" / "5x7.bdf"
    font.LoadFont(str(font_path.resolve()))

    for line, y in zip(lines, itertools.count(10, 8)):
        graphics.DrawText(offscreen_canvas, font, 2, y, graphics.Color(*color), line)
    offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
