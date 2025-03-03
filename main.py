import asyncio
from websockets.asyncio.server import serve, ServerConnection
import ssl
import logging


async def on_client_connect(websocket: ServerConnection) -> None:
    await asyncio.sleep(5)
    await websocket.send(b"Hello")
    logging.info("Message sent")
    await websocket.close()


async def main():
    async with serve(on_client_connect, "localhost", 8080) as server:
        await server.serve_forever()


def get_ssl_context():
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain("./certs/raspi001.cert.pem", "./certs/raspi001.key.pem")
    return ssl_context


if __name__ == "__main__":
    asyncio.run(main())
