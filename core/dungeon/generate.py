import random
import uuid

from core.dungeon.dungeons import Dungeon
from core.dungeon.dungeons import Room
from core.dungeon.dungeons import Cell
import core.critters
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

    # DEFAULT_HEIGHT = 60
    # DEFAULT_WIDTH = 150

    DEFAULT_SETTINGS = {
        'DEFAULT_HEIGHT': 40,
        'DEFAULT_WIDTH': 60,
        'ROOM_HEIGHT_RANGE': (3, 20),
        'ROOM_WIDTH_RANGE': (3, 20),
        'MAX_ROOMS': 40,
        'MAX_ROOM_ATTEMPTS': 300,
        # percent chance the tree maintains same carve direction when available
        'CHANCE_MAINTAIN_DIRECTION': 80,
        # percent chance that an extra connection will become a doorway instead of closed
        # this prevents the dungeon from being too linear
        'CHANCE_EXTRA_DOORWAY': 5,
        # percent chance to let a dead end live
        'CHANCE_KEEP_DEADEND': 5,
        # max number of runs of the sparseness removal process, -1 for no limit
        'MAX_SPARENESS_RUNS': 20
    }       
    CURRENT_SETTINGS = {}

    @classmethod
    def generateDungeon(self, options={}):
        self.CURRENT_SETTINGS = self.DEFAULT_SETTINGS.copy()
        self.CURRENT_SETTINGS.update(options)

        # do a little setting validation
        if self.CURRENT_SETTINGS['DEFAULT_HEIGHT'] < 10:
            raise ValueError('Map height must be at 10')
        if self.CURRENT_SETTINGS['ROOM_HEIGHT_RANGE'][0] > self.CURRENT_SETTINGS['ROOM_HEIGHT_RANGE'][1]:
            raise ValueError('Room height range misordered')
        if self.CURRENT_SETTINGS['ROOM_WIDTH_RANGE'][0] > self.CURRENT_SETTINGS['ROOM_WIDTH_RANGE'][1]:
            raise ValueError('Room width range misordered')
        if self.CURRENT_SETTINGS['ROOM_HEIGHT_RANGE'][1] > self.CURRENT_SETTINGS['DEFAULT_HEIGHT'] - 6:
            raise ValueError('Maximum room height can not be greater than {} [map height - 6]'.format(self.CURRENT_SETTINGS['DEFAULT_HEIGHT'] - 6))
        if self.CURRENT_SETTINGS['ROOM_HEIGHT_RANGE'][0] < 2:
            raise ValueError('Minimum root height can not be less than 2')
        if self.CURRENT_SETTINGS['ROOM_WIDTH_RANGE'][1] > self.CURRENT_SETTINGS['DEFAULT_WIDTH'] - 6:
            raise ValueError('Maximum room width can not be greater than {} [map width - 6]'.format(self.CURRENT_SETTINGS['DEFAULT_WIDTH'] - 6))
        if self.CURRENT_SETTINGS['ROOM_WIDTH_RANGE'][0] < 2:
            raise ValueError('Minimum root width can not be less than 2')

        dungeon = Dungeon()

        self.header('Stage 0: Blank Slate')
        dungeon.initialize(self.CURRENT_SETTINGS['DEFAULT_HEIGHT'], self.CURRENT_SETTINGS['DEFAULT_WIDTH'])
        # dungeon.prettyPrint()

        # =============================================================================================
        self.header('Stage 1: Carve Rooms')
        room_attempts = 0
        while dungeon.roomCount() < self.CURRENT_SETTINGS['MAX_ROOMS'] and room_attempts < self.CURRENT_SETTINGS['MAX_ROOM_ATTEMPTS']:
            # note that row/col zero are reserved for border
            # also note that coords are generated outside of the room to avoid recording bad attempts at all
            coords = (random.randint(1, dungeon.height()), random.randint(1, dungeon.width()))

            room = Room(coords, self.roomProps())

            if dungeon.canRoomFit(room, coords):
                dungeon.carveRoom(room, coords)

            # we only need this if we're debugging a problem seed
            # self.header('Attempt {}'.format(room_attempts))
            # dungeon.prettyPrint()

            room_attempts += 1

        # print()
        # dungeon.prettyPrint()

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

        # print()
        # dungeon.prettyPrint()

        # print('Tree count: {}'.format(treeCount))

        # =============================================================================================
        self.header('Stage 3: Connections')

        # print()
        # dungeon.regionPrint()

        # sub step 1: label connectors
        # Just loop through all uncarved squares and label them if they border two distinct regions
        # We will also create a handy lookup map so we don't gotta fuss about finding them later
        # A dictionary where the index is a cell that is a connector and the value is a list of two regions it bridges
        connectorCells = {}

        for i in range(1, dungeon.height() - 1):
            for j in range(1, dungeon.width() - 1):

                cursor = dungeon.getCell(i, j)

                if cursor.type == Cell.SOLID:
                    e = dungeon.getCell(*cursor.east()).region
                    w = dungeon.getCell(*cursor.west()).region

                    n = dungeon.getCell(*cursor.north()).region
                    s = dungeon.getCell(*cursor.south()).region

                    if (e != None and w != None and e != w):
                        cursor.type = Cell.CONNECTOR
                        connectorCells[(i, j)] = [e, w]
                    elif n != None and s != None and n != s:
                        cursor.type = Cell.CONNECTOR
                        connectorCells[(i, j)] = [n, s]


        # print('After connector creation')
        # dungeon.regionPrint()

        # sub step 2: pick a random starting room
        roomCursor = random.choice(dungeon.rooms)
        # that room's region will eventually become the only region as we open doors
        regionCollapse = dungeon.getCell(*roomCursor.coords).region

        # print('Collapsing to: {}'.format(regionCollapse))

        remainingRegions = self.countRemainingRegions(connectorCells)

        while(remainingRegions > 1):
            # sub step 3: opening and collapsing

            # get a list of all connections from the collapseTo region to pick a new target region
            validConnectorCoords = [coords for coords, regions in connectorCells.items() if regionCollapse in regions]

            if len(validConnectorCoords) == 0:
                # this scenario occurs when a map is generated where a set of regions is more than one cell away from the remaining regions
                # its more likely crop up when the map dimensions are small and the passage carving is unable to create anything between
                # two rooms that start with 2 cells between them
                                
                # Try to find a solution first that doesn't involve two adjacent door cells by finding an uncarved cell that could act as a bridge
                # so we're looking for a solid tile with no adjcaent regions but with neighbors that are adjacent to our main region and any other one
                remediated = False
                solids = dungeon.allCells(Cell.SOLID)
                for cell in solids:
                    neighbors = cell.all()
                    x = [dungeon.getCell(*n).type for n in neighbors]
                    # note the length requirement prevents this condition from picking edge cells for which all() returns fewer results
                    if set(x) == {1} and len(x) == 4:
                        homeOptions = []
                        awayOptions = []

                        for n1 in neighbors:
                            c1 = dungeon.getCell(*n1)
                            for n2 in c1.all():
                                c2 = dungeon.getCell(*n2) 
                                if c2.type in [Cell.PASSAGE, Cell.ROOM]:
                                    if c2.region == regionCollapse:
                                        homeOptions.append( (c1, c2.type) )
                                    if c2.region != regionCollapse:
                                        awayOptions.append( (c1, c2.type, c2.region) )

                        # now that we have a 
                        if len(homeOptions) > 0 and len(awayOptions) > 0:
                            home = random.choice(homeOptions)
                            away = random.choice(awayOptions)
                            # now that we've found a valid set of three cells, we can carve them manually
                            # before proceeding onto the region collapse sub-step for our "away" region
                            cell.type = Cell.PASSAGE
                            cell.region = regionCollapse

                            homeCell = home[0]
                            homeType = home[1]
                            homeCell.type = Cell.PASSAGE if homeType == Cell.PASSAGE else Cell.DOORWAY
                            homeCell.region = regionCollapse

                            awayCell = away[0]
                            awayType = away[1]
                            awayRegion = away[2]

                            awayCell.type = Cell.PASSAGE if awayType == Cell.PASSAGE else Cell.DOORWAY
                            awayCell.region = regionCollapse
                            
                            remediated = True
                            openedRegion = awayRegion
                            # in this case there were never any connectors between our regions so there are 
                            relevantConnectorCoords = []

                if not remediated:
                    # T he previous solution will work in all possible scenarios but we should make a fuss
                    # since it will stack trace later regardless
                    raise RuntimeError('Map generation detected a divided region scenario it was unable to remediate.')
            else:
                # this is the regular scenario section for when the distance problem doesn't occur      
                selectedConnector = random.choice(validConnectorCoords)

                # change the connector into a doorway, it needs a region since it used to be nothing
                # print('Opening connector at: {}'.format(selectedConnector))
                selectedCell = dungeon.getCell(*selectedConnector)
                self.makeDoor(selectedCell, regionCollapse)

                # find the region opposite the doorway and collapse it, there should only ever be 2 items in those lists

                openedRegion = [ x for x in connectorCells[selectedConnector] if x != regionCollapse ][0]

                # get the list of connectors shared between the main and collapsing region, they will be cleaned up in the next stage
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
                    toClose.type = Cell.SOLID
                elif random.randint(1,100) < self.CURRENT_SETTINGS['CHANCE_EXTRA_DOORWAY']:
                    # print('Making auxillary door at: {}'.format(coords))
                    doorCell = dungeon.getCell(*coords)
                    self.makeDoor(doorCell, regionCollapse)
                    adjacencyChecks.append(doorCell)

                    regions = connectorCells[coords]
                    remaining = [ x for x in connectorCells[coords] if x != regionCollapse ]
                    if len(remaining) > 0:
                        # print('Found new region to collapse: {}'.format(remaining[0]))
                        self.collapseRegion(dungeon, connectorCells, remaining[0], regionCollapse)
                else:
                    toClose = dungeon.getCell(*coords)
                    toClose.type = Cell.SOLID

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

        # print('Pre-sparseness removal')
        # dungeon.prettyPrint()

        runCount = 0
        allDone = False
        deadendWhitelist = []

        while (self.CURRENT_SETTINGS['MAX_SPARENESS_RUNS'] == -1 and not allDone) or (runCount < self.CURRENT_SETTINGS['MAX_SPARENESS_RUNS'] and not allDone):

            deadends = []
            for cell in dungeon.allCells():
                if cell.type == Cell.PASSAGE:
                    neighbors = [cell.east(), cell.west(), cell.north(), cell.south()]
                    # paths = [x for x in neighbors if dungeon.getCell(*x).type in [Cell.PASSAGE, Cell.DOORWAY]]
                    passages = [x for x in neighbors if dungeon.getCell(*x).type == Cell.PASSAGE]
                    doors = [x for x in neighbors if dungeon.getCell(*x).type == Cell.DOORWAY]

                    # print('{}, p: {}, d: {}'.format(cell, passages, doors))
                    if len(passages) == 1 and len(doors) == 0:
                        deadends.append(cell)

            if len(deadends) > 0:
                for cell in deadends:
                    if random.randint(1,100) < self.CURRENT_SETTINGS['CHANCE_KEEP_DEADEND']:
                        # print('Found a real keeper. Whitelisting {}'.format(cell))
                        deadendWhitelist.append(cell)
                    elif cell in deadendWhitelist:
                        # print('Skipping whitelisted cell {}'.format(cell))
                        continue
                    else:
                        cell.type = Cell.SOLID

            else:
                allDone = True

            runCount += 1
            # print('Post Sparseness run {}'.format(runCount))
            # dungeon.prettyPrint()

        # =============================================================================================
        self.header('Stage 5: Define entrance')

        # this is obviously pretty token, but we're gonna put the entrance into a random hallway cell

        halls = dungeon.allCells(Cell.PASSAGE)
        entrance = random.choice(halls)
        entrance.type = Cell.ENTRANCE

        # print('Now with entrance')
        # dungeon.prettyPrint()

        self.header('Exuent')

        return dungeon

    @classmethod
    def checkDupes(self, connectorCells):
        # this is just a sanity check on the region collapse system, it can get cleaned up at some point
        for coords, regions in connectorCells.items():
            if len(regions) != len(set(regions)):
                pass
                # print('!!!!! Found duplicate entry: {}, {}'.format(coords, regions))

    @classmethod
    def countRemainingRegions(self, connectorCells):
        uniqueRegions = []
        for regions in connectorCells.values():
            for r in regions:
                if r not in uniqueRegions:
                    uniqueRegions.append(r)
        # print('Found {} remaining regions: {}'.format(len(uniqueRegions), uniqueRegions))
        return len(uniqueRegions)

    @classmethod
    def collapseRegion(self, dungeon, connectorCells, regionToCollapse, collapseTo):
        # print('Collapsing: {}'.format(regionToCollapse))
        for i in range(1, dungeon.height() - 1):
            for j in range(1, dungeon.width() - 1):
                c = dungeon.getCell(i, j)
                if c.region == regionToCollapse:
                    c.region = collapseTo

        # The collapsed region no longer exists so we overwrite all instances of it in our mapping
        # don't worry if we end up with two collapseTo regions in the list, those will get removed later [andy: What does this mean?]
        for coords, regionList in connectorCells.items():
            if regionToCollapse in regionList:
                connectorCells[coords] = [collapseTo if x == regionToCollapse else x for x in connectorCells[coords]]

    @classmethod
    def makeDoor(self, cell, region):
        cell.type = Cell.DOORWAY
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
                roll = random.randint(1,100)

                if previous_direction in options and roll < self.CURRENT_SETTINGS['CHANCE_MAINTAIN_DIRECTION']:
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
    def roomProps(self):
        # TODO: maybe tweak this so really long, thin rooms are less common
        return {
            'height': random.randint(*self.CURRENT_SETTINGS['ROOM_HEIGHT_RANGE']),
            'width': random.randint(*self.CURRENT_SETTINGS['ROOM_HEIGHT_RANGE'])
        }

    @classmethod
    def header(self, title):
        diff = int( (self.CURRENT_SETTINGS['DEFAULT_WIDTH'] + 4 - len(title)) / 2)

        s = ' ' + '=' * (diff - 1)
        s += ' {} '.format(title)
        s = s.ljust(156, '=')
        # print(s)
