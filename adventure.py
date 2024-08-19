
import random
import atexit

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

    # Generate dungeon
    dungeon = core.dungeon.generate.DungeonFactoryAlpha.generateDungeon()

    dungeon.prettyPrint()

    # Populate dungeon
    for room in dungeon.rooms:

        for i in range(4):
            room.populate(core.critters.Monster.random())

    for room in dungeon.rooms:
        print('{}: {}'.format(dungeon.rooms.index(room), room))

    # create party
    delvers = []
    for i in range(4):
        delvers.append(core.critters.Delver.random())

    print(delvers)

    exp = core.expedition.Expedition(dungeon, delvers)
    # exp.registerProcessor(logHandlerPrint)
    exp.registerProcessor(overwriteFileHandler)

    exp.begin()