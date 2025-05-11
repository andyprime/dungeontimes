from typing import Union
from uuid import UUID
import asyncio
import logging

from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.websockets import WebSocketState

from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.database import Database
from pydantic_settings import BaseSettings

import aio_pika


LOG = logging.getLogger('uvicorn.error')

class Settings(BaseSettings):
    api_origins: str = ''
    mongo_user: str
    mongo_password: str
    mongo_host: str
    mongo_port: str
    rabbit_user: str
    rabbit_password: str
    rabbit_host: str

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def initialize(self, host: str):
        self.rmq_connection = await aio_pika.connect_robust(host)

        self.channel = await self.rmq_connection.channel() 
        self.exchange = await self.channel.declare_exchange('dungeon', 'fanout', durable=True)
        self.queue = await self.channel.declare_queue('dlistener-api', exclusive=True)
        await self.queue.bind(self.exchange, routing_key='*')
        await self.queue.consume(self.broadcast)

    async def connect(self, websocket: WebSocket):
        LOG.info('!!! Websocket connect: {}.'.format(websocket))
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        LOG.info('!!! Websocket disconnect {}'.format(websocket))
        self.active_connections.remove(websocket)

    async def broadcast(self, message: aio_pika.IncomingMessage):
        LOG.info('!!! Websocket broadcasting {} to ({}) connections'.format(message.body, len(self.active_connections)))
        for connection in self.active_connections:
            if connection.application_state == WebSocketState.DISCONNECTED:
                LOG.info('Skipping disconnected websocket {}'.format(connection))
            else:
                await connection.send_text(message.body)

manager = ConnectionManager()
settings = Settings()
app = FastAPI()

origins = settings.api_origins.split(',')

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def db_session():
    client = MongoClient('mongodb://{}:{}@{}:{}'.format(settings.mongo_user, settings.mongo_password, settings.mongo_host, settings.mongo_port))
    db = client.dungeondb
    try:
        yield db
    finally:
        client.close()

@app.on_event("startup")
async def startup_event():
    await manager.initialize('amqp://{}:{}@{}/'.format(settings.rabbit_user, settings.rabbit_password, settings.rabbit_host))

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

@app.get("/expeditions/")
def read_active_expedition(db: Database = Depends(db_session)):
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

@app.get("/expedition/{exp_id}/delvers")
def read_expedition_delvers(exp_id: UUID, db: Database = Depends(db_session)):
    exp = db.expeditions.find_one({'id': str(exp_id)})
    delvers = list(db.delvers.find({'id': {'$in': exp['party']}}))
    for d in delvers:
        d.pop('_id')

    return delvers

@app.websocket("/feed/dungeon")
# async def websocket_endpoint(websocket: WebSocket, queue: aio_pika.Queue = Depends(mq_channel)):
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # the client isn't currently sending us anything but this is the correct move
            data = await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket)
