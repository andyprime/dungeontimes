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

    @classmethod
    def generateDungeon(self):


        dungeon = dungeons.Dungeon()



        self.header('Stage 1')
        dungeon.initiateGrid(self.DEFAULT_HEIGHT, self.DEFAULT_WIDTH)
        dungeon.prettyPrint()

        self.header('Stage 2')
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

        self.header('Passage Carving')

        for i in range(1, dungeon.height() - 1):
            for j in range(1, dungeon.width() - 1):

                cursor = dungeon.getCell(i, j)

                if dungeon.isSafeCarvable(cursor):

                    print('Ok lets go! {}'.format(cursor))

                    self.startGrowingTree(cursor, dungeon)

        dungeon.prettyPrint()


        self.header('Exuent')

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

            print('Pile size: {}'.format(len(pile)))

            if len(pile) == 1:
                cursor = pile[0]
            else:
                # random, middle, newest, oldest
                # for now just do oldest
                cursor = pile[-1]

            print('Cursor: {}'.format(cursor))


            options = dungeon.getPossibleCarves(cursor)
            print('Options: {}'.format(options))

            if len(options) == 0:
                # this node is exhausted, remove it from the pile
                print('Node exhausted')
                pile.remove(cursor)
                continue;
            else:

                if previous_direction in options and dice.Dice.d(1,100) < self.CHANCE_MAINTAIN_DIRECTION:
                    direction = previous_direction
                else:
                    direction = random.choice(options)

            next_cell = dungeon.getCell(*cursor.byCode(direction))

            print('Next cell selected: {}'.format(next_cell))
            pile.append(next_cell)
            dungeon.carvePassage(next_cell)

            # if count > 20:
            #     return

        print('Pile is empty')





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
    # seed = 'be8b6c94-fa93-11ed-afe2-13cd88a407db'

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

