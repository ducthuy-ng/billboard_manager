import asyncio
import pathlib
import ssl
import logging

from websockets.asyncio.client import connect


async def main():
    async with connect("ws://localhost:8080") as connection:
        await asyncio.sleep(2)
        response = await connection.recv(decode=True)
        logging.info("Receive: %s", response)

        await asyncio.sleep(2)


def get_ssl_context():
    ssl_path = pathlib.Path(__file__).parent / "certs" / "raspi001.cert.pem"
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.load_verify_locations(ssl_path)
    return ssl_context


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
