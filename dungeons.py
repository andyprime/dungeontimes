import uuid

class Dungeon:

    rooms = []

    free_agents = []

    def __init__(self):
        pass


class Room: 

    def __init__(self):
        self.features = []
        self.inhabitants = []

    def addInhabitant(self, creature):
        # TODO: capacity limits?
        self.inhabitants.append(creature)


    def removeInhabitant(self, creature):
        new_inhabitants = [i for i in self.inhabitants if i.id != creature.id]

        print(len(new_inhabitants))

        self.inhabitants = new_inhabitants


class Creature:

    def __init__(self, properties):
        self.id = str(uuid.uuid1())
        self.name = properties.get('name', 'baddata')
        self.job = properties.get('job', 'baddata')

        self.str = properties.get('str', 'baddata')
        self.dex = properties.get('dex', 'baddata')
        self.con = properties.get('con', 'baddata')
        self.int = properties.get('int', 'baddata')
        self.wis = properties.get('wis', 'baddata')
        self.cha = properties.get('cha', 'baddata')

    def __str__(self):
        return self.name + '; A ' + self.job + '\n Str: ' + str(self.str) + ', Dex: ' + str(self.dex) + ', Con: ' + str(self.con) + ', Int: ' + str(self.int) + ', Wis: ' + str(self.wis) + ', Cha: ' + str(self.cha)
