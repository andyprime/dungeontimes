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

TIME_MAP = {
    'exp': 20,
    'plan': 20,
    'research': 20,
    'carouse': 60,
    'shop': 20
}


def build_dungeon():
    dungeon = core.dungeon.generate.DungeonFactoryAlpha.generateDungeon({
            'DEFAULT_HEIGHT': 10,
            'DEFAULT_WIDTH': 30,
            'ROOM_HEIGHT_RANGE': (3,4),
            'ROOM_WIDTH_RANGE': (3,8),
            'MAX_SPARENESS_RUNS': 5,
            'MAX_ROOM_ATTEMPTS': 100
        })

    for room in dungeon.rooms:
        for i in range(4):
            room.populate(core.critters.Monster.random())

    dungeon.save()
    # dungeon.id = did

    # region.place_dungeon(did)

    return dungeon

def build_party():
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

    return band

def all_done(es):
    for x in es.values():
        if not x['ex'].over():
            return False
    return True

if __name__ == "__main__":
    parser  = argparse.ArgumentParser(description="Options for if you're running this outside of the container")
    parser.add_argument('-l', '--local', action='store_true', help='Overrides container hostnames to be localhost so this can be run in a shell without modification.')
    parser.add_argument('-s', '--seed', help="Override random seed generation with the provided value.")
    parser.add_argument('-b', '--bands', type=int, default=2, help="Number of bands to simulate. Default is 2.")
    parser.add_argument('-d', '--dungeons', type=int, default=4, help="Number of potential dungeons to maintain.")
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

    print('Destroying any existing entities.')
    MongoService.db.regions.delete_many({})
    MongoService.db.expeditions.delete_many({})
    MongoService.db.dungeons.delete_many({})
    MongoService.db.delvers.delete_many({})
    MongoService.db.bands.delete_many({})

    # build region
    region = core.region.RegionGenerate.generate_region()
    region.save()
    region.registerEventEmitter(emitFn)

    # build bands
    bands = {}
    for i in range(0, args.bands):
        b = build_party()
        bands[b.id] = b

    print('Bands: {}'.format(bands))

    dungeons = {}
    expeditions = {}

    # seed initial dungeons
    while len(dungeons) < args.dungeons:
        print('Only {} dungeons, making another one'.format(len(dungeons)))
        d = build_dungeon()
        dungeons[d.id] = d
        region.place_dungeon(d)
    # not sure if this is necessary at this stage
    region.persist()
    region.emitDungeonLocales()

    to_do = []
    current_time = 1
    while True:
        print('New loop, time: {}'.format(current_time))
        dungeon_changes = False
        # if a party doesn't have a todo, create one
        # this should only occur when a band has no active expedition

        print('!!! {}, {}'.format(len(to_do), to_do))

        if len(to_do) < len(bands):
            print('Band activity check: {}, {}'.format(len(to_do), len(bands)))
            for band_id, band in bands.items():
                unbusy = True
                for action in to_do:
                    if action['band'] == band_id:
                        print('Band {} has todo'.format(band.name))
                        unbusy = False
                        break
                
                if unbusy:
                    print('Band {} has nothing to do'.format(band.name))
                    # possible actions
                    #   - plan expedition
                    #   - carouse
                    #   - shop
                    #   - research dungeons

                    options = []

                    if band.can_carouse():
                        options.append('carouse')
                    if band.can_shop():
                        options.append('shop')

                    occupied_dungeons = [e.dungeon.id for e in expeditions.values()]
                    available_dungeons = [d for d in dungeons.values() if d.id not in occupied_dungeons]
                    if len(available_dungeons) > 0:
                        options.append('plan')
                    if len(available_dungeons) < int(args.dungeons/2):
                        options.append('research')

                    selected = random.choice(options)
                    to_do.append({'action': selected, 'band': band_id, 'schedule': current_time + TIME_MAP[selected]})


        if len(to_do) > len(bands):
            print('='*50)
            print('Excess todos detected')
            print(expeditions)
            print('='*50)

        # find the soonest action

        to_do.sort(key=lambda a: a['schedule'])
        do = to_do.pop(0)
        time.sleep(do['schedule'] - current_time)
        current_time = do['schedule']

        # process action

        print('Doing: {}'.format(do))

        if (do['action'] == 'exp'):
            
            band = bands[do['band']]
            exp = expeditions[do['band']]

            if exp.over():
                region.remove_dungeon(exp.dungeon)
                region.emit_del_dungeon(exp.dungeon.id)

                exp.dungeon.complete = True
                exp.dungeon.persist()

                exp.emitDelete()
                exp.persist()
                dungeon_changes = True

                del expeditions[do['band']]
                del dungeons[exp.dungeon.id]

            else:
                delay = exp.processTurn()
                to_do.append({'action': 'exp', 'band': band.id, 'schedule': current_time + delay})

        elif (do['action'] == 'plan'):
            
            band = bands[do['band']]

            print(expeditions.values())

            occupied_dungeons = [e.dungeon.id for e in expeditions.values()]
            available_dungeons = [d for d in dungeons.values() if d.id not in occupied_dungeons]
            dungeon = random.choice(available_dungeons)

            exp = core.expedition.Expedition(region, dungeon, band, None)
            exp.save()

            exp.registerEventEmitter(emitFn)
            exp.emitNew()
            region.emitNarrative('{} have planned an expedition to {}.'.format(band.name, dungeon.name))

            expeditions[band.id] = exp

            to_do.append({'action': 'exp', 'band': band.id, 'schedule': current_time + TIME_MAP['exp']})

        elif (do['action'] == 'research'):
            d = build_dungeon()
            dungeons[d.id] = d
            region.place_dungeon(d)
            dungeon_changes = True

            region.emitNarrative('{} have been asking around and heard rumors about the location of {}.'.format(band.name, d.name))
            region.emit_new_dungeon(d)

            # adding a little extra chance to keep the dungeon count topped up
            if random.choice([True, False]):
                to_do.append({'action': 'research', 'band': band_id, 'schedule': current_time + TIME_MAP['research']})


        elif (do['action'] == 'carouse'):
            band = bands[do['band']]
            region.emitNarrative('{} are going on a long bender.'.format(band.name))
        elif (do['action'] == 'shop'):
            band = bands[do['band']]
            region.emitNarrative('{} are perusing the markets for the newest delving gear.'.format(band.name))
        else:
            print('!!! Unknown loop action: {}'.format(do))



        # batch this
        if dungeon_changes:
            region.emitDungeonLocales()
