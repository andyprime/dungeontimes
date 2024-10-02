import argparse
import uuid
from pymongo import MongoClient

import core
import core.dungeon.generate

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='A simple script that generates a default settings dungeon with stocked rooms.')
    parser.add_argument('-p', '--persist', action='store_true', help='If provided will save the dungeon to the database.')
    args = parser.parse_args()

    # Generate dungeon
    dungeon = core.dungeon.generate.DungeonFactoryAlpha.generateDungeon()

    # Populate dungeon
    for room in dungeon.rooms:
        for i in range(4):
            room.populate(core.critters.Monster.random())

    b = dungeon.serialize()
    d = {
        'id': str(uuid.uuid1()),
        'name': 'PLACEHOLDER',
        'body': b
    }
    print(d)

    if args.persist:
        print('Persisting')
        # one day we will have a shared system for persisting data to storage but for now just do it manually
        client = MongoClient('mongodb://{}:{}@localhost:27017'.format('root', 'devenvironment'))
        db = client.dungeondb

        db.dungeons.insert_one(d)
