import random
import time
import uuid
from functools import partial

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from bson import ObjectId
import pika
from pydantic_settings import BaseSettings, SettingsConfigDict

import core
import core.dungeon.generate
import core.expedition
from core.dungeon.dungeons import Dungeon
from core.mdb import MongoService

_advHandlerSettings = {}

def rabbitHandler(channel, message):
    print('$$$$$$$ Emit {}'.format(message))
    channel.basic_publish(exchange='dungeon', routing_key='*', body=message)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    mongo_user: str
    mongo_password: str
    mongo_host: str
    mongo_port: str
    rabbit_user: str
    rabbit_password: str
    rabbit_host: str

if __name__ == "__main__":
    seed = str(uuid.uuid1())
    # seed = ''
    print('Seed: {}'.format(seed))
    random.seed(seed)

    settings = Settings()
    mongo_client = MongoService('mongodb://{}:{}@{}:{}'.format(settings.mongo_user, settings.mongo_password, settings.mongo_host, settings.mongo_port))

    creds = pika.PlainCredentials(settings.rabbit_user, settings.rabbit_password)
    parameters = (pika.ConnectionParameters(host=settings.rabbit_host, credentials=creds))
    print(parameters)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.exchange_declare('dungeon', exchange_type='fanout', durable=True)

    emitFn = partial(rabbitHandler, channel)

    while True:
        print('Demo loop start!')
        print('Destroying any existing entities.')

        print(mongo_client)

        result = mongo_client.db.expeditions.delete_many({})
        result2 = mongo_client.db.dungeons.delete_many({})
        result3 = mongo_client.db.delvers.delete_many({})

        print('Deleted: {}, {}, {}'.format(result.deleted_count, result2.deleted_count, result3.deleted_count))

        # Generate dungeon
        dungeon = core.dungeon.generate.DungeonFactoryAlpha.generateDungeon({
                'DEFAULT_HEIGHT': 10,
                'DEFAULT_WIDTH': 30,
                'ROOM_HEIGHT_RANGE': (3,4),
                'ROOM_WIDTH_RANGE': (3,8),
                'MAX_SPARENESS_RUNS': 5,
                'MAX_ROOM_ATTEMPTS': 100
            })

        # Populate dungeon
        for room in dungeon.rooms:
            for i in range(4):
                room.populate(core.critters.Monster.random())

        did = mongo_client.persist(dungeon)

        print('Generated dungeon')

        # create party
        delvers = []
        ids = []
        for i in range(4):
            d = core.critters.Delver.random()
            delvers.append(d)
            ids.append(mongo_client.persist(d))

        print('Generated delvers')

        e_id = mongo_client.persist_expedition(did, ids, dungeon.entrance().coords)

        print('Saved the expedition')

        dungeon.prettyPrint()
        for room in dungeon.rooms:
            print('{}: {}'.format(dungeon.rooms.index(room), room))
        print(delvers)

        exp = core.expedition.Expedition(dungeon, delvers, None, id=e_id, mdb=mongo_client)
        exp.registerEventEmitter(emitFn)
        exp.emitNew()

        print('Expedition generated, having a little nap')
        time.sleep(30)

        print('Start expedition process')
        while not exp.over():
            t = exp.processTurn()
            time.sleep(t)

        print('Expedition over, having a little nap')
        time.sleep(30)
