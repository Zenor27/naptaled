from napta_matrix import RGBMatrix, RGBMatrixOptions, graphics
from pathlib import Path
import time


def run():
    options = RGBMatrixOptions()
    options.rows = 64
    options.cols = 64
    options.chain_length = 1
    options.parallel = 1
    options.hardware_mapping = "regular"
    matrix = RGBMatrix(options=options)
    offscreen_canvas = matrix.CreateFrameCanvas()

    font = graphics.Font()
    current_path = Path(__file__).parent.resolve()
    font_path = current_path / "../fonts/7x13.bdf"
    font.LoadFont(str(font_path.resolve()))
    textColor = graphics.Color(255, 255, 0)
    pos = offscreen_canvas.width
    my_text = "Hello Napta!"
    while True:
        offscreen_canvas.Clear()
        len = graphics.DrawText(offscreen_canvas, font, pos, 10, textColor, my_text)
        pos -= 1
        if (pos + len < 0):
            pos = offscreen_canvas.width
        time.sleep(0.05)
        offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)

# Main function
if __name__ == "__main__":
    run()
