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
from core.dice import Dice
import core.dungeon.generate
import core.expedition
import core.region
from core.dungeon.dungeons import Dungeon
from core.mdb import MongoService

_advHandlerSettings = {}

def rabbitHandler(channel, message):
    # print('$$$$$$$ Emit {}'.format(message))
    channel.basic_publish(exchange='dungeon', routing_key='*', body=message)

def eventsaver(type, object, msg, transient=False):
    MongoService.save_event(type, object, msg, transient)

def stdout_processor(str):
    print('>>> {}'.format(str))

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
    'shop': 20,
    'offload': 20,
    'restock': 5000,
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

    print('Destroying any existing entities.')
    MongoService.db.regions.delete_many({})
    MongoService.db.expeditions.delete_many({})
    MongoService.db.dungeons.delete_many({})
    MongoService.db.delvers.delete_many({})
    MongoService.db.bands.delete_many({})
    MongoService.db.cities.delete_many({})

    emitfn = partial(rabbitHandler, channel)

    # build region
    region = core.region.RegionGenerate.generate_region()
    region.save()
    region.register_emitter(emitfn)
    region.register_event(eventsaver)

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
    region.emit_dungeon_locales()

    to_do = []
    current_time = 1

    for venue in region.city.venues:
        to_do.append({'action': 'restock', 'venue': venue.id, 'schedule': current_time + TIME_MAP['restock'] + Dice.roll('1d3') * 1000})

    print(to_do)

    while True:
        print('New loop, time: {}'.format(current_time))
        dungeon_changes = False

        # 1. Check to see if we lost a band and create a replacement
        if len(bands) < args.bands:
            print('Making new band')
            b = build_party()
            bands[b.id] = b
            region.emit_narrative('Aspiring delvers have formed a new band, {}.'.format(b.name), b.id)
            region.emit_bands()

        # 2. Check to see if any bands don't have anything to do
        for band_id, band in bands.items():
            if not any(t.get('band') == band_id for t in to_do):
                print('Band {} has nothing to do'.format(band.name))

                # possible actions
                #   - offload loot, takes precedence
                #   - plan expedition
                #   - carouse
                #   - shop
                #   - research dungeons

                if band.has_loot():
                    selected = 'offload'
                else:
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

        # 3. Find the soonest action

        to_do.sort(key=lambda a: a['schedule'])
        do = to_do.pop(0)
        time.sleep(do['schedule'] - current_time)
        current_time = do['schedule']

        # 4. Process action
        if (do['action'] == 'exp'):
            
            band = bands[do['band']]
            exp = expeditions[do['band']]

            if exp.over():

                region.remove_dungeon(exp.dungeon)
                region.emit_del_dungeon(exp.dungeon.id)
                region.persist()

                exp.dungeon.complete = True
                exp.dungeon.persist()

                exp.emit_delete()
                exp.persist()
                dungeon_changes = True

                del expeditions[do['band']]
                del dungeons[exp.dungeon.id]


                if exp.failed():
                    region.emit_narrative('{} have been defeated with the dungeon, who knows if any survive.'.format(band.name), band.id)
                    del bands[band.id]
                    band.active = False
                    band.persist()
                else:
                    region.emit_narrative('{} have returned from their daring dungeon expedition.'.format(band.name), band.id)

            else:
                delay = exp.process_turn()
                to_do.append({'action': 'exp', 'band': band.id, 'schedule': current_time + delay})

        elif (do['action'] == 'plan'):
            
            band = bands[do['band']]

            occupied_dungeons = [e.dungeon.id for e in expeditions.values()]
            available_dungeons = [d for d in dungeons.values() if d.id not in occupied_dungeons]

            if len(available_dungeons) > 0:
                dungeon = random.choice(available_dungeons)

                exp = core.expedition.Expedition(region, dungeon, band, None)
                exp.save()

                exp.register_emitter(emitfn)
                exp.register_processor(stdout_processor)
                exp.emit_new()
                region.emit_narrative('{} have planned an expedition to {}.'.format(band.name, dungeon.name), band.id)

                expeditions[band.id] = exp

                to_do.append({'action': 'exp', 'band': band.id, 'schedule': current_time + TIME_MAP['exp']})
            else:
                region.emit_narrative('{} were going to plan an expedition to the last dungeon but someone beat them to it.')

        elif (do['action'] == 'research'):
            d = build_dungeon()
            dungeons[d.id] = d
            region.place_dungeon(d)
            dungeon_changes = True

            region.emit_narrative('{} have been asking around and heard rumors about the location of {}.'.format(band.name, d.name), band.id)
            region.emit_new_dungeon(d)
            region.persist()

            # adding a little extra chance to keep the dungeon count topped up
            if random.choice([True, False]):
                to_do.append({'action': 'research', 'band': band_id, 'schedule': current_time + TIME_MAP['research']})

        elif (do['action'] == 'offload'):
            # sell a random loot item from one of the band
            band = bands[do['band']]

            # make sure to search the members in a random order so this process isn't deterministic
            order = list(range(0, len(band.members)))
            random.shuffle(order)

            for i in order:
                delver = band.members[i]
                if len(delver.inventory) > 0:
                    item = delver.inventory.pop()
                    print('Selling item: {} at {}'.format(item.name, item.value))
                    delver.persist()
                    region.emit_narrative('{} sold {} for {} coins.'.format(delver.name, item.name, item.value), band.id)
                    band.add_wealth(item.value)
                    band.persist()
                    region.emit_band(band)
                    break

        elif (do['action'] == 'carouse'):
            band = bands[do['band']]
            region.emit_narrative('{} are going on a long bender.'.format(band.name), band.id)
        elif (do['action'] == 'shop'):
            band = bands[do['band']]
            region.emit_narrative('{} are perusing the markets for the newest delving gear.'.format(band.name), band.id)
        elif (do['action'] == 'restock'):

            for i in range(5):
                print('!'*50)

            venue = next(v for v in region.city.venues if v.id == do['venue'])
            venue.restock()
            region.city.persist()
            region.emit_self()

            to_do.append({'action': 'restock', 'venue': venue.id, 'schedule': current_time + TIME_MAP['restock'] + Dice.roll('1d3') * 1000})

        else:
            print('!!! Unknown loop action: {}'.format(do))

        # we batch the emission of the dungeon entrance message
        if dungeon_changes:
            region.emit_dungeon_locales()
