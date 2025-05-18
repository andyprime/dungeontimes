import uuid
import json
import random

import core.strings as strings

class Region:

    def __init__(self, serialized=None):
        self.grid = []
        self.name = strings.StringTool.random('region_names')
        self.id = str(uuid.uuid1())
        self.dungeons = {}
        self.emitters = []

    def initialize(self, height, width, terrain=None):
        if not terrain:
            raise ValueError('Must provide default terrain to region init.')
        for i in range(height):
            self.grid.append([])

        for i in range(len(self.grid)):
            self.grid[i] = []
            for j in range(width):
                c = RCell(RCell.PLAIN)
                c.coords = (i, j)
                self.grid[i].append(c)

    @property
    def height(self):
        return len(self.grid)

    @property
    def width(self):
        return len(self.grid[0])

    def registerEventEmitter(self, callback):
        self.emitters.append(callback)

    def emit(self, msg):
        for e in self.emitters:
            e(msg.encode('ASCII'))

    def emitDungeonLocales(self):
        dungeons = [str(list(c.coords)) for c in self.dungeons.values()]
        self.emit('DNGS;{}'.format(';'.join(dungeons)))

    # camel name functions are compatibility holdovers from super early prototype code
    def getCell(self, y, x):
        try:
            return self.grid[y][x]
        except:
            return None

    def allCells(self, typeFilter=None, navigable=None):
        bucket = []
        for i in range(0, self.height):
            for j in range(0, self.width):
                c = self.grid[i][j]
                if navigable != None and navigable:
                    if c.navigable():
                        bucket.append(c)
                elif typeFilter == None or typeFilter == c.type:
                    bucket.append(c)
        return bucket

    def getNeighbors(self, cell):
        # get all the navigable neighbors of this cell
        return [self.getCell(*x) for x in cell.all() if self.getCell(*x) and self.getCell(*x).navigable()]

    def getWeight(self, cell):
        return RCell.WEIGHT[cell.type]

    def place_dungeon(self, dungeon_id):
        cells = [c for c in self.allCells() if c.type in RCell.DUNGEON_TYPES]
        self.dungeons[dungeon_id] = random.choice(cells)
        
    def find_dungeon(self, dungeon_id):
        return self.dungeons[dungeon_id]

    def remove_dungeons(self):
        self.dungeons.clear()

    def prettyPrint(self, highlight=None, path=None):
        if highlight and type(highlight) == tuple:
            highlight = self.getCell(*highlight)

        for index, row in enumerate(self.grid):

            display = '{}: '.format(str(index).rjust(4, ' '))

            for cell in row:
                if cell == highlight:
                    c = 'P'
                elif cell in self.dungeons.values():
                    c = 'D'
                else:
                    c = cell.symbol()

                if path and cell in path:
                        c = '\033[93m' + c + '\033[0m'
                display += c

            print(display)

    def serialize(self, stringify=False):
        # just need a basic way to encode the dungeon as a single string, nothing fancy
        box = {
            'id': self.id,
            'name': self.name,
            'width': self.width,
            'height': self.height,
            'homebase': self.homebase,
            'dungeons': [list(e.coords) for e in self.dungeons.values()],
            'cells': [c.serialize(False) for c in self.allCells()]
        }
        if stringify:
            return json.dumps(box)
        else:
            return box

class RCell:

    CITY = 1
    FARMLAND = 2
    ROAD = 3
    FOREST = 4
    RIVER = 5
    WATER = 6
    HILLS = 7
    MOUNTAIN = 8
    DESERT = 9
    PLAIN = 10
    TOWN = 11

    ALL_TYPES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    DUNGEON_TYPES = [4, 7, 9, 10]
    NAVIGABLE = [1, 2, 3, 4, 5, 7, 9, 10, 11]
    PERSISTENT = [1, 2, 3, 11]

    PRETTY = {
        1: '*',
        2: '#',
        3: '=',
        4: '▓',
        5: '~',
        6: ' ',
        7: '@',
        8: '^',
        9: '%',
        10: '.',
        11: 'o'
    }

    TRANSLATE = {
        1: 'City',
        2: 'Farm',
        3: 'Road',
        4: 'Forest',
        5: 'River',
        6: 'Water',
        7: 'Hills',
        8: 'Mtn.',
        9: 'Desert',
        10: 'Plain',
        11: 'Town'
    }

    WEIGHT = {
        1: 3,
        2: 2,
        3: 1,
        4: 8,
        5: 6,
        6: 100,
        7: 6,
        8: 16,
        9: 4,
        10: 4,
        11: 2
    }

    def __init__(self, type=None):
        if type and type not in RCell.ALL_TYPES:
            raise ValueError('Invalid Region Cell type: {}'.format(type))

        self.type = type
        self.name = None

    @property
    def coords(self):
        return self._coords

    @coords.setter
    def coords(self, coords):
        self._coords = coords
        self.h = coords[0]
        self.w = coords[1]

    def navigable(self):
        return self.type in RCell.NAVIGABLE

    def symbol(self):
        return RCell.PRETTY[self.type]

    def north(self):
        return (self.h - 1, self.w)

    def south(self):
        return (self.h + 1, self.w)

    def west(self):
        return (self.h, self.w - 1)

    def east(self):
        return (self.h, self.w + 1)

    def all(self):
        a = [self.north(), self.south(), self.east(), self.west()]
        return [x for x in a if x]

    def serialize(self, stringify=False):
        box = [self.type, self.h, self.w]
        if self.name:
            box.append(self.name)
        if stringify:
            return json.dumps(box)
        else:
            return box

    def __str__(self):
        return 'R Cell: {}, {}'.format(RCell.TRANSLATE[self.type], self._coords)

    def __repr__(self):
        return 'RC {}'.format(self._coords)

class RegionGenerate:

    DEFAULT_SETTINGS = {
        'DEFAULT_HEIGHT': 40,
        'DEFAULT_WIDTH': 80,
        'DEFAULT_TERRAIN': RCell.PLAIN,
        'TOWN_AMOUNT_RATIO': 0.0021,
        'TOWN_SPACING_RATIO': 0.15,
        'FARMLAND_RADIUS': 3,
        'TERRAIN_AMOUNT_RATIO': 0.0030,

    }       
    CURRENT_SETTINGS = {}

    TOWN_ATTEMPT_CUTOFF = 100

    @classmethod
    def generate_region(self, options={}):
        self.CURRENT_SETTINGS = self.DEFAULT_SETTINGS.copy()
        self.CURRENT_SETTINGS.update(options)

        # =============================================================================================
        # self.header('Setup')
        region = Region()
        region.initialize(self.CURRENT_SETTINGS['DEFAULT_HEIGHT'], self.CURRENT_SETTINGS['DEFAULT_WIDTH'], self.CURRENT_SETTINGS['DEFAULT_TERRAIN'])

        # region.prettyPrint()

        # =============================================================================================
        # self.header('City Generation')

        height_range = ( int(region.height / 2) - int(region.height * 0.1), int(region.height / 2) + int(region.height * 0.1) )
        width_range = ( int(region.width / 2) - int(region.width * 0.1), int(region.width / 2) + int(region.width * 0.1) )

        y = random.randint(height_range[0], height_range[1])
        x = random.randint(width_range[0], width_range[1])

        # friendly reminder we do (y, x) because that's more convenient to display
        region.grid[y][x].type = RCell.CITY
        region.grid[y][x].name = strings.StringTool.random('city_names')
        region.homebase = (y, x)

        # region.prettyPrint()

        # =============================================================================================
        # self.header('Towns and roads')

        total_space = region.height * region.width
        amount = int(total_space * self.CURRENT_SETTINGS['TOWN_AMOUNT_RATIO'])
        town_count = max(1, random.randint(amount - 1, amount + 1))
        
        existing_towns = []
        town_spacing = int(max(region.height, region.width) * self.CURRENT_SETTINGS['TOWN_SPACING_RATIO'])
        town_attempts = 0

        # print('Placeing {} towns'.format(town_count))
        # print('Min spacing: {}'.format(town_spacing))

        while len(existing_towns) < town_count and town_attempts < self.TOWN_ATTEMPT_CUTOFF:
            clear = True

            placement = ( random.randint(0, region.height - 1), random.randint(0, region.width - 1))

            # no towns on the borders just for looks
            if placement[0] in [0, region.height - 1] or placement[1] in [0, region.width - 1]:
                clear = False
            # must be a certain distance away from the main city and any already placed towns based on map proportions
            if self.distance(placement, region.homebase) <= town_spacing:
                clear = False
            for town in existing_towns:
                if self.distance(placement, town) <= town_spacing:
                    clear = False

            if clear:
                existing_towns.append(placement)
                region.grid[placement[0]][placement[1]].type = RCell.TOWN
                self.path_road(region, region.homebase, placement)
        
        # region.prettyPrint()

        # =============================================================================================
        # self.header('Farms')

        # lets not be clever about this
        for cell in region.allCells():
            close_enough = False
            if self.distance(cell.coords, region.homebase) <= self.CURRENT_SETTINGS['FARMLAND_RADIUS'] + 1:
                close_enough = True
            for town in existing_towns:
                if self.distance(cell.coords, town) <= self.CURRENT_SETTINGS['FARMLAND_RADIUS']:
                    close_enough = True

            if close_enough and cell.type == self.CURRENT_SETTINGS['DEFAULT_TERRAIN']:
                cell.type = RCell.FARMLAND

        # region.prettyPrint()


        # =============================================================================================
        # self.header('Other Terrain')

        terrain_options = [RCell.FOREST, RCell.HILLS, RCell.MOUNTAIN, RCell.DESERT]

        all_locales = existing_towns.copy()
        all_locales.append(region.homebase)
        for i in [0, 1]:
            terrain = random.choice(terrain_options)
            terrain_options.remove(terrain)

            # print('Drawing some: {}'.format(terrain))
            amount = int(region.height * region.width * self.CURRENT_SETTINGS['TERRAIN_AMOUNT_RATIO'])
            attempts = 0
            successes = 0
            while successes < amount or attempts > self.TOWN_ATTEMPT_CUTOFF:
                # this is mildly heavy but this process doesn't need to run often
                cell = random.choice(region.allCells(self.CURRENT_SETTINGS['DEFAULT_TERRAIN']))

                clear = True
                for pos in all_locales:
                    if self.distance(pos, cell.coords) <= 4:
                        clear = False
                if clear:
                    radius = random.randint(4, 8)
                    self.draw_terrain(region, cell.coords, radius, terrain)
                    successes += 1

        # region.prettyPrint()

        return region


    @classmethod
    def draw_terrain(self, region, center, radius, type):
        for cell in region.allCells():
            if self.distance(cell.coords, center) <= radius and cell.type not in RCell.PERSISTENT:
                cell.type = type

    @classmethod
    def path_road(self, region, start, end):
        # gonna keep it really basic with straight-ish lines for now
        # note that as of this writing this gets run before any non-traversable terrain gets drawn
        cursor = start

        while cursor != end:
            # First see if either of our options is already a road
            # this is just a funny way to get 1 or -1

            if end[0] == cursor[0]:
                yoption = None
            else:
                ychange = int((end[0] - cursor[0]) / abs(end[0] - cursor[0]))
                yoption = (cursor[0] + ychange, cursor[1])
            if end[1] == cursor[1]:
                xoption = None
            else:
                xchange = int((end[1] - cursor[1]) / abs(end[1] - cursor[1]))
                xoption = (cursor[0], cursor[1] + xchange)

            if yoption and region.getCell(*yoption).type == RCell.ROAD or not xoption:
                cursor = yoption
            elif region.getCell(*xoption).type == RCell.ROAD or not yoption:
                cursor = xoption
            else:
                # otherwise select randomly based on the diff proportions
                ydiff = self.ydistance(cursor, end)
                xdiff = self.xdistance(cursor, end)
                proportion = random.randint(0, ydiff + xdiff - 1)

                if proportion < ydiff:
                    cursor = yoption
                else:
                    cursor = xoption

            cell = region.getCell(*cursor)
            if cell.type not in [RCell.TOWN, RCell.ROAD]:
                cell.type = RCell.ROAD

    # returns the distance between two positions in terms of orthogonal movement
    @classmethod
    def distance(self, pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    @classmethod
    def ydistance(self, pos1, pos2):
        return abs(pos1[0] - pos2[0])

    @classmethod
    def xdistance(self, pos1, pos2):
        return abs(pos1[1] - pos2[1])

    @classmethod
    def header(self, title):
        diff = int( (self.CURRENT_SETTINGS['DEFAULT_WIDTH'] + 4 - len(title)) / 2)

        s = ' ' + '=' * (diff - 1)
        s += ' {} '.format(title)
        s = s.ljust(156, '=')
        print(s)


if __name__ == "__main__":
    
    r = RegionGenerate.generate_region()


    # print(r.serialize())