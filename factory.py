import random
import uuid

import dungeons
import dice
import strings
import critters


# All this nonsense is deprecated, but it can live a little longer for reference

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

        return critters.Creature(data)

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

        return critters.Creature(data)


class NameFactory:
    @classmethod
    def randomByType(self, type):
        return strings.StringTool.random('monster_'+ type)

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
    d = DungeonFactoryAlpha.generateDungeon()

    s = d.serialize()

    d2 = dungeons.Dungeon(s)
    d2.prettyPrint()

    s2 = d2.serialize()

    print(s == s2)

    print('Seed : {}'.format(seed))
