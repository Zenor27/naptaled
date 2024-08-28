import asyncio
import logging
import os
from collections.abc import Callable, Coroutine
from functools import lru_cache, wraps
from typing import TYPE_CHECKING, Any

from typing_extensions import Concatenate, ParamSpec

from src.helpers.napta_colors import NaptaColor

MATRIX_SIZE = 64


def is_raspberry() -> bool:
    """Check if the current device is the Raspberry Pi."""
    return os.uname().machine == "armv6l"


if is_raspberry() and not TYPE_CHECKING:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
else:
    from RGBMatrixEmulator import (
        RGBMatrix,
        RGBMatrixOptions,
        graphics,
    )  # pyright: ignore[reportMissingTypeStubs]


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


MATRIX_SCRIPTS = dict[
    str, Callable[Concatenate[RGBMatrix, _P], Coroutine[Any, Any, None]]
]()


def matrix_script(
    function: Callable[Concatenate[RGBMatrix, _P], Coroutine[Any, Any, None]],
) -> Callable[_P, Coroutine[Any, Any, None]]:

    @wraps(function)
    async def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> None:
        matrix = _get_matrix()
        matrix.Clear()
        try:
            await function(matrix, *args, **kwargs)
        except Exception:
            from src.display_screensaver import display_screensaver
            from src.helpers.fullscreen_message import fullscreen_message

            logging.exception(
                f"Fatal error in program {function.__name__!r}: ", exc_info=True
            )
            program_name = function.__name__.removeprefix("display_")
            await fullscreen_message(
                matrix,
                [
                    "Fatal error",
                    "in program",
                    program_name,
                    "",
                    "Restarting",
                    "in a few",
                    "seconds...",
                ],
                color=NaptaColor.BITTERSWEET,
            )
            await asyncio.sleep(5)
            await asyncio.create_task(display_screensaver())
            raise

    MATRIX_SCRIPTS[function.__name__] = wrapper

    return wrapper


__all__ = ["RGBMatrix", "RGBMatrixOptions", "graphics", "matrix_script"]
