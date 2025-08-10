import glob
import pytest

from core.strings import StringTool


@pytest.fixture
def locations():
    return ['strings/', 'test/strings/']


# yield fixture to convert the tool over to using test process specific string files
@pytest.fixture
def cache_wrapper(locations):
    StringTool.clear_cache()
    StringTool.location = locations[1]

    yield

    StringTool.clear_cache()
    StringTool.location = locations[0]

class TestStrings:

    # Just a brute force test of every normal yaml spec to make (pretty) sure there's no 
    # invalid definitions in there. Pretty fast despite all the file management.
    def test_everything(self, locations): 
        for file in glob.glob('*.yaml'.format(locations[0]), root_dir=locations[0]):
            # nip the .yaml off
            shortname = file[0:-5]
            print(shortname)
            for i in range(100):
                s = StringTool.random(shortname)
                assert(type(s) == str)

    def test_handling(self):
        # the only failure state in StringTool should be requesting a bad file
        with pytest.raises(ValueError):
            StringTool.random('__________')

    def test_rules(self, cache_wrapper):
        # test the string capitalization
        assert(StringTool.random('cap') == 'It Worked')
