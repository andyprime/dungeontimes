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

class RabbitQueue:
    def __new__(cls, *args):
        if not hasattr(cls, 'instance'):
            cls.instance = super(RabbitQueue, cls).__new__(cls)
        return cls.instance

    def __init__(self, host=None):
        if host:
            self.host = host

    async def connect(self):
        self.connection = await aio_pika.connect_robust(self.host)
        self.channel = await self.connection.channel() 
        # we really shouldn't be declaring the exchange in here in the future but right now it helps manage order issues
        self.exchange = await self.channel.declare_exchange('dungeon', 'fanout', durable=True)
        self.queue = await self.channel.declare_queue('dlistener-api', exclusive=True)
        await self.queue.bind(self.exchange, routing_key='*')

    def get_queue(self):
        return self.queue
        
    async def close(self):
        await self.connection.close()

async def mq_channel():
    LOG.info('!!!!! Closing rabbit connection')
    return RabbitQueue().get_queue()

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
    x = 'mongodb://{}:{}@{}:{}'.format(settings.mongo_user, settings.mongo_password, settings.mongo_host, settings.mongo_port)
    print('!!!!!!! {}'.format(x))
    client = MongoClient(x)
    db = client.dungeondb
    try:
        yield db
    finally:
        client.close()

@app.on_event("startup")
async def startup_event():
    q = RabbitQueue('amqp://{}:{}@{}/'.format(settings.rabbit_user, settings.rabbit_password, settings.rabbit_host))
    await q.connect()

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
        LOG.info('!!! Websocket connect: {}.'.format(websocket))
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        LOG.info('!!! Websocket disconnect {}'.format(websocket))
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        LOG.info('!!! Websocket broadcasting {} to ({}) connections'.format(message, len(self.active_connections)))
        for connection in self.active_connections:
            if connection.application_state == WebSocketState.DISCONNECTED:
                LOG.info('Skipping disconnected websocket {}'.format(connection))
            else:
                await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/feed/dungeon")
async def websocket_endpoint(websocket: WebSocket, queue: aio_pika.Queue = Depends(mq_channel)):
    await manager.connect(websocket)
    try:
        # the main listener loop should maybe be somewhere it doesn't get run for each socket but seems to be ok atm
        async with queue.iterator() as q:
            async for message in q:
                await manager.broadcast(message.body)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
