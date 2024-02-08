import random


# OldStringsTool is confused, its creating too many hard coded objects that may never get used
# Better to use StringTool which will keep anything it needs in memory but will never load things that don't get used
#
# This system is still flawed because it doesn't let you build composite lists, might need to move to yaml

class StringTool:

    _records = {}

    @classmethod
    def random(self, source):

        if not self._records.get(source, False):
            filename = 'strings/' + source + '.txt'
            lines = open(filename).read().splitlines()
            self._records[source] = lines

        return random.choice(self._records[source])


class OldStringsTool:

    def __init__(self, sourceName):
        self.sourceName = sourceName
        self.fileName = filename = 'strings/' + sourceName + '.txt'
        self.loaded = False
        self.values = []

    def random(self):
        if not self.loaded:
            self.load()
            
        return random.choice(self.values)

    def load(self):
        lines = open(self.fileName).read().splitlines()
        self.values = lines
        self.loaded = True


    def __str__(self):
        return self.fileName + '; Loaded: ' + str(self.loaded) + ', value count: ' + str(len(self.values))

CoolNouns = OldStringsTool('coolnouns')
CoolAdjectives = OldStringsTool('cooladjectives')
CoolVerbs = OldStringsTool('coolverbs')
FirstNames = OldStringsTool('firstnames')
BasicLastNames = OldStringsTool('basiclastnames')


if __name__ == "__main__":

    # TODO: maybe write a duplicate checker in here


    print(CoolNouns)

    print()

    print(CoolNouns.random())
    print(CoolNouns.random())