import yaml
import random
import re

'''
     String Tool
    ------------

    This is a little doodad for generating random names with some heirarchical syntax. The only
    call at the moment is StringTool.random('somesource'), which we'll call the root source.
    The root source will always look for the associated yaml file.

    These yaml files should take one of the following forms:
        1) A plain yaml list, when called as a source a single entry will be selected randomly

        2) A yaml file that contains an object that contains an array named "options" followed 
            by any number of local sources

            options is a list of objects from which the tool will select to build our string
              each should contain two fields:
                s: the string format to build, using (hopefully) straightforward interpolation
                w: an integer, the weight that the random selection will use for this value

            local sources are optional but are named lists that can only be referenced by
            the string fields in the same file's options object 

    String interpolation rules:
        * Anything encapsulated with ${} is a reference to a source. The tool will match local
          sources first, and failing that will attempt to load a string file matching the name

        * Some control characters can be inserted as the first character after the ${

            ^ - will capitalize the selected string
            (more to come, as needed)

        * Everything else is a string literal, you know the drill    

    Note that by default the tool will create a local cache of all files loaded so far. 

'''

class StringTool:

    _records = {}

    location = 'strings/'

    @classmethod
    def random(self, source):
        if not self._records.get(source, False):
            self._load(source)

        if type(self._records[source]) == list:
            return random.choice(self._records[source])
        else:
            try:
                weights = [x['w'] for x in self._records[source]['options']]
            except: 
                raise ValueError('Strings source file missing weight attribute: "{}"'.format(source))

            # reminder that choices always returns an array even if you only want 1 result
            main_selection = random.choices(self._records[source]['options'], weights)[0]

            gen_string = main_selection['s']
            bits = re.findall(r"\$\{[\^\w]+\}", gen_string)

            for bit in bits:
                if bit[0] == '$':
                    if bit[2] == '^':
                        index = bit[3:-1]
                    else:
                        index = bit[2:-1]

                    if index in self._records[source]:
                        x = random.choice(self._records[source][index])
                    else:
                        x = self.random(index)
                    if bit[2] == '^':
                        x = x.capitalize()                    
                    gen_string = gen_string.replace(bit, x, 1)

            return gen_string

    @classmethod
    def clear_cache(self):
        _records = {}

    @classmethod
    def _load(self, source):
        filename = self.location + source + '.yaml'
        try:
            with open(filename) as stream:
                self._records[source] = yaml.safe_load(stream)
        except: 
            raise ValueError('Unable to find strings file: "{}"'.format(source))


if __name__ == "__main__":

    for i in range(1, 1000):
        print(StringTool.random('band_names'))
