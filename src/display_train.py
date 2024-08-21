from pathlib import Path
from PIL import Image
import time
from napta_matrix import MATRIX_SIZE, RGBMatrix, matrix_script

TRAIN_PATH = Path(__file__).parent.resolve() / "../assets/train.gif"


@matrix_script
def display_image(matrix: RGBMatrix) -> None:
    image = Image.open(TRAIN_PATH.resolve())

    double_buffer = matrix.CreateFrameCanvas()
    while True:
        image.seek(0)
        for keyframe in range(image.n_frames):  # type: ignore[attr-defined]
            image.seek(keyframe)
            img_cpy = image.copy()
            double_buffer.SetImage(img_cpy.resize((MATRIX_SIZE, MATRIX_SIZE)))
            double_buffer = matrix.SwapOnVSync(double_buffer)
            time.sleep(0.1)


if __name__ == "__main__":
    display_image()
