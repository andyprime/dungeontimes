from definitions.model import Gear, GearMod

class Item:

    def __init__(self, props):

        self.weight = 1
        self.value = props['value']


class Equipable(Item):
    
    @classmethod
    def generate(self, max_rarity=2):
        f = lambda r: r.rarity <= max_rarity
        gear = Gear.random(f)
        gear_mod = GearMod.random(f)

        props = {
            'code': gear.code,
            'name': '{} {}'.format(gear_mod.prefix, gear.name),
            'slot': gear.slot,
            'effect': {}
        }

        props['rarity'] = max(gear.rarity + gear_mod.effect.get('rarity', 0), 0)
        value = max(gear.value + gear_mod.effect.get('value', 0), 0)
        props['value'] = value + int( value * (gear_mod.effect.get('value_mod', 0) / 100) )
        
        for eff in ['encumberance', 'armor', 'style']:
            base = gear.effect.get(eff, 0) + gear_mod.effect.get(eff, 0)
            modded = base + int(base * (gear_mod.effect.get('{}_mod', 0) / 100) )
            props['effect'][eff] = modded

        return Equipable(props)

    def __init__(self, props):
        super().__init__(props)

        self.name = props['name']
        self.slot = props['slot']
        self.code = props['code']
        self.rarity = props['rarity']
        self.effect = props['effect']

    def __str__(self):
        return 'Equipable Item: {}'.format(self.name)

    def __repr__(self):
        return 'Equipable: {}'.format(self.name)


if __name__ == "__main__":
    
    x = Equipable.generate()

    print(x)