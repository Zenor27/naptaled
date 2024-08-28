import asyncio
from collections.abc import Coroutine
from contextlib import asynccontextmanager
from http import HTTPStatus
from importlib import import_module
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.napta_matrix import MATRIX_SCRIPTS

# Import scripts
THIS_DIR = Path(__file__).resolve().parent
for file in sorted(THIS_DIR.glob("src/**/*.py")):
    if file.stem != "__init__":
        module_path = ".".join(file.relative_to(THIS_DIR).parts).removesuffix(".py")
        import_module(module_path)


DEFAULT_PROGRAM = MATRIX_SCRIPTS["display_screensaver"]()


_main_program_task: asyncio.Task[None]


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _main_program_task
    _main_program_task = asyncio.create_task(DEFAULT_PROGRAM, name="default_program")
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


@app.get("/scripts", operation_id="get_scripts")
async def scripts() -> list[str]:
    return list(MATRIX_SCRIPTS.keys())


class ChangeScriptRequest(BaseModel):
    script: str


@app.post("/scripts/change", operation_id="post_change_script")
async def change_script(change_script_request: ChangeScriptRequest):
    try:
        script = MATRIX_SCRIPTS[change_script_request.script]
    except KeyError:
        raise HTTPException(HTTPStatus.UNPROCESSABLE_ENTITY, f"Unknown program: {change_script_request.script}")
    switch_program(script())
    return "OK"
