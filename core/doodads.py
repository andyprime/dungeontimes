import uuid

import definitions.model as model
from core.dice import Dice
import core.strings as strings


class Item:

    @classmethod
    def smush(self, gear, mod):

        base = {
            'code': gear.code,
            'name': gear.name,
            'effect': {}
        }
        if pre := mod.name.get('prefix', None):
            base['name'] = f"{pre} {base['name']}"
        if post := mod.name.get('postfix', None):
            base['name'] = f"{base['name']} {post}"
        for prop in self.props:
            base[prop] = getattr(gear, prop)

        # these should always be present and on the main object
        for prop in ['rarity', 'value']:
            base[prop] = self._mod(getattr(gear, prop), mod.effect.get(prop, 0), mod.effect.get(f'{prop}_mod', 0))

        for effect in self.smushables:
            base['effect'][effect] = self._mod(gear.effect.get(effect, 0), mod.effect.get(effect, 0), mod.effect.get(f'{effect}_mod', 0))

        return base

    @classmethod
    def _mod(self, base, additive, percent):
        start = base + additive
        modded = start + int( (start * percent) / 100)
        return modded

    def __init__(self, props):
        self.id = str(uuid.uuid1())
        self.weight = 1
        self.name = props['name'].capitalize()
        self.value = props['value']

    def wearable(self):
        return False

    def consumable(self):
        return False

    def tool(self):
        return False

    def useless(self):
        return not self.wearable() and not self.consumable() and not self.tool()

    def data_format(self):
        return {
            'id': self.id,
            'name': self.name,
            'value': self.value,
            'weight': self.weight
        }

    def __str__(self):
        return 'Item: {}'.format(self.name)

    def __repr__(self):
        return 'Item: {}'.format(self.name)

class Equipable(Item):
    
    props = ['slot']
    smushables = ['encumberance', 'armor', 'style']

    @classmethod
    def generate(self, max_rarity=2):
        f = lambda r: r.rarity <= max_rarity
        combined = self.smush(model.Gear.random(f), model.GearMod.random(f))
        return Equipable(combined)

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
            'id': self.id,
            'slot': self.slot,
            'code': self.code,
            'rarity': self.rarity,
            'name': self.name,
            'weight': self.weight
        }
        return base | super().data_format()

class Tool(Item):

    props = ['type', 'size', 'grants']
    smushables = ['power', 'style']

    @classmethod
    def generate(self, max_rarity=2):
        f = lambda r: r.rarity <= max_rarity
        combined = self.smush(model.Tool.random(f), model.ToolMod.random(f))
        return Tool(combined)

    def tool(self):
        return True

    def __init__(self, props):
        super().__init__(props)

        self.code = props['code']
        self.rarity = props['rarity']
        self.type = props['type']
        self.size = props['size']
        self.grants = props['grants']
        self.effect = props['effect']

    def data_format(self):
        base = {
            'id': self.id,
            'code': self.code,
            'rarity': self.rarity,
            'name': self.name,
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