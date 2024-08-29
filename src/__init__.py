from importlib import import_module
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
for file in sorted(CURRENT_DIR.glob("*.py")):
    if file.stem != "__init__":
        module_path = ".".join(file.relative_to(CURRENT_DIR).parts).removesuffix(".py")
        import_module(f".{module_path}", __package__)
