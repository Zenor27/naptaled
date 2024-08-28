import asyncio
import logging
from collections.abc import AsyncIterator, Awaitable
from contextlib import asynccontextmanager

from src.helpers import ainput

SERVER_PORT = 4422

INP = b"INP\n"
RDY = b"RDY\n"

class ControlServer:
    def __init__(self) -> None:
        self.clients = dict[str, asyncio.StreamReader]()


@asynccontextmanager
async def control_server(client_names: list[str], on_started: Awaitable[None]) -> AsyncIterator[ControlServer]:
    _client_names = [name.encode() for name in client_names]
    server = ControlServer()

    async def client_connected(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        if len(client_names) == 1:
            client_name = client_names[0]
        else:
            while True:
                writer.write(b"Who are you? (choices: %s)\n" % b", ".join(_client_names))
                writer.write(INP)
                await writer.drain()
                proposal = (await reader.readuntil(b"\n")).strip()
                if proposal in _client_names:
                    client_name = proposal.decode()
                    break
                writer.write(b"Wrong answer...\n\n")

        writer.write(RDY)
        await writer.drain()
        server.clients[client_name] = reader

    logging.info(f"Creating TCP server on port {SERVER_PORT}...")
    async with await asyncio.start_server(client_connected, host="0.0.0.0", port=SERVER_PORT):
        logging.info("Server ready!")
        await on_started
        while len(server.clients) < len(client_names):
            await asyncio.sleep(1)

        yield server


async def connect_to_server() -> None:
    print("Connecting...")
    reader, writer = await asyncio.open_connection(host="127.0.0.1", port=SERVER_PORT)
    print("Connected!")
    while True:
        message = await reader.readuntil(b"\n")
        if message == RDY:
            break
        elif message == INP:
            inp = input(">>> ")
            writer.write(inp.encode() + b"\n")
            await writer.drain()
        else:
            print(message.decode(), end="")

    print("Ready!")

    with ainput.capture_terminal() as get_input:
        while True:
            if input_ := get_input():
                writer.write(input_)
            await asyncio.sleep(0.01)
