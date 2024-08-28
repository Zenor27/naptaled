import asyncio
from collections.abc import Coroutine
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from src.display_pong import display_pong
from src.display_random_restaurant import display_random_restaurant
from src.display_screensaver import display_screensaver
from src.display_snake import display_snake
from src.display_text import display_text
from src.display_train import display_train
from src.display_whos_that_pokemon import display_whos_that_pokemon

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


@app.get("/screensaver")
async def run_screensaver():
    switch_program(display_screensaver())
    return "OK"


@app.get("/train")
async def run_train():
    switch_program(display_train())
    return "OK"


@app.get("/snake")
async def run_snake():
    switch_program(display_snake())
    return "OK"


@app.get("/wtp")
async def run_wtp():
    switch_program(display_whos_that_pokemon())
    return "OK"


@app.get("/text")
async def run_text(text: str):
    switch_program(display_text(text))
    return "OK"


@app.get("/random_restaurant")
async def run_random_restaurant():
    switch_program(display_random_restaurant())
    return "OK"


@app.get("/pong")
async def run_pong():
    switch_program(display_pong())
    return "OK"
