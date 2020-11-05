import random

class StringsTool:

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
        # TODO: make sure there's no whitespace lines
        lines = open(self.fileName).read().splitlines()
        self.values = lines
        self.loaded = True


    def __str__(self):
        return self.fileName + '; Loaded: ' + str(self.loaded) + ', value count: ' + str(len(self.values))


CoolNouns = StringsTool('coolnouns')
CoolAdjectives = StringsTool('cooladjectives')
CoolVerbs = StringsTool('coolverbs')
FirstNames = StringsTool('firstnames')
BasicLastNames = StringsTool('basiclastnames')


if __name__ == "__main__":

    # TODO: maybe write a duplicate checker in here


    print(CoolNouns)

    print()

    print(CoolNouns.random())
    print(CoolNouns.random())