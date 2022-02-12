import asyncio

from fastapi.websockets import WebSocket
from websockets.exceptions import ConnectionClosedOK

import utils


def update_websocket(data_func):
    async def handle_websocket(websocket: WebSocket):
        try:
            await websocket.accept()
            message_task = None
            db_task = None
            last_updated = None

            while True:
                await websocket.send_json(data_func())

                if message_task is None:
                    message_task = asyncio.ensure_future(websocket.receive())
                if db_task is None:
                    db_task = asyncio.ensure_future(
                        utils.wait_for_db_update(last_updated))

                # Wait for next update call from client or next db update
                done, pending = await asyncio.wait(
                    [message_task, db_task], timeout=5,
                    return_when=asyncio.FIRST_COMPLETED)

                # Reset tasks if it is done to spawn again in next loop
                if message_task in done:
                    message_task = None
                if db_task in done:
                    last_updated = await db_task
                    db_task = None
        except (ConnectionClosedOK, RuntimeError):
            pass

    return handle_websocket
