import random

class Expedition:

    READY = 1
    MOVING = 2
    BATTLE = 3
    RECOVER = 4
    EXITING = 5
    SCATTERED = 6
    COMPLETE = 7
    ERROR = 8

    def __init__(self, dungeon, party):

        self.dungeon = dungeon
        self.party = party

        self.cursor = dungeon.entrance()
        self.status = Expedition.READY

        self.steps = 0

        # if set it is the cells we are currently trying to navigate through
        self.path = []

        # Got to log which sections of the map have already been explored
        # So for now we're gonna keep the cell coords in an array to reference
        self.history = []
        self.history.append(self.cursor.coords)

        self.processors = []

    def registerProcessor(self, callback):
        self.processors.append(callback)

    def processMessage(self, message):
        for f in self.processors:
            f(message)

    def begin(self):

        while (self.status not in [Expedition.COMPLETE, Expedition.ERROR]):
            self.steps += 1

            if (self.status == Expedition.READY):

                self.processMessage('The party is attempting to navigate the dungeon.')

                # Nothing needs to go here just yet but we're gonna formalize it as a step for clarity and future use

                self.status = Expedition.MOVING

            elif (self.status == Expedition.MOVING):

                self.processMessage('The party is deciding where to go.')

                # just going to implement a real basic navigation system for now
                # if there are unexplored cells adjacent to our current location just pick one at random and go there
                # otherwise find the closest unexplored cell and chart a course to there


                neighbors = self.dungeon.getNeighbors(self.cursor)
                easyDirections = [n for n in neighbors if n.coords not in self.history]

                if self.path:
                    destination = self.path.pop()
                else:
                    if easyDirections:
                        destination = random.choice(easyDirections)
                    else:

                        # time to Dijkstra

                        self.path = self.generatePath()

                        self.processMessage('Generated this path: {}'.format(self.path))
                        destination = self.path.pop()

                if destination:
                    self.cursor = destination

                    if self.cursor.isRoom():
                        for cell in self.dungeon.getRoomBrethren(self.cursor):
                            if cell not in self.history:
                                self.history.append(cell.coords)
                    else:
                        self.history.append(self.cursor.coords)
                    self.processMessage('Moving to {}'.format(self.cursor.coords))
                else:
                    self.processMessage('Moving algorithm did not produce a destination')
                    self.status = Expedition.ERROR

                if self.steps % 20 == 0:
                    self.historyMap()

                # if len(self.path) > 20:
                #     self.historyMap()
                #     print(len(self.path))
                #     pizza.ham()

            else:
                self.processMessage('Unknown expedition status: {}'.format(self.status))

    def historyMap(self):
        for index, row in enumerate(self.dungeon.grid):

            display = '{}: '.format(str(index).rjust(4, ' '))

            for cell in row:
                if cell == self.cursor:
                    display += 'P'
                elif cell in self.path:
                    display += '\033[93m' + cell.positiveSymbol() + '\033[0m'
                elif cell.coords in self.history:
                    display += '\033[94m' + cell.positiveSymbol() + '\033[0m'
                else:
                    display += cell.symbol()
            print(display)
        print('\n')

    def generatePath(self):
        # just a basic dijkstra implementation that stops once it finds an unexplored cell

        distance = {}
        previous = {}
        q = []

        for cell in self.dungeon.allCells(navigable=True):
            distance[cell] = 1000000
            previous[cell] = None
            q.append(cell)

        distance[self.cursor] = 0

        while len(q) > 0:
            lowest = q[0]
            for cell in q:
                if distance[cell] < distance[lowest]:
                    lowest = cell
            q.remove(lowest)

            if lowest.coords not in self.history:
                break

            neighbors = self.dungeon.getNeighbors(lowest)
            for neighbor in [n for n in neighbors if n in q]:
                newDistance = distance[lowest] + 1 if distance[lowest] else 1

                if newDistance < distance[neighbor]:
                    distance[neighbor] = newDistance
                    previous[neighbor] = lowest

        if len(q) == 0:
            print('UH OH')
            pizza.ham()

        c = lowest
        path = []
        while(previous.get(c, False)):
            path.append(previous[c])
            c = previous[c]

        return path