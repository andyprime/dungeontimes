import argparse
import random
import uuid
from functools import partial, reduce

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from bson import ObjectId
import pika
from pydantic_settings import BaseSettings, SettingsConfigDict

import core.dm
# import core.region as region
# from core.dice import Dice
# import core.dungeon.generate
# from core.dungeon.dungeons import Dungeon
from core.mdb import MongoService

_advHandlerSettings = {}

def rabbit_handler(channel, message):
    # print('$$$$$$$ Emit {}'.format(message))
    channel.basic_publish(exchange='dungeon', routing_key='*', body=message)

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

    MongoService.hard_reset()
    emitfn = partial(rabbit_handler, channel)

    dm = core.dm.DungeonMaster({
        'db': MongoService,
        'rabbit': emitfn,
        'output': stdout_processor,
        'bands': args.bands,
        'dungeons': args.dungeons
        })

    dm.setup()

    try:
        dm.run()
    except Exception as e:
        print('Top level except exit:', e)
        raise e
