import pytest

import definitions


@pytest.mark.parametrize('className', ['Classes', 'Monsters', 'Moves', 'Spells', 'Stocks', 'Gear', 'GearMod', 'Consumable'])
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

def test_tool_granting():
    # verifying that all moves described in a Tool's grants field actually exist

    for tool in definitions.model.Tool.all():

        try:
            move = definitions.model.Moves.find(tool.grants)
        except ValueError:
            pytest.fail(f'Unable to find move "{tool.grants}" specified in tool "{tool.code}"')
        assert tool.grants == move.code, "Nope"
        