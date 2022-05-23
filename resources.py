from enum import Enum

class Other(Enum):
    UNOCCUPIED = 1
    UNKNOWN = 2


# Resources can be real or theoretical, 
# depending on if they are assumed from 
# reflection or observed.

class Resource:
    def __init__(self, obj, theoretical = False):
        self.obj_raw = obj
        self.theoretical = theoretical


class Tree(Resource):
    def __init__(self, obj, theoretical = False):
        super().__init__(obj, theoretical)
        if self.theoretical:
            self.id = -1

class Gold(Resource):
    def __init__(self, obj, theoretical = False):
        super().__init__(obj, theoretical)
        if self.theoretical:
            self.id = -2
