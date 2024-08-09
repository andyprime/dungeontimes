
import random

import core
import core.dungeon.generate
import core.expedition
from core.dungeon.dungeons import Dungeon


def logHandlerPrint(message):
    print(message)


if __name__ == "__main__":

    # This is all just some ad hoc stuff until a more robust

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
    exp.registerProcessor(logHandlerPrint)

    exp.begin()