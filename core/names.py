import random

import strings
from core.dice import Dice

class NameFactory:
    @classmethod
    def randomByType(self, type):
        return strings.StringTool.random('monster_'+ type)

    @classmethod
    def generateRandom(self):
        rando = Dice.d(100)
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

        rando = Dice.d(6)

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
        rando = Dice.d(3)

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

