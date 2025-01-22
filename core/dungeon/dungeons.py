import uuid
import json

import core.critters

class Dungeon:
    '''
        Currently the dungeon class only supports block dungeon types
        it can be child classed into block/wall versions later if needed
    '''

    def __init__(self, serialized=None):

        self.grid = []
        self.rooms = []
        self.regionPalette = 1

        if serialized:
            document = json.loads(serialized)
            self.initialize(document.get('height'), document.get('width'))

            for code, coords in document.get('cells', {}).items():
                type = int(code[1])
                for c in coords:
                    self.getCell(c[0], c[1]).type = type

            for r in document.get('rooms', []):
                room = Room(serialized = r)
                self.rooms.append(room)
                room.num = self.rooms.index(room) + 1

    def initialize(self, height, width):
        # TODO: complain if params are bad

        for i in range(height):
            self.grid.append([])

        for i in range(len(self.grid)):
            self.grid[i] = []
            for j in range(width):
                border = i == 0 or j == 0 or i == (height - 1) or (j == width - 1)
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

    def entrance(self):
        for cell in self.allCells():
            if cell.type == Cell.ENTRANCE:
                return cell

    def allCells(self, typeFilter=None, navigable=None):
        # this is just a convenience function for when a process needs all the cells
        # regardless of arrangement, some code predates this call and could be switched over
        bucket = []
        for i in range(0, self.height()):
            for j in range(0, self.width()):
                c = self.grid[i][j]
                if navigable != None and navigable:
                    if c.navigable():
                        bucket.append(c)
                elif typeFilter == None or typeFilter == c.type:
                    bucket.append(c)
        return bucket

    def allRoomCells(self, roomNo):
        # a bit more efficient than making room no an allCells filter
        if type(roomNo) == Room:
            roomNo = self.rooms.index(roomNo)
        room = self.rooms[roomNo]
        cells = []
        for i in range(room.height):
            for j in range(room.width):
                cells.append(self.grid[i + room.coords[0]][j + room.coords[1]])
        return cells

    def getNeighbors(self, cell):
        # get all the navigable neighbors of this cell
        # return [x for x in cell.all() if x]
        return [self.getCell(*x) for x in cell.all() if self.getCell(*x).navigable()]

    # def getRoomForCell(self, cell):
    def roomAt(self, cell):
        for room in self.rooms:
            if cell in room:
                return room
        return None

    def roomBrethren(self, cell):
        # get all the cells that match the room of a given cell
        r = self.roomAt(cell)
        return self.allRoomCells(r)

    def basicPrint(self):
        for index, row in enumerate(self.grid):

            display = '{}: '.format(str(index).rjust(4, ' '))

            for cell in row:
                display += cell.symbol()

            print(display)

    def prettyPrint(self, highlight=None):
        for index, row in enumerate(self.grid):

            display = '{}: '.format(str(index).rjust(4, ' '))

            for cell in row:
                if cell == highlight:
                    display += 'P'
                elif cell.type == Cell.ROOM:
                    room = self.roomAt(cell)
                    roomNumber = self.rooms.index(room) + 1

                    # currently this expects min room dimensions of 3 and will break if the total room counts is 3 digits
                    displayLine = room.coords[0] + int(room.height / 2)
                    displayLength = len(str(roomNumber))
                    # this could come left a cell when the room no is 2 digits but I've already spent too much time here
                    displayStart = room.coords[1] + int(room.width / 2)

                    if cell.coords[0] == displayLine:
                        if (cell.coords[1] >= displayStart) and (cell.coords[1] < displayStart + displayLength):
                            display += str(roomNumber)[cell.coords[1] - displayStart]
                        else:
                            display += cell.symbol()
                    else:
                        display += cell.symbol()

                else:
                    display += cell.symbol()

            print(display)

    def regionPrint(self):

        for index, row in enumerate(self.grid):

            display = '{}: '.format(str(index).rjust(4, ' '))

            for cell in row:
                display += cell.regionSymbol()

            print(display)

    def serialize(self, includeOccupants=False):
        # just need a basic way to encode the dungeon as a single string, nothing fancy
        box = {
            'width': self.width(),
            'height': self.height(),
            'cells': {},
            'rooms': [r.serialize() for r in self.rooms]
        }

        # TODO: save some space by switching to a single string approach
        for t in Cell.realTypes():
            code = 't' + str(t)
            box['cells'][code] = []
            for cell in self.allCells():
                if cell.type == t:
                    box['cells'][code].append(cell.coords)

        return json.dumps(box)


    # all the purely construction functions

    def newRegion(self):
        self.regionPalette += 1

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

        self.rooms.append(room)
        room.num = self.rooms.index(room) + 1

        top_bound = coords[0]
        bottom_bound = coords[0] + room.height

        left_bound = coords[1]
        right_bound = coords[1] + room.width

        for i in range(top_bound, bottom_bound):
            for j in range(left_bound, right_bound):
                self.grid[i][j].type = Cell.ROOM
                self.grid[i][j].region = self.regionPalette
        self.newRegion()

    def carvePassage(self, cell):
        if type(cell) is tuple:
            cell = self.getCell(*cell)

        # TODO: maybe throw an exception if its not solid
        cell.type = Cell.PASSAGE
        cell.region = self.regionPalette

    def isSafeCarvable(self, cell, ignore=[]):
        # safe carvable means it won't create any incidental connections between regions during dungeon gen
        # right now this doesn't test the cell itself, which *shouldn't* be a problem, I hope
        # this also doesn't want to create any diagonal not-exactly-a-connections

        if type(cell) is tuple:
            cell = self.getCell(*cell)

        if cell.border:
            return False

        tests = []
        tests.append( self.getCell(*cell.north()) )
        tests.append( self.getCell(*cell.south()) )
        tests.append( self.getCell(*cell.east()) )
        tests.append( self.getCell(*cell.west()) )

        tests.append( self.getCell(*cell.northWest()) )
        tests.append( self.getCell(*cell.southWest()) )
        tests.append( self.getCell(*cell.northEast()) )
        tests.append( self.getCell(*cell.southEast()) )

        for test in tests:
            c = self.getCell(test.h, test.w)
            if c in ignore:
                continue

            if c and c.type != Cell.SOLID:
                return False
        return True

    def getPossibleCarves(self, cell, ignores=[]):
        if type(cell) is tuple:
            cell = self.getCell(*cell)

        options = []

        ignores = [self.getCell(*c) for c in cell.all()]
        ignores.append(cell)

        for dir in Cell.directions():
            test_cell = self.getCell(*cell.byCode(dir))

            if test_cell.type != Cell.PASSAGE and self.isSafeCarvable(test_cell, ignores):
                options.append(dir)

        return options


class Cell:

    SOLID = 1
    ROOM = 2
    PASSAGE = 3
    DOORWAY = 4
    ENTRANCE = 5
    CONNECTOR = 6

    NORTH = 100
    SOUTH = 101
    EAST = 102
    WEST = 103

    ALL_TYPE = [1, 2, 3, 4, 5, 6]
    NAVIGABLE = [2, 3, 4, 5]

    TRANSLATE = {
        1: 'solid',
        2: 'room',
        3: 'passage',
        4: 'doorway',
        5: 'entrance',
        6: 'BUILD UTIL'
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
        5: '>',
        6: '!'
    }

    @classmethod
    def directions(self):
        return [self.NORTH, self.SOUTH, self.EAST, self.WEST]

    @classmethod
    def realTypes(self):
        return [self.ROOM, self.PASSAGE, self.DOORWAY, self.ENTRANCE]

    def __init__(self, border=False, type=None):
        if type and type not in Cell.ALL_TYPE:
            raise ValueError('Invalid Cell type: {}'.format(type))
        self.type = type
        # Note that we can't use static variable as parameter defaults in Python, so do this manually
        if self.type is None:
            self.type = Cell.SOLID
        self._coords = None
        self.h = None
        self.w = None
        # TODO: border was a dumb experiment, pull it out
        self.border = border
        self.region = None

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

    def positiveSymbol(self):
        # some cell symbols are too blank to appear well when we use a non-standard color to highlight special cells
        if self.type == Cell.PASSAGE:
            return Cell.PRETTY[Cell.SOLID]
        else:
            return self.symbol()

    def navigable(self):
        return self.type in Cell.NAVIGABLE

    def regionSymbol(self):
        if self.type == Cell.CONNECTOR:
            return '!'
        elif self.region == None:
            return Cell.PRETTY[1]
        else:
            # just get a nice unique ascii symbol
            return chr(33 + self.region)

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

    # note that the diagonals are only used in carvability checks
    # to avoid diagonal connections
    def northEast(self):
        if self.h == 0:
            return False
        else:
            return (self.h -1, self.w + 1)

    def northWest(self):
        return (self.h - 1, self.w - 1)

    def southEast(self):
        return (self.h + 1, self.w + 1)

    def southWest(self):
        return (self.h + 1, self.w - 1)

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

    def adjacent(self, coords):
        return coords in self.all()

    def isRoom(self):
        # just a convenience function for accessing classes not to have to do the test themselves
        return self.type == Cell.ROOM

    def serialize(self, stringify=False):
        # not gonna json dump it since the dungeon side will do that
        if stringify:
            return json.dumps([self.type, self.h, self.w])
        else:
            return [self.type, self.h, self.w]

    def __str__(self):
        # this one is basically just for printing/debug
        return 'Cell: {}, {}'.format(Cell.TRANSLATE[self.type], self._coords)

    def __repr__(self):
        return 'C {}'.format(self._coords)

class Room:

    def __init__(self, coords=None, props=None, serialized=None):
        if serialized:
            i = serialized['i']
            self.height = i[0]
            self.width = i[1]
            self.coords = (i[2], i[3])
            self.locals = []
            self.num = 0
            for o in serialized['occ']:
                self.populate(core.critters.Monster(serialized=o))
        else:
            if not props.get('height', None):
                raise ValueError('Room creation missing parameter: props.height')
            if not props.get('width', None):
                raise ValueError('Room creation missing parameter: props.width')
            self.height = props.get('height')
            self.width = props.get('width')
            self.coords = coords
            self.locals = []
            self.num = 0

    def populate(self, critter):
        if type(critter) != core.critters.Monster:
            raise ValueError('Can not populate room with non-monster: {}'.format(critter))
        self.locals.append(critter)

    def occupied(self):
        return len(self.locals) > 0

    def empty(self):
        # clear out all the occupants of the room, they are probably dead!
        self.locals = []

    def serialize(self, stringify=False):
        box = {
            'i': (self.height, self.width, self.coords[0], self.coords[1]),
        }
        if len(self.locals):
            box['occ'] = [l.serialize() for l in self.locals]
        if stringify:
            return json.dumps(box)
        else:
            return box

    def __contains__(self, c):
        if type(c) == Cell:
            # print('1 {}, 2{}'.format(c, self.coords))
            if (c.coords[0] >= self.coords[0] and c.coords[0] < self.coords[0] + self.height) and (c.coords[1] >= self.coords[1] and c.coords[1] < self.coords[1] + self.width):
                return True
            else:
                return False
        else:
            return False

    def __str__(self):
        return '(Room No {}: {}x{} @ {}, {})'.format(self.num, self.height, self.width, self.coords, len(self.locals))

    def __repr__(self):
        return self.__str__()
