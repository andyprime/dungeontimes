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

