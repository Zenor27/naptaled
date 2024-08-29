from collections import defaultdict
from textwrap import dedent

from PIL.ImageDraw import ImageDraw


def pattern_to_points(pattern: str, origin_x: int = 0, origin_y: int = 0) -> list[tuple[int, int]]:
    return [
        (origin_x + x, origin_y + y)
        for y, line in enumerate(dedent(pattern).strip("\n").split("\n"))
        for x, char in enumerate(line)
        if char not in (" ", "⬛")
    ]


def draw_pattern(
    drawer: ImageDraw,
    pattern: str,
    color_map: dict[str, tuple[int, int, int]],
) -> None:
    coords_by_color = defaultdict[tuple[int, int, int], list[tuple[int, int]]](list)
    for y, line in enumerate(dedent(pattern).strip("\n").split("\n")):
        for x, char in enumerate(line):
            if char in (" ", "⬛"):
                continue
            coords_by_color[color_map[char]].append((x, y))

    for color, coords in coords_by_color.items():
        drawer.point(coords, fill=color)
