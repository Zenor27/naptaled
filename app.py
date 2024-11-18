import asyncio
from collections.abc import Coroutine
from contextlib import asynccontextmanager
from http import HTTPStatus
from importlib import import_module
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.napta_matrix import MATRIX_SCRIPTS

# Import scripts
THIS_DIR = Path(__file__).resolve().parent
for file in sorted(THIS_DIR.glob("src/**/*.py")):
    if file.stem != "__init__":
        module_path = ".".join(file.relative_to(THIS_DIR).parts).removesuffix(".py")
        import_module(module_path)


DEFAULT_PROGRAM = MATRIX_SCRIPTS["display_snow"]()


_main_program_task: asyncio.Task[None]


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _main_program_task
    _main_program_task = asyncio.create_task(
        DEFAULT_PROGRAM, name=DEFAULT_PROGRAM.__name__
    )
    try:
        yield
    finally:
        _main_program_task.cancel()


def switch_program(program: Coroutine[Any, Any, None]) -> None:
    global _main_program_task
    _main_program_task.cancel()
    _main_program_task = asyncio.create_task(program, name=program.__name__)


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class ScriptResponse(BaseModel):
    script_name: str


class GetScriptsResponse(BaseModel):
    scripts: list[str]
    current_script: str


@app.get("/scripts", operation_id="get_scripts")
async def scripts() -> GetScriptsResponse:
    global _main_program_task
    scripts = list(MATRIX_SCRIPTS.keys())
    current_script = _main_program_task.get_name()
    return GetScriptsResponse(scripts=scripts, current_script=current_script)


@app.post("/scripts/change", operation_id="post_change_script")
async def change_script(script: str = Form(...), image: UploadFile | None = File(None)):
    try:
        script_func = MATRIX_SCRIPTS[script]

        # If image is provided, pass it to the script
        if image:
            # Read image content
            image_content = await image.read()
            # Call script with image
            program = script_func(image=image_content)
        else:
            # Call script without image
            program = script_func()

        switch_program(program)
        return "OK"
    except KeyError:
        raise HTTPException(
            HTTPStatus.UNPROCESSABLE_ENTITY, f"Unknown program: {script}"
        )
