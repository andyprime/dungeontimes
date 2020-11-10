import uuid

class Dungeon:

    rooms = []

    free_agents = []

    def __init__(self):
        pass


class Room: 

    def __init__(self, number):
        self.number = number
        self.entrance = False
        self.style = 'init'
        self.size = 'init'
        self.features = []
        self.inhabitants = []
        self.connections = []

    def __str__(self):
        line1 = 'Room {}. A {} room in the {} style.'.format(self.number, self.size, self.style)
        if len(self.inhabitants) > 0:
            line2 = 'Currently inhabited by some folks'
        else:
            line2 = 'Currently unoccupied'
        line3 = 'Connects to rooms {}'.format(', '.join(self.connections))
        return line1 + "\n" + line2 + "\n" + line3


    def addInhabitant(self, creature):
        # TODO: capacity limits?
        self.inhabitants.append(creature)


    def removeInhabitant(self, creature):
        new_inhabitants = [i for i in self.inhabitants if i.id != creature.id]
        self.inhabitants = new_inhabitants


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

    def __str__(self):
        return self.name + '; ' + self.stock + ' ' + self.job + '\n Str: ' + str(self.str) + ', Dex: ' + str(self.dex) + ', Con: ' + str(self.con) + ', Int: ' + str(self.int) + ', Wis: ' + str(self.wis) + ', Cha: ' + str(self.cha)
