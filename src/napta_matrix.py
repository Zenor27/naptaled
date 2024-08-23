import os
from collections.abc import Callable, Coroutine
from typing import TYPE_CHECKING, Any

MATRIX_SIZE = 64


def is_raspberry() -> bool:
    """Check if the current device is the Raspberry Pi."""
    return os.uname().machine == "armv6l"


if is_raspberry() and not TYPE_CHECKING:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
else:
    from RGBMatrixEmulator import RGBMatrix, RGBMatrixOptions, graphics  # pyright: ignore[reportMissingTypeStubs]


def matrix_script(
    function: Callable[[RGBMatrix], Coroutine[Any, Any, None]],
) -> Callable[[], Coroutine[Any, Any, None]]:
    async def wrapper() -> None:
        options = RGBMatrixOptions()
        options.rows = MATRIX_SIZE
        options.cols = MATRIX_SIZE
        options.chain_length = 1
        options.parallel = 1
        options.hardware_mapping = "regular"

        matrix = RGBMatrix(options=options)

        await function(matrix)

    return wrapper


__all__ = ["RGBMatrix", "RGBMatrixOptions", "graphics", "matrix_script"]
