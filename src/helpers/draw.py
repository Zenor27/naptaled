from collections import defaultdict
from textwrap import dedent
from typing import Iterator

from PIL.ImageDraw import ImageDraw


def pattern_to_points(pattern: str, origin_x: int = 0, origin_y: int = 0) -> list[tuple[int, int]]:
    return [
        (origin_x + x, origin_y + y)
        for y, line in enumerate(dedent(pattern).strip("\n").split("\n"))
        for x, char in enumerate(line)
        if char not in (" ", "⬛")
    ]


def _parse_pattern(pattern: str) -> Iterator[tuple[int, int, str]]:
    for y, line in enumerate(dedent(pattern).strip("\n").split("\n")):
        for x, char in enumerate(line):
            yield y, x, char


def pattern_to_color_by_point(
    pattern: str,
    color_map: dict[str, tuple[int, int, int]],
    origin_x: int = 0,
    origin_y: int = 0,
) -> dict[tuple[int, int], tuple[int, int, int]]:
    return {(origin_x + x, origin_y + y): color_map[char] for y, x, char in _parse_pattern(pattern)}


def draw_pattern(
    drawer: ImageDraw,
    pattern: str,
    color_map: dict[str, tuple[int, int, int]],
    origin_x: int = 0,
    origin_y: int = 0,
) -> None:
    coords_by_color = defaultdict[tuple[int, int, int], list[tuple[int, int]]](list)
    for y, x, char in _parse_pattern(pattern):
        if char in (" ", "⬛"):
            continue
        coords_by_color[color_map[char]].append((origin_x + x, origin_y + y))

    for color, coords in coords_by_color.items():
        drawer.point(coords, fill=color)
