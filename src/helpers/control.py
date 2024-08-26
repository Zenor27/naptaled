import asyncio
import logging
from collections.abc import AsyncIterator, Awaitable
from contextlib import asynccontextmanager

from src.helpers import ainput

SERVER_PORT = 4422


class ControlServer:
    def __init__(self) -> None:
        self.clients = list[asyncio.StreamReader]()


@asynccontextmanager
async def control_server(n_clients: int, on_started: Awaitable[None]) -> AsyncIterator[ControlServer]:
    server = ControlServer()

    def client_connected(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        server.clients.append(reader)

    logging.info(f"Creating TCP server on port {SERVER_PORT}...")
    async with await asyncio.start_server(client_connected, host="0.0.0.0", port=SERVER_PORT):
        logging.info("Server ready!")
        await on_started
        while len(server.clients) < n_clients:
            await asyncio.sleep(1)

        yield server


async def connect_to_server() -> None:
    print("Connecting...")
    reader, writer = await asyncio.open_connection(host="192.168.128.175", port=SERVER_PORT)
    print("Connected!")

    with ainput.capture_terminal() as get_input:
        while True:
            if input := get_input():
                writer.write(input)
            await asyncio.sleep(0.01)
