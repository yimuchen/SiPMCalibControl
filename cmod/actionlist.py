import json


class ActionList(object):
  def __init__(self):
    self.map = {}

  def add_json(self, file):
    with open(file) as f:
      jsonfile = json.load(f)
    for shorthand in jsonfile:
      self.map[shorthand] = jsonfile[shorthand]
      if 'message' not in self.map[shorthand]:
        self.map.pop(shorthand)
        print(('[MALFORMED USERACTION] Expects a message string! '
               'User action [{0}] will be excluded').format(shorthand))
      if 'set' not in self.map[shorthand]:
        self.map.pop(shorthand)
        print(('[MALFORMED USERACTION] Expects a set list! '
               'User action [{0}] will be excluded').format(shorthand))
      if type(self.map[shorthand]['set']) != list:
        self.map.pop(shorthand)
        print(('[MALFORMED USERACTION] Expects a set list! '
               'User action [{0}] will be excluded').format(shorthand))

  def shorthands(self):
    return self.map.keys()

  def getmessage(self, shorthand):
    return self.map[shorthand]["message"]

  def getset(self, shorthand):
    return self.map[shorthand]["set"]


if __name__ == "__main__":
  a = ActionList()
  a.add_json('cfg/useractions.json')
  for s in a.shorthands():
    print(a.getmessage(s))
    print(a.getset(s))
