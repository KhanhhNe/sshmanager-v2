import json
import logging
import traceback
from datetime import datetime
from typing import Type

import pendulum
from fastapi.websockets import WebSocket
from fastapi.websockets import WebSocketDisconnect
from pony import orm
from pony.orm.core import db_session
from pydantic import BaseModel

from models import Model

logger = logging.getLogger('Websockets')


def websocket_auto_update_endpoint(entity: Type[Model], output_model: Type[BaseModel]):
    async def handle_websocket(websocket: WebSocket):
        try:
            await websocket.accept()

            while True:
                message = await websocket.receive_json()
                query = entity.select()

                if message.get('last_modified'):
                    parsed_time = pendulum.parse(message['last_modified'],
                                                 tz=pendulum.tz.get_local_timezone())
                    last_modified = datetime.fromtimestamp(parsed_time.timestamp())
                    query = query.filter(lambda obj: obj.last_modified >= last_modified)
                else:
                    last_modified = None

                with db_session:
                    objects = [obj for obj in query[:].to_list()
                               if last_modified is None or (
                                       obj.last_modified > last_modified or
                                       obj.id not in message.get('ids', [])
                               )]
                    # noinspection PyTypeChecker
                    object_ids = orm.select(obj.id for obj in entity)[:].to_list()
                    output_objects = [output_model.from_orm(obj).dict() for obj in objects]

                if objects:
                    last_modified = max(objects, key=lambda obj: obj.last_modified).last_modified
                if message.get('ids'):
                    removed = [object_id
                               for object_id in message['ids']
                               if object_id not in object_ids]
                else:
                    removed = []

                await websocket.send_text(json.dumps({
                    'last_modified': last_modified,
                    'objects': output_objects,
                    'removed': removed
                }, default=str))
        except WebSocketDisconnect:
            pass
        except Exception:
            logger.error(traceback.format_exc())
            raise

    return handle_websocket
