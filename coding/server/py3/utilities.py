import time
import yaml
import os

def getElapsedTime(startTime):
    elapsedTime = time.time() - startTime
    hours = elapsedTime // 360
    minutes = (elapsedTime - hours * 360) // 60
    seconds = (elapsedTime - hours * 360 - minutes * 60)
    return "{}h {}m {}s".format(int(hours), int(minutes), int(seconds))


def read_yaml(file_path):
    file_path = os.path.join(os.path.dirname(__file__), file_path)
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)