

class Expedition:

    READY = 1
    MOVING = 2
    BATTLE = 3
    RECOVER = 4
    EXITING = 5
    SCATTERED = 6
    COMPLETE = 7

    def __init__(self, dungeon, party):

        self.dungeon = dungeon
        self.party = party

        self.cursor = dungeon.entrance()
        self.status = Expedition.READY

        self.processors = []

    def registerProcessor(self, callback):
        self.processors.append(callback)

    def processMessage(self, message):
        for f in self.processors:
            f(message)

    def begin(self):


        while (self.status != Expedition.COMPLETE):

            if (self.status == Expedition.READY):

                self.processMessage('The party is attempting to navigate the dungeon.')

                self.status = Expedition.MOVING

            elif (self.status == Expedition.MOVING):

                self.processMessage('The party is moving down the passageway. Or they would if it was implemented.')

                self.status = Expedition.COMPLETE

            else:
                self.processMessage('Unknown expedition status: {}'.format(self.status))
