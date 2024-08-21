import os


def is_raspberry() -> bool:
    """Check if the current device is the Raspberry Pi."""
    return os.uname().machine == 'armv6l'

if is_raspberry():
    from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
else:
    from RGBMatrixEmulator import RGBMatrix, RGBMatrixOptions, graphics

