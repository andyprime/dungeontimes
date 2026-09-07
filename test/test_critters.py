import core.critters
import definitions.model as model

# delver stuff

class TestDelver:

    def test_delver(self):
        d = core.critters.Delver.random()
        assert type(d) == core.critters.Delver


    def test_attr_stuff(self):

        d = core.critters.Delver.test_delver()

        assert d.calc_attr('BEEFINESS') == 10
        assert d.calc_parent('MUSCULARITY') == 10

        d.set_attr('BEEFINESS', 14)

        assert d.calc_attr('BEEFINESS') == 14
        assert d.calc_parent('MUSCULARITY') == 11

        assert d.calc_test_value('BEEFINESS', 'COOL') == 19

        d.add_move(model.Moves.find('REGIMEN'))

        assert d.calc_attr('ATHLETICISM') == 15
        assert d.calc_parent('MUSCULARITY') == 12
        assert d.calc_test_value('BEEFINESS', 'ATHLETICISM') == 21

    def test_advancement(self):

        d = core.critters.Delver.test_delver()

        assert not d.can_advance()

        d.apply_xp(20)

        assert d.can_advance()

        pre_advance = d.attr.copy()        
        raises = d.advance()

        assert len(raises) == 2

        # verify that two attributes changed
        c = 0
        for name, value in d.attr.items():
            if pre_advance[name] != value:
                c += 1

        assert c == 2

    def test_conditions(self):

        d = core.critters.Delver.test_delver()

        cold = model.Condition.find('COLD')

        d.apply_condition(cold)

        assert len(d.conditions) == 1

        assert d.calc_attr('BEEFINESS') == 8
        assert d.calc_attr('COOL') == 8

        d.heal_condition('rest')

        assert len(d.conditions) == 0

        dep = model.Condition.find('DEPRESSED')
        d.apply_condition(dep)

        assert d.calc_attr('BRAVADO') == 5
        assert d.calc_attr('DISAFFECTION') == 15

        d.heal_condition('any')

        assert len(d.conditions) == 0

        sprain = model.Condition.find('SPRAIN')
        d.apply_condition(cold)
        d.apply_condition(sprain)

        assert len(d.conditions) == 2

        d.heal_condition('rest', 1)

        assert len(d.conditions) == 1

