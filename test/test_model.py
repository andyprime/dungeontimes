import pytest

import definitions

# Currently none of the models have any special features unique to them, so this should be enough

@pytest.mark.parametrize('className', ['Classes', 'Monsters', 'Moves', 'Spells', 'Stocks'])
def test_coreModelFeatures(className):
    c = getattr(definitions.model, className)

    a = c.all()
    # It should be a list no matter what
    assert type(a) == list
    # If its empty that means something has gone wrong with the YAML or loading
    assert len(a) > 0
    assert type(a[0]) == c

    # this one is commented out for the moment since not all definitions have been given the code property
    #assert type(c.find(a[0].code)) == c
    assert type(c.random()) == c
