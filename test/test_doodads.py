import pytest

import definitions
import core.doodads as doodads


pretend_gear = definitions.model.Gear({
        'name': 'leather armor',
        'code': 'leatherarmor',
        'slot': 'torso',
        'rarity': 1,
        'value': 20,
        'effect': {
          'armor': 10,
          'style': 2
        }
    })

pretend_gearmod = definitions.model.GearMod({
        'code': 'heavy',
        'rarity': 1,
        'name': {
          'prefix': 'heavy'
        },
        'effect': {
              'armor_mod': 20,
              'style': -1
        }
    })

pretend_tool = definitions.model.Tool({
        'name': 'sword',
        'code': 'sword',
        'type': 'melee',
        'size': 'small',
        'grants': 'N/A',
        'rarity': 1,
        'value': 20,
        'effect': {
          'power': 10,
          'style': 2
        }
    })

pretend_toolmod = definitions.model.ToolMod({
        'code': 'heavy',
        'rarity': 1,
        'name': {
          'prefix': 'heavy'
        },
        'effect': {
              'power_mod': -20,
              'style': -1
        }
    })

def test_gear_smushing():
    # doodads don't have a ton of distinct functionality so we're just testing the mod application function atm

    smushed = doodads.Equipable(doodads.Equipable.smush(pretend_gear, pretend_gearmod))

    assert smushed.name == 'Heavy leather armor'
    assert smushed.effect['armor'] == 12
    assert smushed.effect['style'] == 1

def test_tool_smushing():
    smushed = doodads.Tool(doodads.Tool.smush(pretend_tool, pretend_toolmod))

    assert smushed.name == 'Heavy sword'
    assert smushed.effect['power'] == 8
    assert smushed.effect['style'] == 1
