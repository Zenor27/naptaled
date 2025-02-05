from src.play_2048.algorithm import _find_moves, _shift


def _test_shift(
    initial: tuple[int, ...], expected: tuple[int, ...], expected_moves: set[tuple[int, int, bool]]
) -> None:
    assert sum(initial) == sum(expected), "error in test case, cannot be true..."
    result = _shift(*initial)
    assert result == expected, f"_shift{initial} -> {result} != {expected} (as expected)"
    moves = set(_find_moves(result, initial))
    assert moves == expected_moves, f"_find_moves({result}, {initial}) -> {moves} != {expected_moves} (as expected)"


_test_shift((0, 0, 0, 0), (0, 0, 0, 0), set())
_test_shift((0, 0, 0, 2), (2, 0, 0, 0), {(3, 0, False)})
_test_shift((0, 0, 2, 0), (2, 0, 0, 0), {(2, 0, False)})
_test_shift((0, 0, 2, 2), (4, 0, 0, 0), {(2, 0, False), (3, 0, True)})
_test_shift((0, 0, 2, 4), (2, 4, 0, 0), {(2, 0, False), (3, 1, False)})
_test_shift((0, 0, 4, 2), (4, 2, 0, 0), {(2, 0, False), (3, 1, False)})
_test_shift((0, 2, 0, 0), (2, 0, 0, 0), {(1, 0, False)})
_test_shift((0, 2, 0, 2), (4, 0, 0, 0), {(1, 0, False), (3, 0, True)})
_test_shift((0, 2, 0, 4), (2, 4, 0, 0), {(1, 0, False), (3, 1, False)})
_test_shift((0, 2, 2, 0), (4, 0, 0, 0), {(1, 0, False), (2, 0, True)})
_test_shift((0, 2, 2, 2), (4, 2, 0, 0), {(1, 0, False), (2, 0, True), (3, 1, False)})
_test_shift((0, 2, 2, 4), (4, 4, 0, 0), {(1, 0, False), (2, 0, True), (3, 1, False)})
_test_shift((0, 2, 4, 0), (2, 4, 0, 0), {(1, 0, False), (2, 1, False)})
_test_shift((0, 2, 4, 4), (2, 8, 0, 0), {(1, 0, False), (2, 1, False), (3, 1, True)})
_test_shift((0, 4, 0, 2), (4, 2, 0, 0), {(1, 0, False), (3, 1, False)})
_test_shift((2, 0, 0, 0), (2, 0, 0, 0), set())
_test_shift((2, 0, 0, 2), (4, 0, 0, 0), {(3, 0, True)})
_test_shift((2, 0, 2, 0), (4, 0, 0, 0), {(2, 0, True)})
_test_shift((2, 0, 2, 2), (4, 2, 0, 0), {(2, 0, True), (3, 1, False)})
_test_shift((2, 2, 2, 2), (4, 4, 0, 0), {(1, 0, True), (2, 1, False), (3, 1, True)})
_test_shift((2, 4, 2, 2), (2, 4, 4, 0), {(3, 2, True)})
_test_shift((2, 4, 2, 4), (2, 4, 2, 4), set())
_test_shift((2, 4, 4, 2), (2, 8, 2, 0), {(2, 1, True), (3, 2, False)})
_test_shift((4, 0, 0, 2), (4, 2, 0, 0), {(3, 1, False)})
_test_shift((4, 2, 0, 2), (4, 4, 0, 0), {(3, 1, True)})
_test_shift((4, 2, 2, 2), (4, 4, 2, 0), {(2, 1, True), (3, 2, False)})
_test_shift((4, 4, 0, 2), (8, 2, 0, 0), {(1, 0, True), (3, 1, False)})
_test_shift((4, 4, 2, 2), (8, 4, 0, 0), {(1, 0, True), (2, 1, False), (3, 1, True)})
