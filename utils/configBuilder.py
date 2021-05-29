import json
from dictor import dictor


class WmpConfig:
    def __init__(self, path: str, env: str):
        # default to test if no env provided
        if not env:
            env = "test"

        with open(path) as f:
            self.data = json.load(f)[env]

    def getValue(self, path: str):
        res = dictor(self.data, path)
        if not res:
            raise Exception('No value found for ' + path)
        return res
