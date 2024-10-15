from typing import Union

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.database import Database
from uuid import UUID


def db_session():
    client = MongoClient('mongodb://{}:{}@data-store:27017'.format('root', 'devenvironment'))
    db = client.dungeondb
    try:
        yield db
    finally:
        client.close()

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