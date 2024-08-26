import asyncio

from src.helpers.control import connect_to_server

if __name__ == "__main__":
    asyncio.run(connect_to_server())
