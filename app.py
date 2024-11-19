import asyncio
from collections.abc import Coroutine
from contextlib import asynccontextmanager
from http import HTTPStatus
from importlib import import_module
from pathlib import Path
from typing import Any, Union
from dataclasses import dataclass

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


DEFAULT_PROGRAM = MATRIX_SCRIPTS["display_screensaver"]()


@dataclass
class ScriptState:
    name: str
    image_content: Union[bytes, None] = None
    task: Union[asyncio.Task, None] = None


class ScriptManager:
    def __init__(self, default_script: str):
        self.previous_state: Union[ScriptState, None] = None
        self.current_state: ScriptState = ScriptState(name=default_script)

    def switch_to(self, new_state: ScriptState) -> None:
        # Cancel current task if it exists
        if self.current_state and self.current_state.task:
            self.current_state.task.cancel()

        # Store current as previous, and set new as current
        self.previous_state = self.current_state
        self.current_state = new_state

    def can_undo(self) -> bool:
        return self.previous_state is not None

    def undo(self) -> Union[ScriptState, None]:
        if not self.can_undo():
            return None

        # Cancel current task
        if self.current_state.task:
            self.current_state.task.cancel()

        # Swap current and previous
        temp = self.current_state
        self.current_state = self.previous_state
        self.previous_state = temp

        return self.current_state


# Initialize script manager with default script
script_manager = ScriptManager("display_screensaver")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Initialize with default program
    script_state = ScriptState(
        name="display_screensaver",
        task=asyncio.create_task(DEFAULT_PROGRAM, name=DEFAULT_PROGRAM.__name__),
    )
    script_manager.switch_to(script_state)
    try:
        yield
    finally:
        if script_manager.current_state.task:
            script_manager.current_state.task.cancel()


def switch_program(program: Coroutine[Any, Any, None], name: str) -> None:
    task = asyncio.create_task(program, name=name)
    script_manager.current_state.task = task


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
    scripts: list[dict[str, Any]]
    current_script: str


@app.get("/scripts", operation_id="get_scripts")
async def scripts() -> GetScriptsResponse:
    # Get information about each script
    scripts_info = [
        {
            "name": script_name,
            "requires_image": script_name in ["display_choose_image"],
        }
        for script_name in MATRIX_SCRIPTS.keys()
    ]

    # Get current script from script_manager instead of _main_program_task
    current_script = script_manager.current_state.name
    return GetScriptsResponse(scripts=scripts_info, current_script=current_script)


@app.post("/scripts/change", operation_id="post_change_script")
async def change_script(
    script: str = Form(...),
    image: Union[UploadFile, None] = File(None),
):
    try:
        script_func = MATRIX_SCRIPTS[script]
        image_content = None

        if image:
            image_content = await image.read()
            program = script_func(image=image_content)
        else:
            program = script_func()

        script_state = ScriptState(name=script, image_content=image_content)
        script_manager.switch_to(script_state)
        switch_program(program, script)
        return "OK"
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=f"Error processing request: {str(e)}",
        )


@app.post("/scripts/undo", operation_id="post_undo_script")
async def undo_script():
    try:
        previous_state = script_manager.undo()
        if not previous_state:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="No previous script to undo to",
            )

        script_func = MATRIX_SCRIPTS[previous_state.name]
        if previous_state.image_content:
            program = script_func(image=previous_state.image_content)
        else:
            program = script_func()

        switch_program(program, previous_state.name)
        return "OK"
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=f"Error processing request: {str(e)}",
        )
