import pytest

import definitions

import core.critters

@pytest.mark.parametrize('className', ['Classes', 'Monsters', 'Moves', 'Spells', 'Stocks', 'Gear', 'GearMod', 'Tool', 'ToolMod', 'Consumable', 'Follower', 'Condition', 'Trap'])
def test_coreModelFeatures(className):
    # Just testing to make sure all models load and parse according to their schemas
    c = getattr(definitions.model, className)

    a = c.all()

    # It should be a list no matter what
    assert type(a) == list
    # If its empty that means something has gone wrong with the YAML or loading
    assert len(a) > 0
    assert type(a[0]) == c

    assert type(c.random()) == c

def test_classes():
    # just makin' sure all the attributes specified in class definitions are real
    for cl in definitions.model.Classes.all():
        for attr in cl.attrs['primary'] + cl.attrs['secondary']:
            assert attr in core.critters.Creature.ATTRIBUTE_NAMES.keys()

def test_class_moves():

    for cl in definitions.model.Classes.all():

        for code in cl.moves:

            try:
                move = definitions.model.Moves.find(code)
            except ValueError:
                pytest.fail(f'Unable to find move "{code}" specified in class "{cl.code}"')
            assert code == move.code


def test_tool_granting():
    # verifying that all moves described in a Tool's grants field actually exist

    for tool in definitions.model.Tool.all():

        try:
            move = definitions.model.Moves.find(tool.grants)
        except ValueError:
            pytest.fail(f'Unable to find move "{tool.grants}" specified in tool "{tool.code}"')
        assert tool.grants == move.code, "Nope"
        
def test_filter():

    types = []
    for i in range(100):
        c = definitions.model.Condition.random(lambda c: c.type in ['injury'])
        types.append(c.type)

    assert len(set(types)) == 1

def test_trap_conditions():

    for trap in definitions.model.Trap.all():
        code = trap.effect.get('condition')
        if code:
            try:
                condition = definitions.model.Condition.find(code)
            except ValueError:
                pytest.fail(f'Unable to find condition "{code}" specified in trap "{trap.code}"')