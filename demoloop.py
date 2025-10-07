import argparse
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
import core.region
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

def buildExpedition(region):
    """
        Making a note here for clarity
        Strictly speaking the expedition should not be a top level object, eventually the logic of where delvers go
        and what they do as a group should at the band level but since we're still in this engine demo stage where
        everything is ephemeral so the hooks to correctly hang that logic simply do not exist yet. For now things
        can live under expedition as an expedient way to get the data to the client
    """

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

    did = dungeon.save()
    dungeon.id = did

    region.place_dungeon(did)

    print('Generated dungeon')

    # create party
    delvers = []
    ids = []
    for i in range(4):
        d = core.critters.Delver.random()
        delvers.append(d)
        ids.append(d.save())

    band = core.critters.Band()
    band.members = delvers
    band.save()

    print('Generated delvers')

    exp = core.expedition.Expedition(region, dungeon, band, None)
    exp.save()

    print('Saved the expedition: {}'.format(exp.id))

    dungeon.prettyPrint()
    for room in dungeon.rooms:
        print('{}: {}'.format(dungeon.rooms.index(room), room))
    print(delvers)

    return exp 

def all_done(es):
    for x in es.values():
        if not x['ex'].over():
            return False
    return True

if __name__ == "__main__":
    parser  = argparse.ArgumentParser(description="Options for if you're running this outside of the container")
    parser.add_argument('-l', '--local', action='store_true', help='Overrides container hostnames to be localhost so this can be run in a shell without modification.')
    parser.add_argument('-s', '--seed', help="Override random seed generation with the provided value.")
    parser.add_argument('-e', '--exp', type=int, default=2, help="Number of expeditions to simulate. Default is 2.")
    args = parser.parse_args()

    print(args)

    if args.seed:
        seed = args.seed
    else:
        seed = str(uuid.uuid1())
    print('Seed: {}'.format(seed))
    random.seed(seed)

    settings = Settings()

    if args.local:
        mongo_host = 'localhost'
        rabbit_host = 'localhost'
    else:
        mongo_host = settings.mongo_host
        rabbit_host = settings.rabbit_host

    MongoService.setup('mongodb://{}:{}@{}:{}'.format(settings.mongo_user, settings.mongo_password, mongo_host, settings.mongo_port))
    creds = pika.PlainCredentials(settings.rabbit_user, settings.rabbit_password)
    parameters = (pika.ConnectionParameters(host=rabbit_host, credentials=creds))
    
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.exchange_declare('dungeon', exchange_type='fanout', durable=True)

    emitFn = partial(rabbitHandler, channel)

    result = MongoService.db.regions.delete_many({})

    region = core.region.RegionGenerate.generate_region()
    region.save()
    region.registerEventEmitter(emitFn)
    
    while True:
        print('Demo loop start!')
        print('Destroying any existing entities.')

        result = MongoService.db.expeditions.delete_many({})
        result2 = MongoService.db.dungeons.delete_many({})
        result3 = MongoService.db.delvers.delete_many({})
        region.remove_dungeons()

        print('Deleted: {}, {}, {}'.format(result.deleted_count, result2.deleted_count, result3.deleted_count))

        expeditions = {}

        for i in range(0, args.exp):
            exp = buildExpedition(region) 
            # starting it off with a low but staggered time
            expeditions[exp.id] = {'ex': exp, 'time': i+2}

        region.prettyPrint()

        for ex in expeditions.values():
            exchange_name = ex['ex'].id
            print('Declaring: {}'.format(exchange_name))
            ex['ex'].registerEventEmitter(emitFn)
            ex['ex'].emitNew()

        region.persist()
        region.emitDungeonLocales()

        print('Expedition(s) generated, having a little nap')
        print(expeditions)
        time.sleep(30)

        current_time = 1
        print('Start expedition process')
        while not all_done(expeditions):
            # this just figures out which expedition has the first scheduled process time
            ex = reduce(lambda x, y: x if x['time'] < y['time'] else y, expeditions.values())

            time.sleep(ex['time'] - current_time)
            current_time = ex['time']

            wakeup = ex['ex'].processTurn()
            expeditions[ex['ex'].id]['time'] = current_time + wakeup

        print('Expedition over, having a little nap')
        time.sleep(30)

        for ex in expeditions.values():
            ex['ex'].emitDelete()
