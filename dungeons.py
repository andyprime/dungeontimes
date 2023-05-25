import uuid

import dice

class Dungeon:
    '''
        Currently the dungeon class only supports block dungeon types
        it can be child classed into block/wall versions later if needed
    '''

    def __init__(self):

        self.grid = []
        self.rooms = []


    def initiateGrid(self, height, width):
        # TODO: complain if params are bad

        for i in range(height):
            self.grid.append([])

        for i in range(len(self.grid)):
            self.grid[i] = []
            for j in range(width):
                border = i == 0 or j == 0 or i == (height -1) or (j == width - 1)
                c = Cell(border)
                c.coords = (i, j)
                self.grid[i].append(c)

    def height(self):
        return len(self.grid)

    def width(self):
        return len(self.grid[0])

    def roomCount(self):
        return len(self.rooms)

    def getCell(self, x, y):
        try:
            return self.grid[x][y]
        except:
            return None


    def canRoomFit(self, room, coords):
        if coords[0] == 0 or coords[1]  == 0:
            # print('Room fit failure: root border violation')
            return False

        if room.height + coords[0] >= self.height():
            # print('Room fit failure: max height exceeded')
            return False
        if room.width + coords[1] >= self.width():
            # print('Room fit failure: max width exceeded')
            return False


        top_bound = coords[0] - 1
        bottom_bound = coords[0] + room.height + 1

        left_bound = coords[1] - 1
        right_bound = coords[1] + room.width + 1


        # print('Height check: {}, {}'.format(bottom_bound - top_bound, room.height))
        # print(' Width check: {}, {}'.format(right_bound - left_bound, room.width))

        try:
            for i in range(top_bound, bottom_bound):
                for j in range(left_bound, right_bound):
                    if self.grid[i][j].type != Cell.SOLID:
                        return False
        except:
            print('Uh oh')
            print('TL Coords: {}, {}'.format(coords[0], coords[1]))
            print('BR Coords: {}, {}'.format(coords[0] + room.height, coords[1] + room.width))
            print('Room size: {}, {}'.format(room.height, room.width))
            print('Indexes: {}, {}'.format(i, j))
            print('Dimensions: {}, {}'.format(self.height(), self.width()))

        return True


    def carveRoom(self, room, coords):
        # we're gonna assume you already ran canRoomFit I guess

        room.coords = coords

        top_bound = coords[0]
        bottom_bound = coords[0] + room.height

        left_bound = coords[1]
        right_bound = coords[1] + room.width

        # print('C Height check: {}, {}'.format(bottom_bound - top_bound, room.height))
        # print('C  Width check: {}, {}'.format(right_bound - left_bound, room.width))

        for i in range(top_bound, bottom_bound):
            for j in range(left_bound, right_bound):
                self.grid[i][j].type = Cell.ROOM

    def carvePassage(self, cell):
        if type(cell) is tuple:
            cell = self.getCell(*cell)

        # TODO: maybe throw an exception if its not solid
        cell.type = Cell.PASSAGE

    # def canSupportRegion(self, cell):
    #     # this is kind of a shitty name

    #     tests = [cell.coords]

    #     tests.append( cell.north() )
    #     tests.append( cell.south() )
    #     tests.append( cell.east() )
    #     tests.append( cell.west() )

    #     for test in tests:
    #         c = self.getCell(cell.h, cell.w)
    #         if c and c.type != Cell.SOLID:
    #             return False
    #     return True

    def isSafeCarvable(self, cell, ignore=None):
        # safe carvable means it won't create any incidental connections between regions during dungeon gen
        # right now this doesn't test the cell itself, which *shouldn't* be a problem, I hope

        if type(cell) is tuple:
            cell = self.getCell(*cell)

        if cell.border:
            return False

        tests = []

        tests.append( self.getCell(*cell.north()) )
        tests.append( self.getCell(*cell.south()) )
        tests.append( self.getCell(*cell.east()) )
        tests.append( self.getCell(*cell.west()) )

        for test in tests:
            c = self.getCell(test.h, test.w)
            if c is ignore:
                continue

            if c and c.type != Cell.SOLID:
                return False
        return True


    def getPossibleCarves(self, cell):
        if type(cell) is tuple:
            cell = self.getCell(*cell)

        options = []

        for dir in Cell.directions():
            test_cell = self.getCell(*cell.byCode(dir))

            if test_cell.type != Cell.PASSAGE and self.isSafeCarvable(test_cell, cell):
                options.append(dir)

        return options



    def prettyPrint(self):

        for index, row in enumerate(self.grid):

            display = '{}: '.format(str(index).rjust(4, ' '))

            for cell in row:
                display += cell.symbol()

            print(display)



class Cell:

    SOLID = 1
    ROOM = 2
    PASSAGE = 3
    DOORWAY = 4
    ENTRANCE = 5


    NORTH = 100
    SOUTH = 101
    EAST = 102
    WEST = 103

    TRANSLATE = {
        1: 'solid',
        2: 'room',
        3: 'passage',
        4: 'doorway',
        5: 'entrance'
    }

    TRANSLATE_DIR = {
        100: 'North',
        101: 'South',
        102: 'East',
        103: 'West'
    }

    PRETTY = {
        1: '▓',
        2: '_',
        3: ' ',
        4: '+',
        5: '>'
    }

    @classmethod
    def directions(self):
        return [self.NORTH, self.SOUTH, self.EAST, self.WEST]

    def __init__(self, border=False, type=None):
        self.type = type
        # Note that we can't use static variable as parameter defaults in Python, so do this manually
        if self.type is None:
            self.type = Cell.SOLID
        self._coords = None
        self.h = None
        self.w = None
        self.border = border

    @property
    def coords(self):
        return self._coords

    @coords.setter
    def coords(self, coords):
        self._coords = coords
        self.h = coords[0]
        self.w = coords[1]

    def symbol(self):
        if self.border and False:
            return '#'
        else:
            return Cell.PRETTY[self.type]

    def north(self):
        if self.h == 0:
            return False
        else:
            return (self.h - 1, self.w)

    def south(self):
        if self.h != 0 and self.border:
            return False
        else:
            return (self.h + 1, self.w)

    def west(self):
        if self.w == 0:
            return False
        else:
            return (self.h, self.w - 1)

    def east(self):
        if self.w != 0 and self.border:
            return False
        else:
            return (self.h, self.w + 1)

    def all(self):
        a = [self.north(), self.south(), self.east(), self.west()]
        return [x for x in a if x]

    def byCode(self, code):
        if code == Cell.NORTH:
            return self.north()
        elif code == Cell.SOUTH:
            return self.south()
        elif code == Cell.EAST:
            return self.east()
        elif code == Cell.WEST:
            return self.west()
        else:
            return None

    def __str__(self):
        return 'Cell: {}, {}'.format(Cell.TRANSLATE[self.type], self._coords)




class Room:

    def __init__(self, properties):
        self.height = properties.get('height', None)
        self.width = properties.get('width', None)
        self.coords = properties.get('coords', None)




# class Room:

#     def __init__(self, number):
#         self.number = number
#         self.entrance = False
#         self.style = 'init'
#         self.size = 'init'
#         self.features = []
#         self.inhabitants = []
#         self.connections = []

#     def __str__(self):
#         line1 = 'Room {}. A {} room in the {} style.'.format(self.number, self.size, self.style)
#         if len(self.inhabitants) > 0:
#             line2 = 'Currently inhabited by some folks'
#         else:
#             line2 = 'Currently unoccupied'
#         line3 = 'Connects to rooms {}'.format(', '.join(self.connections))
#         return line1 + "\n" + line2 + "\n" + line3


#     def addInhabitant(self, creature):
#         # TODO: capacity limits?
#         self.inhabitants.append(creature)


#     def removeInhabitant(self, creature):
#         new_inhabitants = [i for i in self.inhabitants if i.id != creature.id]
#         self.inhabitants = new_inhabitants


class Creature:

    def __init__(self, properties):
        self.id = str(uuid.uuid1())
        self.name = properties.get('name', 'baddata')
        self.type = properties.get('type', 'baddata')
        self.job = properties.get('job', 'baddata')
        self.stock = properties.get('stock', 'baddata')

        self.str = properties.get('str', 'baddata')
        self.dex = properties.get('dex', 'baddata')
        self.con = properties.get('con', 'baddata')
        self.int = properties.get('int', 'baddata')
        self.wis = properties.get('wis', 'baddata')
        self.cha = properties.get('cha', 'baddata')

        self.maxhp = self.con
        self.currenthp = self.maxhp

    def generateInitiative(self):
        return dice.Dice.d(1,20)

    def __str__(self):
        return self.name + ', ' + self.stock + ' ' + self.job + '; S: ' + str(self.str) + ', D: ' + str(self.dex) + ', C: ' + str(self.con) + ', I: ' + str(self.int) + ', W: ' + str(self.wis) + ', C: ' + str(self.cha)

    def canAct(self):
        return self.currenthp > 0

    def getCombatAction(self, battle):
        # given the current battle state 

        target_team = battle.randomTeam(exclude=self.type) # using self.type won't work in the long run

        x = {
            'action_type': 'melee attack',
            'target': target_team.randomMember(alive=True)
        }
        # print(' Me: {}, {}'.format(self.name, self.type))
        # print('Him: {}, {}'.format(x['target'].name, x['target'].type))
        return x

    def applyDamage(self, damage_count):
        old = self.currenthp
        self.currenthp = self.currenthp - damage_count
        if self.currenthp < 0:
            self.currenthp = 0
        print('  HP old - {}, new - {}'.format(old, self.currenthp))

    def status(self):
        if self.currenthp == 0:
            return 'dead'
        elif self.currenthp < self.currenthp / 2:
            return 'injured'
        else:
            return 'mostly ok'

    def rollStat(self, stat):
        target = getattr(self, stat)
        return dice.Dice.d(1,20) <= target
        
