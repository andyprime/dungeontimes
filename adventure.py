
import random
import atexit
from pymongo import MongoClient
from bson import ObjectId

import core
import core.dungeon.generate
import core.expedition
from core.dungeon.dungeons import Dungeon

_advHandlerSettings = {}

def logHandlerPrint(message):
    print(message)

def overwriteFileHandler(message):
    if not _advHandlerSettings.get('fileHandle', False):
        _advHandlerSettings['fileHandle'] = open('default.out', 'w')
        atexit.register(_overwriteCleanup)

    _advHandlerSettings['fileHandle'].write(message + "\n")

def _overwriteCleanup():
    _advHandlerSettings['fileHandle'].close()

if __name__ == "__main__":

    # This is all just some ad hoc stuff until a more robust framework is made
    client = MongoClient('mongodb://{}:{}@localhost:27017'.format('root', 'devenvironment'))
    db = client.dungeondb

    exp = db.expeditions.find_one({'complete': False})

    if exp:
        print('Existing expedition found, unpacking.')

        # get the map
        d = db.dungeons.find_one({'id': exp.get('dungeon')})
        if not d:
            raise ValueError('No matching dungeon found.')

        cursor = exp.get('cursor', None)
        dungeon = Dungeon(serialized=d.get('body'))

        # get the party
        print('Unpacking delvers')
        delvers = []
        for a in db.delvers.find({'id': {'$in': exp.get('party') }}):
            delvers.append(core.critters.Delver(serialized=a['body']))

    else:
        print('No existing expedition, generating a new one.')

        # Generate dungeon
        dungeon = core.dungeon.generate.DungeonFactoryAlpha.generateDungeon()
        cursor = None

        # Populate dungeon
        for room in dungeon.rooms:
            for i in range(4):
                room.populate(core.critters.Monster.random())

        # create party
        delvers = []
        for i in range(4):
            delvers.append(core.critters.Delver.random())

    dungeon.prettyPrint()
    for room in dungeon.rooms:
        print('{}: {}'.format(dungeon.rooms.index(room), room))
    print(delvers)

    print('Start expedition process')
    exp = core.expedition.Expedition(dungeon, delvers, cursor)

    # exp.registerProcessor(logHandlerPrint)
    exp.registerProcessor(overwriteFileHandler)

    exp.begin()