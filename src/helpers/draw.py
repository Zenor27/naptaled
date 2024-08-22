from collections import defaultdict
from PIL.ImageDraw import ImageDraw
from textwrap import dedent


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
