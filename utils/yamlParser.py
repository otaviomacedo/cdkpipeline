import yaml


def readYaml(path: str):
    with open(path) as file:
        res = yaml.load(file, yaml.FullLoader)
    return res


def readManifest(paths: [str]):
    res = []
    for filename in paths:
        if filename.endswith(('.yaml', '.yml')):
            with open(filename) as file:
                for data in yaml.load_all(file, yaml.SafeLoader):
                    res.append(data)
    # os.print(res)
    return res
