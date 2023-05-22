import random

import dungeons
import dice
import strings


class DungeonFactory:

    @classmethod
    def generateDungeon(self):
        rooms = []

        # build rooms
        for i in range(1,11):
            rooms.append(self.generateRoom(i))

        print('Generated {} rooms'.format(len(rooms)))

        # populate rooms

        # connect rooms

        for room in rooms:
            print(room)


    @classmethod
    def generateRoom(self, num):
        r = dungeons.Room(num)
        
        r.style = random.choice(['natural cavern', 'crystal cavern', 'hand-carved stonework', 'drywall finished', 'partially worked'])
        r.size = random.choice(['huge', 'spacious', 'comfortable', 'cramped', 'echoing'])


        return r



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

    print('Random Dungeon Test')
    print(DungeonFactory.generateDungeon())    


    # print('Random Adventurer Test')
    # for i in range(1,12):
    #     print(CreatureFactory.generateAdventurer())    

    # for i in range(1,10):

    #     print(NameFactory.generateRandom())
    #     print('')

