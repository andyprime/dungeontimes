from typing import Union
from uuid import UUID
import asyncio
import logging

from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.database import Database

import aio_pika


LOG = logging.getLogger('uvicorn.error')

def db_session():
    client = MongoClient('mongodb://{}:{}@data-store:27017'.format('root', 'devenvironment'))
    db = client.dungeondb
    try:
        yield db
    finally:
        client.close()

async def mq_channel():
    connection = await aio_pika.connect_robust('amqp://guest:guest@rabbit/')
    channel = await connection.channel()
    exchange = await channel.declare_exchange('dungeon', 'fanout', durable=True)
    queue = await channel.declare_queue('dlistener-api', exclusive=True)
    await queue.bind(exchange, routing_key='*')
    try:
        yield queue
    finally:
        LOG.info('----- Channel connection closed')
        await connection.close()

app = FastAPI()

origins = ['http://localhost', 'http://localhost:8081']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Oh": "Hello there"}

@app.get('/delver/')
def read_delvers(db: Database = Depends(db_session)):
    ds = []
    for d in db.delvers.find():
        d.pop('_id')
        ds.append(d)
    return ds

@app.get("/delver/{delver_id}")
def read_delver(delver_id: UUID, db: Database = Depends(db_session)):
    d = db.delvers.find_one({'id': str(delver_id)})
    d.pop('_id')
    return d

@app.get("/dungeon/")
def read_dungeons(db: Database = Depends(db_session)):
    ds = []
    for d in db.dungeons.find():
        d.pop('_id')
        ds.append(d)
    return ds

@app.get("/dungeon/{dungeon_id}")
def read_dungeon(dungeon_id: UUID, db: Database = Depends(db_session)):
    d = db.dungeons.find_one({'id': str(dungeon_id)})
    d.pop('_id')
    return d

@app.get("/expedition/")
def read_expedition(db: Database = Depends(db_session)):
    es = []
    for ex in db.expeditions.find():
        ex.pop('_id')
        es.append(ex)
    return es

@app.get("/expedition/{exp_id}")
def read_expedition(exp_id: UUID, db: Database = Depends(db_session)):
    e = db.expeditions.find_one({'id': str(exp_id)})
    e.pop('_id')
    return e

# stolen blatently from the tutorial
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        LOG.info('!!! Websocket connect.')
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        LOG.info('!!! Websocket disconnect')
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        LOG.info('!!! Websocket broadcast ({})'.format(len(self.active_connections)))
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/feed/dungeon")
async def websocket_endpoint(websocket: WebSocket, queue: aio_pika.Queue = Depends(mq_channel)):
    await manager.connect(websocket)
    try:
        async with queue.iterator() as q:
            async for message in q:
                await manager.broadcast(message.body)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
