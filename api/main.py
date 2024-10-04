from typing import Union

from fastapi import Depends, FastAPI
from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.database import Database
from uuid import UUID


def dbSession():
    client = MongoClient('mongodb://{}:{}@data-store:27017'.format('root', 'devenvironment'))
    db = client.dungeondb
    try:
        yield db
    finally:
        client.close()

app = FastAPI()


@app.get("/")
def read_root():
    return {"Oh": "Hello there"}

@app.get("/delver/{delver_id}")
def read_delver(delver_id: UUID, db: Database = Depends(dbSession)):
    x = db.delvers.find_one({'id': delver_id})
    x.pop('_id')
    return x

@app.get("/dungeon/")
def read_dungeon(db: Database = Depends(dbSession)):
    ds = []
    for d in db.dungeons.find():
        d.pop('_id')
        ds.append(d)
    return ds

@app.get("/dungeon/{dungeon_id}")
def read_dungeon(dungeon_id: str, db: Database = Depends(dbSession)):
    x = db.dungeons.find_one({'id': dungeon_id})
    x.pop('_id')
    return x

@app.get("/expedition/")
def read_expedition(db: Database = Depends(dbSession)):
    x = db.expeditions.find_one({'id': exp_id})
    x.pop('_id')
    return x

@app.get("/expedition/{exp_id}")
def read_expedition(exp_id: str, db: Database = Depends(dbSession)):
    x = db.expeditions.find_one({'id': exp_id})
    x.pop('_id')
    return x