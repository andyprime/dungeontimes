import yaml
import random
import re

class StringTool:

    _records = {}

    @classmethod
    def random(self, source):
        if not self._records.get(source, False):
            self.load(source)

        if type(self._records[source]) == list:
            return random.choice(self._records[source])
        else:
            weights = [x['w'] for x in self._records[source]['options']]
            # remidner that choices always returns an array even if you only want 1 result
            main_selection = random.choices(self._records[source]['options'], weights)[0]

            gen_string = main_selection['s']
            # bits = gen_string.split(' ')
            bits = re.findall('\$[\^\w]+', gen_string)

            for bit in bits:
                if bit[0] == '$':
                    if bit[1] == '^':
                        index = bit[2:]
                    else:
                        index = bit[1:]

                    if index in self._records[source]:
                        x = random.choice(self._records[source][index])
                    else:
                        x = self.random(index)
                    if bit[1] == '^':
                        x = x.capitalize()                    
                    gen_string = gen_string.replace(bit, x, 1)

            return gen_string

    @classmethod
    def load(self, source):
        filename = 'strings/' + source + '.yaml'
        with open(filename) as stream:
            self._records[source] = yaml.safe_load(stream)

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

    for i in range(1, 1000):
        print(StringTool.random('regular_names'))

    for i in range(1, 1000):
        print(StringTool.random('dungeon_names'))