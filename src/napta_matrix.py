from collections.abc import Callable
import os


MATRIX_SIZE = 64


def is_raspberry() -> bool:
    """Check if the current device is the Raspberry Pi."""
    return os.uname().machine == 'armv6l'



if is_raspberry():
    from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
else:
    from RGBMatrixEmulator import RGBMatrix, RGBMatrixOptions, graphics



def matrix_script(function: Callable[[RGBMatrix], None]) -> Callable[[], None]:
    def wrapper() -> None:
        options = RGBMatrixOptions()
        options.rows = MATRIX_SIZE
        options.cols = MATRIX_SIZE
        options.chain_length = 1
        options.parallel = 1
        options.hardware_mapping = "regular"

        matrix = RGBMatrix(options=options)

        function(matrix)
    
    return wrapper