import asyncio
from collections.abc import Coroutine
from contextlib import asynccontextmanager
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.helpers.control import RDY, SERVER_PORT, WAIT
from src.napta_matrix import MATRIX_SCRIPTS, PlayableMatrixScript

DEFAULT_PROGRAM = MATRIX_SCRIPTS["display_screensaver"].function()


_main_program_task: asyncio.Task[None]


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _main_program_task
    _main_program_task = asyncio.create_task(DEFAULT_PROGRAM, name=DEFAULT_PROGRAM.__name__)
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
    script_id: str
    script_name: str
    is_playable: bool


class GetScriptsResponse(BaseModel):
    scripts: list[ScriptResponse]
    current_script: ScriptResponse


@app.get("/scripts", operation_id="get_scripts")
async def scripts() -> GetScriptsResponse:
    global _main_program_task
    scripts = [
        ScriptResponse(
            script_id=script_name,
            script_name=script.script_name,
            is_playable=isinstance(script, PlayableMatrixScript),
        )
        for script_name, script in MATRIX_SCRIPTS.items()
    ]
    current_script = MATRIX_SCRIPTS[_main_program_task.get_name()]
    return GetScriptsResponse(
        scripts=scripts,
        current_script=ScriptResponse(
            script_id=_main_program_task.get_name(),
            script_name=current_script.script_name,
            is_playable=isinstance(current_script, PlayableMatrixScript),
        ),
    )


class ChangeScriptRequest(BaseModel):
    script_id: str


@app.post("/scripts/change", operation_id="post_change_script")
async def change_script(change_script_request: ChangeScriptRequest) -> None:
    try:
        script = MATRIX_SCRIPTS[change_script_request.script_id].function
    except KeyError:
        raise HTTPException(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            f"Unknown program: {change_script_request.script_id}",
        )
    switch_program(script())


class PlayableScriptResponse(BaseModel):
    script_id: str
    script_name: str
    min_player_number: int
    max_player_number: int
    keys: list[str]


@app.get("/scripts/playable/{script_id}", operation_id="get_playable_script")
async def playable_script(script_id: str) -> PlayableScriptResponse:
    try:
        script = MATRIX_SCRIPTS[script_id]
    except KeyError:
        raise HTTPException(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            f"Unknown program: {script_id}",
        )

    if not isinstance(script, PlayableMatrixScript):
        raise HTTPException(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            f"Program {script_id} is not a playable program",
        )

    return PlayableScriptResponse(
        script_id=script_id,
        script_name=script.script_name,
        min_player_number=script.min_player_number,
        max_player_number=script.max_player_number,
        keys=[key.value for key in script.keys],
    )


async def _handle_choose_player(
    data: dict, websocket: WebSocket, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
) -> None:
    player_number = data.get("data", {}).get("player_number", None)
    if player_number is None:
        await websocket.send_json({"error": "Missing player number"})
        return

    writer.write(f"P{player_number}".encode() + b"\n")
    await writer.drain()
    message = await reader.readuntil(b"\n")
    if message == RDY:
        await websocket.send_json({"type": "status", "data": "READY"})
    elif message == WAIT:
        await websocket.send_json({"type": "status", "data": "WAITING"})
    else:
        await websocket.send_json({"type": "error", "data": "Unknown message"})


async def _handle_key(data: dict, websocket: WebSocket, writer: asyncio.StreamWriter) -> None:
    key = data.get("data", {}).get("key", None)
    if key is None:
        await websocket.send_json({"type": "error", "data": "Missing key"})
        return

    if key == "UP":
        key = "\x1b[A"
    elif key == "DOWN":
        key = "\x1b[B"
    elif key == "LEFT":
        key = "\x1b[D"
    elif key == "RIGHT":
        key = "\x1b[C"
    else:
        await websocket.send_json({"type": "error", "data": "Unknown key"})
        return

    writer.write(key.encode())


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    reader, writer = await asyncio.open_connection(host="localhost", port=SERVER_PORT)

    await websocket.accept()
    while True:
        data = await websocket.receive_json()
        if data.get("type") == "choose_player":
            await _handle_choose_player(data, websocket, reader, writer)
        elif data.get("type") == "key":
            await _handle_key(data, websocket, writer)
        else:
            await websocket.send_json({"type": "error", "data": "Unknown message"})
