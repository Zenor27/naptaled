import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from src.helpers import ainput

SOCKET_NAME = "naptaled_control"


class ControlServer:
    def __init__(self) -> None:
        self.clients = list[asyncio.StreamReader]()


@asynccontextmanager
async def control_server(n_clients: int) -> AsyncIterator[ControlServer]:
    server = ControlServer()

    def client_connected(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        server.clients.append(reader)

    async with await asyncio.start_unix_server(client_connected, SOCKET_NAME):
        while len(server.clients) < n_clients:
            await asyncio.sleep(1)

        yield server


async def connect_to_server() -> None:
    print("Connecting...")
    reader, writer = await asyncio.open_unix_connection(SOCKET_NAME)
    print("Connected!")

    with ainput.capture_terminal() as get_input:
        while True:
            if input := get_input():
                writer.write(input)
            await asyncio.sleep(0.01)
