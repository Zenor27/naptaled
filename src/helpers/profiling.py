import contextlib
from typing import Iterator, Optional

try:
    import pyinstrument
except ModuleNotFoundError:
    pyinstrument = None


@contextlib.contextmanager
def sampling_profile(
    *,
    disabled: bool = False,
    dump_file: Optional[str] = None,
    interval_ms: float = 1,
) -> Iterator[None]:
    """Context manager / decorator to profile a block of code using sampling.

    Sampling is less accurate than instrumenting all function calls, but has less overhead than instrumenting all
    function calls.

    Args:
        disabled: Do not run the profiler.
        dump_file: Dump the stats to the given file. If None, browser will be opened.
        interval_ms: The interval in milliseconds at which to sample the stack. Note that very low intervals (sub millisecond) tend to have higher overhead, but they can yield more detailed profiles.

    Examples:
        >>> with naptx.sampling_profile():
        ...     do_something()
        ...
        >>> @naptx.sampling_profile
        ... def some_func():
        ...     do_something()
    """
    assert pyinstrument is not None, "pyinstrument is not installed"
    if disabled:
        yield
        return

    profiler = pyinstrument.Profiler(interval=interval_ms / 1000)
    profiler.start()
    yield
    profiler.stop()
    if dump_file:
        profiler.write_html(dump_file)
        print(f"Profile has been written to {dump_file}")
    else:
        profiler.open_in_browser()
