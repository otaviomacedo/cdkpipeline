import json


def readJson(path: str):
    with open(path) as file:
        data = json.load(file)
    return data