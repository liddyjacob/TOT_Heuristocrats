from enum import Enum

class Other(Enum):
    UNOCCUPIED = 1
    UNKNOWN = 2

class Resource:
    def __init__(self, obj):
        self.obj_raw = obj

class Tree(Resource):
    def __init__(self, obj):
        super().__init__(obj)

class Gold(Resource):
    def __init__(self, obj):
        super().__init__(obj)
