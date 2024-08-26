import os
from collections.abc import Callable, Coroutine
from functools import lru_cache, wraps
from typing import TYPE_CHECKING, Any

from typing_extensions import Concatenate, ParamSpec

MATRIX_SIZE = 64


def is_raspberry() -> bool:
    """Check if the current device is the Raspberry Pi."""
    return os.uname().machine == "armv6l"


if is_raspberry() and not TYPE_CHECKING:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
else:
    from RGBMatrixEmulator import RGBMatrix, RGBMatrixOptions, graphics  # pyright: ignore[reportMissingTypeStubs]


_P = ParamSpec("_P")


@lru_cache(maxsize=1)
def _get_matrix() -> RGBMatrix:
    options = RGBMatrixOptions()
    options.rows = MATRIX_SIZE
    options.cols = MATRIX_SIZE
    options.chain_length = 1
    options.parallel = 1
    options.hardware_mapping = "regular"

    return RGBMatrix(options=options)


def matrix_script(
    function: Callable[Concatenate[RGBMatrix, _P], Coroutine[Any, Any, None]],
) -> Callable[_P, Coroutine[Any, Any, None]]:
    @wraps(function)
    async def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> None:
        matrix = _get_matrix()
        matrix.Clear()

        await function(matrix, *args, **kwargs)

    return wrapper


__all__ = ["RGBMatrix", "RGBMatrixOptions", "graphics", "matrix_script"]
