
# Resources can be real or theoretical, 
# depending on if they are assumed from 
# reflection or observed.

class MapObj:
    def __init__(self, theoretical):
        self.theoretical = theoretical

class Resource(MapObj):
    def __init__(self, obj, theoretical = False):
        super().__init__(theoretical)
        self.obj_raw = obj


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

class Unknown(MapObj):
    def __init__(self):
        super().__init__(True)

class Unoccupied(MapObj):
    def __init__(self, theoretical = False):
        super().__init__(theoretical)