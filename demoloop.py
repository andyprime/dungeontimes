import random
import time
import uuid
from functools import partial

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from bson import ObjectId
import pika

import core
import core.dungeon.generate
import core.expedition
from core.dungeon.dungeons import Dungeon
from core.mdb import MongoService

_advHandlerSettings = {}

def rabbitHandler(channel, message):
    print('$$$$$$$ Emit {}'.format(message))
    channel.basic_publish(exchange='dungeon', routing_key='*', body=message)

if __name__ == "__main__":
    # seed = str(uuid.uuid1())
    seed = 'f948ee97-d878-11ef-883a-0800279f8ffa'
    print('Seed: {}'.format(seed))
    random.seed(seed)

    mongo_client = MongoService('mongodb://{}:{}@localhost:27017'.format('root', 'devenvironment'))

    parameters = (pika.ConnectionParameters(host='localhost'))
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
                'ROOM_HEIGHT_RANGE': (3,8),
                'ROOM_WIDTH_RANGE': (3,8)
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

        pizza.ham()

        print('Expedition generated, having a little nap')
        time.sleep(30)

        print('Start expedition process')
        exp.begin()

        print('Expedition over, having a little nap')
        time.sleep(30)
