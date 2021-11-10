import asyncio

from fastapi.websockets import WebSocket
from websockets.exceptions import ConnectionClosedOK

import utils


def update_websocket(data_func):
    async def handle_websocket(websocket: WebSocket):
        await websocket.accept()
        message_task = None
        db_task = None

        while True:
            try:
                await websocket.send_json(data_func())

                if message_task is None:
                    message_task = asyncio.create_task(websocket.receive())
                if db_task is None:
                    db_task = asyncio.create_task(utils.wait_for_db_update())

                # Timeout so we don't wait infinitely
                timeout_task = asyncio.create_task(asyncio.sleep(5))

                # Wait for next update call from client or next db update
                done, pending = await asyncio.wait(
                    [message_task, db_task, timeout_task],
                    return_when=asyncio.FIRST_COMPLETED)

                # Reset tasks if it is done to spawn again in next loop
                if message_task in done:
                    message_task = None
                if db_task in done:
                    db_task = None
            except (ConnectionClosedOK, RuntimeError):
                break

    return handle_websocket
