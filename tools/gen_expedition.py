import argparse
import uuid
from pymongo import MongoClient

import core
import core.dungeon.generate

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='A simple script that generates a default settings dungeon with stocked rooms.')
    parser.add_argument('-p', '--persist', action='store_true', help='If provided will save the dungeon to the database.')
    parser.add_argument('-d', '--dungeon', help="The ID of a dungeon, if not provided a new one will also be generated.")
    args = parser.parse_args()

    if args.dungeon:
        dungeonId = args.dungeon
    else:

        # Generate dungeon
        dungeon = core.dungeon.generate.DungeonFactoryAlpha.generateDungeon()

        # Populate dungeon
        for room in dungeon.rooms:
            for i in range(4):
                room.populate(core.critters.Monster.random())

        b = dungeon.serialize()
        dungeonId = str(uuid.uuid1())
        d = {
            'id': dungeonId,
            'name': 'PLACEHOLDER',
            'body': b
        }

    # right now we're just going to always generate a party
    delvers = []
    for i in range(4):
        delver = core.critters.Delver.random()
        x = delver.serialize()
        print('1 {}'.format(x))
        x.update({'id': str(uuid.uuid1())})
        print('2 {}'.format(x))
        delvers.append(x)

    e = {
        'name': 'PLACEHOLDER',
        'complete': False,
        'dungeon': dungeonId,
        'party': [d['id'] for d in delvers],
        'cursor': None
    }

    print(e)
    if not args.dungeon:
        print(d)

    for delver in delvers:
        print(delver)

    if args.persist:

        client = MongoClient('mongodb://{}:{}@localhost:27017'.format('root', 'devenvironment'))
        db = client.dungeondb

        db.expeditions.insert_one(e)

        for delver in delvers:
            db.delvers.insert_one(delver)

        if not args.dungeon:
            db.dungeons.insert_one(d)