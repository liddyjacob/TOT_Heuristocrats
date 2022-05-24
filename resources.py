
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
        self.island_ids = set()
        if not self.theoretical:
            self.id = obj['id']
            self.x = obj['x']
            self.y = obj['y']
        else:
            self.id = -1

class Tree(Resource):
    def __init__(self, obj, theoretical = False):
        super().__init__(obj, theoretical)

class Gold(Resource):
    def __init__(self, obj, theoretical = False):
        super().__init__(obj, theoretical)

class Unknown(MapObj):
    def __init__(self):
        super().__init__(True)

class Unoccupied(MapObj):
    def __init__(self, theoretical = False):
        super().__init__(theoretical)