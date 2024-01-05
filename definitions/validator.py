# just a dumb util for making sure no errors get introduced into the yamls
# until there's a more robust solution for this

import yaml

files = ['monsters.yaml', 'moves.yaml', 'classes.yaml']

for f in files:
    print('Parsing {}'.format(f))
    s = open(f, 'r')
    x = list(yaml.safe_load_all(s))

print('All done')