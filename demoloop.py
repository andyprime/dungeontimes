import random
import time
import uuid
from functools import partial, reduce

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

def buildExpedition(mongo_client):
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

        print('Saved the expedition: {}'.format(e_id))

        dungeon.prettyPrint()
        for room in dungeon.rooms:
            print('{}: {}'.format(dungeon.rooms.index(room), room))
        print(delvers)

        return core.expedition.Expedition(dungeon, delvers, None, id=e_id, mdb=mongo_client)

def all_done(es):
    for x in es.values():
        if not x['ex'].over():
            return False
    return True

if __name__ == "__main__":
    seed = str(uuid.uuid1())
    # seed = ''
    print('Seed: {}'.format(seed))
    random.seed(seed)

    settings = Settings()
    #mongo_client = MongoService('mongodb://{}:{}@{}:{}'.format(settings.mongo_user, settings.mongo_password, settings.mongo_host, settings.mongo_port))
    mongo_client = MongoService('mongodb://{}:{}@{}:{}'.format(settings.mongo_user, settings.mongo_password, 'localhost', settings.mongo_port))

    creds = pika.PlainCredentials(settings.rabbit_user, settings.rabbit_password)
    #parameters = (pika.ConnectionParameters(host=settings.rabbit_host, credentials=creds))
    parameters = (pika.ConnectionParameters(host='localhost', credentials=creds))
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.exchange_declare('dungeon', exchange_type='fanout', durable=True)

    emitFn = partial(rabbitHandler, channel)

    while True:
        print('Demo loop start!')
        print('Destroying any existing entities.')

        result = mongo_client.db.expeditions.delete_many({})
        result2 = mongo_client.db.dungeons.delete_many({})
        result3 = mongo_client.db.delvers.delete_many({})

        print('Deleted: {}, {}, {}'.format(result.deleted_count, result2.deleted_count, result3.deleted_count))

        expeditions = {}
        exp1 = buildExpedition(mongo_client) 
        expeditions[exp1.id] = {'ex': exp1, 'time': 2}

        exp2 = buildExpedition(mongo_client)
        expeditions[exp2.id] = {'ex': exp2, 'time': 3}

        for ex in expeditions.values():
            exchange_name = ex['ex'].id
            print('Declaring: {}'.format(exchange_name))
            ex['ex'].registerEventEmitter(emitFn)
            ex['ex'].emitNew()

        print('Expedition(s) generated, having a little nap')
        print(expeditions)
        time.sleep(30)

        current_time = 1
        print('Start expedition process')
        while not all_done(expeditions):
            ex = reduce(lambda x, y: x if x['time'] < y['time'] else y, expeditions.values())

            time.sleep(ex['time'] - current_time)
            current_time = ex['time']

            wakeup = ex['ex'].processTurn()
            expeditions[ex['ex'].id]['time'] = current_time + wakeup
            

        print('Expedition over, having a little nap')
        time.sleep(30)

        for ex in expeditions.values():
            ex['ex'].emitDelete()
