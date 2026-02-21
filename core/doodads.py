import definitions.model as model

from core.dice import Dice
import core.strings as strings

class Item:

    def __init__(self, props):

        self.weight = 1
        self.name = props['name']
        self.value = props['value']

    def wearable(self):
        return False

    def consumable(self):
        return False

    def data_format(self):
        return {
            'name': self.name,
            'value': self.value,
            'weight': self.weight
        }

    def __str__(self):
        return 'Item: {}'.format(self.name)

    def __repr__(self):
        return 'Item: {}'.format(self.name)


class Equipable(Item):
    
    @classmethod
    def generate(self, max_rarity=2):
        f = lambda r: r.rarity <= max_rarity
        gear = model.Gear.random(f)
        gear_mod = model.GearMod.random(f)

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

        self.slot = props['slot']
        self.code = props['code']
        self.rarity = props['rarity']
        self.effect = props['effect']

    def wearable(self):
        return True

    def data_format(self):
        base = {
            'slot': self.slot,
            'code': self.code,
            'rarity': self.rarity,
            'name': self.name,
            'weight': self.weight
        }
        return base | super().data_format()

class Consumable(Item):

    @classmethod
    def generate(self, max_rarity=2):
        cons = model.Consumable.random(lambda r: r.rarity <= max_rarity)

        return Consumable(cons.raw)

    def consumable(self):
        return True

    def __init__(self, props):
        super().__init__(props)

        self.code = props['code']
        self.rarity = props['rarity']
        self.effect = props['effect']


class Valuable(Item):

    @classmethod
    def generate(self):
        return Valuable({
            'name': strings.StringTool.random('valuables', indefinite=True), 
            'value': Dice.roll('3d10')
            })


if __name__ == "__main__":
    
    x = Equipable.generate()

    print(x)
    print(x.data_format())

    y = Valuable.generate()
    print(y)

    z = Consumable.generate()
    print(z)