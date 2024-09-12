import asyncio
import enum
import logging
import os
from collections.abc import Callable, Coroutine
from functools import lru_cache, wraps
from typing import TYPE_CHECKING, Any, NamedTuple, cast

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


class MatrixScript(NamedTuple):
    function: Callable[..., Coroutine[Any, Any, None]]
    script_name: str


class KeyboardKeys(enum.Enum):
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"


class PlayableMatrixScript(NamedTuple):
    function: Callable[..., Coroutine[Any, Any, None]]
    script_name: str
    min_player_number: int
    max_player_number: int
    keys: list[KeyboardKeys]


MATRIX_SCRIPTS = dict[str, MatrixScript | PlayableMatrixScript]()


async def _handle_matrix_script_exception(matrix: RGBMatrix, function_name: str) -> None:
    from src.display_screensaver import display_screensaver
    from src.helpers.fullscreen_message import fullscreen_message

    logging.exception(f"Fatal error in program {function_name!r}: ", exc_info=True)
    program_name = function_name.removeprefix("display_")
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
        color=cast(tuple[int, int, int], NaptaColor.BITTERSWEET),
    )
    await asyncio.sleep(5)
    await asyncio.create_task(display_screensaver())


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
            await _handle_matrix_script_exception(matrix, function.__name__)
            raise

    MATRIX_SCRIPTS[function.__name__] = MatrixScript(
        function=wrapper, script_name=function.__name__.replace("display_", "")
    )

    return wrapper


def playable_matrix_script(*, min_player_number: int, max_player_number: int, keys: list[KeyboardKeys]):
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
                await _handle_matrix_script_exception(matrix, function.__name__)
                raise

        MATRIX_SCRIPTS[function.__name__] = PlayableMatrixScript(
            function=wrapper,
            script_name=function.__name__.replace("display_", ""),
            min_player_number=min_player_number,
            max_player_number=max_player_number,
            keys=keys,
        )

        return wrapper

    return matrix_script


__all__ = [
    "RGBMatrix",
    "RGBMatrixOptions",
    "graphics",
    "matrix_script",
    "playable_matrix_script",
]
