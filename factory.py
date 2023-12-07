import random
import uuid

import dungeons
import dice
import strings


class DungeonFactoryAlpha:
    '''
        This is a dungeon generation factory that follows the following principals:

        Grid type - block (borders are defined by cells not walls)

        Step 1: Place a random number of randomly sized rooms across the map
        Step 2: Use a growing tree algorithm to fill any remaining possible spaces with a perfect maze
        Step 3: Identify each unconnected room/passage segment and add connections until none remain
        Step 4: Remove some amount of dead ends to clean it up

        See: https://journal.stuffwithstuff.com/2014/12/21/rooms-and-mazes/
    '''

    DEFAULT_HEIGHT = 60
    DEFAULT_WIDTH = 150

    ROOM_HEIGHT_RANGE = (3, 20)
    ROOM_WIDTH_RANGE = (3, 20)


    MAX_ROOMS = 40
    MAX_ROOM_ATTEMPTS = 300

    # percent chance the tree maintains same carve direction when available
    CHANCE_MAINTAIN_DIRECTION = 80

    # percent chance that an extra connection will become a doorway instead of closed
    # this prevents the dungeon from being too linear
    CHANCE_EXTRA_DOORWAY = 5

    # percent chance to let a dead end live
    CHANCE_KEEP_DEADEND = 5
    # max number of runs of the sparseness removal process, -1 for no limit
    MAX_SPARENESS_RUNS = 20


    @classmethod
    def generateDungeon(self):


        dungeon = dungeons.Dungeon()

        self.header('Stage 0: Blank Slate')
        dungeon.initiateGrid(self.DEFAULT_HEIGHT, self.DEFAULT_WIDTH)
        dungeon.prettyPrint()

        # =============================================================================================
        self.header('Stage 1: Carve Rooms')
        room_attempts = 0
        while dungeon.roomCount() < self.MAX_ROOMS and room_attempts < self.MAX_ROOM_ATTEMPTS:
            room = self.generateRoom()

            # note that row/col zero are reserved for border
            # also note that coords are generated outside of the room to avoid recording bad attempts at all
            coords = (dice.Dice.between(1, dungeon.height()), dice.Dice.between(1, dungeon.width()))

            if dungeon.canRoomFit(room, coords):
                dungeon.carveRoom(room, coords)

            # we only need this if we're debugging a problem seed
            # self.header('Attempt {}'.format(room_attempts))
            # dungeon.prettyPrint()

            room_attempts += 1

        print()
        dungeon.prettyPrint()

        # =============================================================================================
        self.header('Stage 2: Passage Carving')

        treeCount = 0

        for i in range(1, dungeon.height() - 1):
            for j in range(1, dungeon.width() - 1):

                cursor = dungeon.getCell(i, j)

                if dungeon.isSafeCarvable(cursor):


                    treeCount += 1

                    # print('Starting new tree at {}'.format(cursor))

                    self.startGrowingTree(cursor, dungeon)

                    dungeon.newRegion()

        print()
        dungeon.prettyPrint()

        print('Tree count: {}'.format(treeCount))


        # =============================================================================================
        self.header('Stage 3: Connections')

        print()
        dungeon.regionPrint()

        # sub step 1: label connectors
        # Just loop through all uncarved squares and label them if they border two distinct regions


        # just a handy lookup map so we don't gotta fuss about finding them later
        # cell -> list of adjacent regions region
        connectorCells = {}

        for i in range(1, dungeon.height() - 1):
            for j in range(1, dungeon.width() - 1):

                cursor = dungeon.getCell(i, j)

                if cursor.type == dungeons.Cell.SOLID:
                    e = dungeon.getCell(*cursor.east()).region
                    w = dungeon.getCell(*cursor.west()).region

                    n = dungeon.getCell(*cursor.north()).region
                    s = dungeon.getCell(*cursor.south()).region

                    if (e != None and w != None and e != w):
                        cursor.type = dungeons.Cell.CONNECTOR
                        connectorCells[(i, j)] = [e, w]
                    elif n != None and s != None and n != s:
                        cursor.type = dungeons.Cell.CONNECTOR
                        connectorCells[(i, j)] = [n, s]


        print('After connector creation')
        dungeon.regionPrint()

        # sub step 2: pick a random starting room
        roomCursor = random.choice(dungeon.rooms)
        # that room's region will eventually become the only region as we open doors
        regionCollapse = dungeon.getCell(*roomCursor.coords).region

        print('Collapsing to: {}'.format(regionCollapse))

        remainingRegions = self.countRemainingRegions(connectorCells)

        while(remainingRegions > 1):
            # sub step 3: opening and collapsing

            # get a list of all connections from the collapseTo region to pick a new target region
            validConnectorCoords = [coords for coords, regions in connectorCells.items() if regionCollapse in regions]

            selectedConnector = random.choice(validConnectorCoords)

            # change the connector into a doorway, it needs a region since it used to be nothing
            print('Opening connector at: {}'.format(selectedConnector))
            selectedCell = dungeon.getCell(*selectedConnector)
            self.makeDoor(selectedCell, regionCollapse)

            # find the region opposite the doorway and collapse it, there should only ever be 2 items in those lists

            openedRegion = [ x for x in connectorCells[selectedConnector] if x != regionCollapse ][0]

            # get the list of connectors shared between the main and collapsing region
            relevantConnectorCoords = [coords for coords, regions in connectorCells.items() if regionCollapse in regions and openedRegion in regions]

            self.collapseRegion(dungeon, connectorCells, openedRegion, regionCollapse)

            # sub step 4: cleaning remaining connectors for starting region
            # always remove connectors adjacent to new or auxilliary doorways
            adjacencyChecks = [selectedCell]
            for coords in relevantConnectorCoords:
                if coords == selectedConnector:
                    connectorCells.pop(coords)
                    continue

                adjacent = False
                for check in adjacencyChecks:
                    if check.adjacent(coords):
                        adjacent = True
                        break

                if adjacent:
                    # print('Closing adjacent: {}'.format(coords))
                    toClose = dungeon.getCell(*coords)
                    toClose.type = dungeons.Cell.SOLID
                elif dice.Dice.d(1,100) < self.CHANCE_EXTRA_DOORWAY:
                    print('Making auxillary door at: {}'.format(coords))
                    doorCell = dungeon.getCell(*coords)
                    self.makeDoor(doorCell, regionCollapse)
                    adjacencyChecks.append(doorCell)

                    regions = connectorCells[coords]
                    remaining = [ x for x in connectorCells[coords] if x != regionCollapse ]
                    if len(remaining) > 0:
                        print('Found new region to collapse: {}'.format(remaining[0]))
                        self.collapseRegion(dungeon, connectorCells, remaining[0], regionCollapse)
                else:
                    toClose = dungeon.getCell(*coords)
                    toClose.type = dungeons.Cell.SOLID

                connectorCells.pop(coords)

            # dungeon.regionPrint()

            remainingRegions = self.countRemainingRegions(connectorCells)


        # =============================================================================================
        self.header('Stage 4: Sparseness')

        # Sparseness removal is the process of removing some percentage of dead ends to reduce the
        # amount of wasted time exploring the dungeon
        # This particular implementation is particularly ham handed, trading a lot of loop cycles for
        # simplicity of implementation. A more methodical approach could also implement max dead end
        # length if it actually followed paths


        print('Pre-sparseness removal')
        dungeon.prettyPrint()

        runCount = 0
        allDone = False
        deadendWhitelist = []

        while (self.MAX_SPARENESS_RUNS == -1 and not allDone) or (runCount < self.MAX_SPARENESS_RUNS and not allDone):

            deadends = []
            for cell in dungeon.allCells():
                if cell.type == dungeons.Cell.PASSAGE:
                    neighbors = [cell.east(), cell.west(), cell.north(), cell.south()]
                    paths = [x for x in neighbors if dungeon.getCell(*x).type in [dungeons.Cell.PASSAGE, dungeons.Cell.DOORWAY]]
                    if len(paths) == 1:
                        deadends.append(cell)

            if len(deadends) > 0:
                print('Remaining deadends: {}'.format(len(deadends)))
                for cell in deadends:
                    if dice.Dice.d(1,100) < self.CHANCE_KEEP_DEADEND:
                        print('Found a real keeper. Whitelisting {}'.format(cell))
                        deadendWhitelist.append(cell)
                    elif cell in deadendWhitelist:
                        print('Skipping whitelisted cell {}'.format(cell))
                        continue
                    else:
                        cell.type = dungeons.Cell.SOLID

            else:
                allDone = True

            runCount += 1
            print('Post Sparseness run {}'.format(runCount))
            dungeon.prettyPrint()

        # =============================================================================================
        self.header('Stage 5: Define entrance')

        # this is obviously pretty token, but we're gonna put the entrance into a random hallway cell

        halls = dungeon.allCells(dungeons.Cell.PASSAGE)
        entrance = random.choice(halls)
        entrance.type = dungeons.Cell.ENTRANCE

        print('Now with entrance')
        dungeon.prettyPrint()

        self.header('Exuent')
        return dungeon

    @classmethod
    def checkDupes(self, connectorCells):
        # this is just a sanity check on the region collapse system, it can get cleaned up at some point
        for coords, regions in connectorCells.items():
            if len(regions) != len(set(regions)):
                print('!!!!! Found duplicate entry: {}, {}'.format(coords, regions))

    @classmethod
    def countRemainingRegions(self, connectorCells):
        uniqueRegions = []
        for regions in connectorCells.values():
            for r in regions:
                if r not in uniqueRegions:
                    uniqueRegions.append(r)
        print('Found {} remaining regions: {}'.format(len(uniqueRegions), uniqueRegions))
        return len(uniqueRegions)

    @classmethod
    def collapseRegion(self, dungeon, connectorCells, regionToCollapse, collapseTo):
        print('Collapsing: {}'.format(regionToCollapse))
        for i in range(1, dungeon.height() - 1):
            for j in range(1, dungeon.width() - 1):
                c = dungeon.getCell(i, j)
                if c.region == regionToCollapse:
                    c.region = collapseTo

        # overwrite collapsed region in the map
        # don't worry if we end up with two collapseTo regions in the list, those will get removed later
        for coords, regionList in connectorCells.items():
            if regionToCollapse in regionList:
                connectorCells[coords] = [collapseTo if x == regionToCollapse else x for x in connectorCells[coords]]

    @classmethod
    def makeDoor(self, cell, region):
        cell.type = dungeons.Cell.DOORWAY
        cell.region = region


    @classmethod
    def startGrowingTree(self, start, dungeon):
        '''
        This is a general algorithm, capable of creating Mazes of different textures. It requires storage up to the size of the Maze. Each time you carve a cell,
        add that cell to a list. Proceed by picking a cell from the list, and carving into an unmade cell next to it. If there are no unmade cells next to the current
        cell, remove the current cell from the list. The Maze is done when the list becomes empty. The interesting part that allows many possible textures is how
        you pick a cell from the list. For example, if you always pick the most recent cell added to it, this algorithm turns into the recursive backtracker. If you
        always pick cells at random, this will behave similarly but not exactly to Prim's algorithm. If you always pick the oldest cells added to the list, this will
        create Mazes with about as low a "river" factor as possible, even lower than Prim's algorithm. If you usually pick the most recent cell, but occasionally pick
        a random cell, the Maze will have a high "river" factor but a short direct solution. If you randomly pick among the most recent cells, the Maze will have a
        low "river" factor but a long windy solution.
        '''

        dungeon.carvePassage(start)
        cursor = start
        pile = [start]

        previous_direction = None

        count = 1

        while len(pile) > 0:
            count += 1

            # print('Pile size: {}'.format(len(pile)))

            if len(pile) == 1:
                cursor = pile[0]
            else:
                # random, middle, newest, oldest
                # for now just do newest
                cursor = pile[-1]

            # print('Cursor: {}'.format(cursor))


            options = dungeon.getPossibleCarves(cursor)
            # print('Options: {}'.format(options))

            if len(options) == 0:
                # this node is exhausted, remove it from the pile
                # print('Node exhausted')
                pile.remove(cursor)
                continue
            else:
                roll = dice.Dice.d(1,100)

                if previous_direction in options and roll < self.CHANCE_MAINTAIN_DIRECTION:
                    direction = previous_direction
                else:
                    direction = random.choice(options)

            previous_direction = direction

            next_cell = dungeon.getCell(*cursor.byCode(direction))

            # print('Next cell selected: {}'.format(next_cell))
            pile.append(next_cell)
            dungeon.carvePassage(next_cell)

        # print('Pile is empty')

    @classmethod
    def getAllValidConnectors(self, dungeon, region):
        return

    @classmethod
    def generateRoom(self):
        # TODO: maybe tweak this so really long, thin rooms are less common
        props = {
            'height': dice.Dice.between(*self.ROOM_HEIGHT_RANGE),
            'width': dice.Dice.between(*self.ROOM_WIDTH_RANGE)
        }
        return dungeons.Room(props)

    @classmethod
    def header(self, title):
        diff = int( (self.DEFAULT_WIDTH + 4 - len(title)) / 2)

        s = ' ' + '=' * (diff - 1)
        s += ' {} '.format(title)
        s = s.ljust(156, '=')
        print(s)


class CreatureFactory:

    @classmethod
    def randomAdventurer(self):
        data = {
            'name': NameFactory.generateRandom(),
            'type': 'adventurer',
            'job': self.randomClass(),
            'stock': self.randomStock(),
            'str': dice.Dice.d(3, 6),
            'dex': dice.Dice.d(3, 6),
            'con': dice.Dice.d(3, 6),
            'int': dice.Dice.d(3, 6),
            'wis': dice.Dice.d(3, 6),
            'cha': dice.Dice.d(3, 6),
        }

        return dungeons.Creature(data)

    @classmethod
    def randomClass(self):
        return random.choice(['Barbarian', 'Bard', 'Cleric', 'Druid', 'Fighter', 'Paladin', 'Rogue', 'Ranger', 'Sorceror', 'Warlock', 'Wizard'])

    @classmethod
    def randomMonsterJob(self):
        return random.choice(['Brute', 'Warlord', 'Hedge Wizard', 'Skulker', 'Minion', 'Grunt'])

    @classmethod
    def randomStock(self):
        return random.choice(['Human', 'Elf', 'Half-Elf', 'Dwarf', 'Halfling', 'Ork', 'Half-Ork', 'Gnome', 'Aasimar', 'Tiefling', 'Genasi'])


    @classmethod
    def randomHumanoid(self):
        return random.choice(['Bandit', 'Ork', 'Goblin', 'Gnoll', 'Kua Toa', 'Dark Dwarf', 'Dark Elf', 'Morlock', 'Lizardman', 'Troglodyte'])

    @classmethod
    def randomMonster(self):
        data = {
            'name': NameFactory.generateRandom(),
            'type': 'monster',
            'job': self.randomMonsterJob(),
            'stock': self.randomHumanoid(),
            'str': dice.Dice.d(3, 6),
            'dex': dice.Dice.d(3, 6),
            'con': dice.Dice.d(3, 6),
            'int': dice.Dice.d(3, 6),
            'wis': dice.Dice.d(3, 6),
            'cha': dice.Dice.d(3, 6),
        }

        return dungeons.Creature(data)


class NameFactory:
    @classmethod
    def generateRandom(self):
        rando = dice.Dice.d(100)
        if rando <= 75:
            return self.generateRegularName()
        elif rando <= 90:
            return self.generateNickname()
        elif rando <= 100:
            return self.generateHonorificName()

    @classmethod
    def generateRegularName(self):
        return self.generateFirstName() + ' ' + self.generateBasicLastName()

    @classmethod
    def generateNickname(self):
        return self.generateFirstName() + ' "' + self.generateRandomWord().capitalize() + '" ' + self.generateBasicLastName()

    @classmethod
    def generateHonorificName(self):
        first = self.generateFirstName()

        rando = dice.Dice.d(6)

        # adjective-noun
        # adjective-verb
        # noun-verb
        # adjective
        # noun
        # verb
        if rando == 1:
            honorific = (strings.CoolAdjectives.random() + strings.CoolNouns.random()).capitalize()
        elif rando == 2:
            honorific = (strings.CoolAdjectives.random() + strings.CoolVerbs.random()).capitalize()
        elif rando == 3:
            honorific = (strings.CoolNouns.random() + strings.CoolVerbs.random()).capitalize()
        elif rando == 4:
            honorific = strings.CoolAdjectives.random().capitalize()
        elif rando == 5:
            honorific = strings.CoolNouns.random().capitalize()
        else:
            honorific = strings.CoolVerbs.random().capitalize()

        return first + ' the ' + honorific

    @classmethod
    def generateRandomWord(self):
        rando = dice.Dice.d(3)

        if rando == 1:
            return strings.CoolNouns.random()
        elif rando == 2:
            return strings.CoolAdjectives.random()
        else:
            return strings.CoolVerbs.random()


    @classmethod
    def generateFirstName(self):
        return strings.FirstNames.random()

    @classmethod
    def generateBasicLastName(self):
        return strings.BasicLastNames.random()


if __name__ == "__main__":

    seed = str(uuid.uuid1())
    # seed = '48cba384-4d36-11ee-8173-194626641d15'

    random.seed(seed)


    print('Random Dungeon Test')
    print('Seed : {}'.format(seed))
    print(DungeonFactoryAlpha.generateDungeon())

    print('Seed : {}'.format(seed))

    # print('Random Adventurer Test')
    # for i in range(1,12):
    #     print(CreatureFactory.generateAdventurer())    

    # for i in range(1,10):

    #     print(NameFactory.generateRandom())
    #     print('')

