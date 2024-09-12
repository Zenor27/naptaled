import asyncio
import logging
from collections.abc import AsyncIterator, Awaitable, Collection
from contextlib import asynccontextmanager
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

SERVER_PORT = 4422

RDY = b"RDY\n"
WAIT = b"WAIT\n"
WRONG = b"WRG\n"


class ControlServer:
    def __init__(self, *, min_clients: int) -> None:
        self.clients = dict[str, asyncio.StreamReader]()
        self.min_clients = min_clients

    def can_start(self) -> bool:
        return len(self.clients) >= self.min_clients


@asynccontextmanager
async def control_server(
    client_names: Collection[str],
    min_clients: Optional[int] = None,
    on_started: Optional[Awaitable[None]] = None,
) -> AsyncIterator[ControlServer]:
    if min_clients is None:
        min_clients = len(client_names)

    _client_names = [name.encode() for name in client_names]
    server = ControlServer(min_clients=min_clients)

    async def client_connected(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        if len(client_names) == 1:
            [client_name] = client_names
        else:
            while True:
                proposal = (await reader.readuntil(b"\n")).strip()
                if proposal in _client_names:
                    client_name = proposal.decode()
                    break
                writer.write(WRONG)

        server.clients[client_name] = reader

        if server.can_start():
            writer.write(RDY)
        else:
            writer.write(WAIT)
        await writer.drain()

    logger.info(f"Creating TCP server on port {SERVER_PORT}...")
    async with await asyncio.start_server(client_connected, host="0.0.0.0", port=SERVER_PORT):
        if on_started:
            await on_started
        while not server.can_start():
            await asyncio.sleep(1)

        yield server
