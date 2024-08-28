import asyncio
from collections.abc import Coroutine
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from src.display_screensaver import display_screensaver
from src.napta_matrix import MATRIX_SCRIPTS
from pydantic import BaseModel


from fastapi.middleware.cors import CORSMiddleware


DEFAULT_PROGRAM = display_screensaver()


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
    script = MATRIX_SCRIPTS[change_script_request.script]
    switch_program(script())
    return "OK"
