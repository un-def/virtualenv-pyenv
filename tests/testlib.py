import json
from pathlib import Path


FIXTURE_PATH = Path(__file__).parent / 'python_spec_fixture.json'


with open(FIXTURE_PATH) as fobj:
    python_spec_fixture = json.load(fobj)
