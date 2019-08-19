import json


class ActionList(object):

  def __init__(self):
    self.map = {}

  def add_json(self, file):
    with open(file) as f:
      jsonfile = json.load(f)
    for shorthand in jsonfile:
      self.map[shorthand] = jsonfile[shorthand]

  def shorthands(self):
    return self.map.keys()


if __name__ == "__main__":
  a = ActionList()
  a.add_json('cfg/static_calib.json')