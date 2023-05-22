
import factory

class Battle:

    PAPERWORK = 1
    BATTAL = 2
    OVER = 3


    def __init__(self):
        self.teams = {}
        self.conditions = []
        self.initiative = []
        self.state = Battle.PAPERWORK

    def start(self):
        print('Lets fight!')
        print()

        count = 1
        for team, members in self.teams.items():
            print('Team #{}: {}'.format(count, team))
            for fellah in members:
                print('    {}'.format(str(fellah)))
            print()
            count += 1


        self.state = Battle.BATTAL


        round_count = 1
        while (self.state == Battle.BATTAL):
            print('ROUND {}'.format(round_count))

            self.resetInitiative()



    def resetInitiative(self):
        self.initiative = []

        for team, members in self.teams.items():
            for fellah in members:

                x = fellah.generateInitiative()

                self.initiative.append( (x, fellah) )

        print(len(self.initiative))
        print(self.initiative)
        self.initiative.sort(key=lambda x: x[0])
        print()
        print(self.initiative)


    def addParticipant(self, side, creature):
        if not self.teams.get(side, False):
            self.teams[side] = []

        self.teams[side].append(creature)






if __name__ == "__main__":

    b = Battle()


    for i in range(4):
        b.addParticipant('monster', factory.CreatureFactory.randomMonster())

    for i in range(4):
        b.addParticipant('adventurer', factory.CreatureFactory.randomAdventurer()) 
        

    b.start()

    print('Ok, done.')   
