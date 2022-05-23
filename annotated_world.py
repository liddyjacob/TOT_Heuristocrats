from ast import Pass
from ai.heuristocrats.foliage_finder import FoliageRegisry
from ai.heuristocrats.constants import HWSIZE, WSIZE
from ai.heuristocrats.resources import Resource, Other

class FoliageRegisry:
    def __init__(self, size = HWSIZE):
        self.registry = {}
        self.size = size

    # update the registry with an object:
    def update(self, x, y, obj):
        if x > HWSIZE:
            x = WSIZE - x - 1
        if y > HWSIZE:
            y = WSIZE - y - 1    
        
        # New object, update registry
        if self.registry.get((x,y)) is None:
            if issubclass(type(obj), Resource):
                self.registry[(x,y)] = type(obj)(None, theoretical=True)
                return
            if obj != Other.UNKNOWN:
                self.registry[(x,y)] = Other.UNOCCUPIED

    def get_reflected_coords(self, x,y):
        return [(x,y), (WSIZE - x - 1, y), (WSIZE - x - 1, WSIZE - y - 1), (x, WSIZE - y - 1)]

    def redefine_if_unknown(self, coord_set, crw):
        (base_x, base_y) = coord_set[0]
        fstate = self.registry.get((base_x,base_y))

        # no foliage state to use.
        if fstate is None:
            return

        for (x,y) in coord_set:
            if crw.get_coord((x,y)) == Other.UNKNOWN:
                crw.set_coord((x,y), fstate)

    # update crw to include new plants
    def reflect(self, crw):
        for x in range(HWSIZE):
            for y in range(HWSIZE):
                all_coords = self.get_reflected_coords(x,y)
                self.redefine_if_unknown(all_coords, crw)

class AnnotatedWorld:
    def __init__(self):
        self.foliage_registry = FoliageRegisry()

    def update(self, x,y,obj):
        self.foliage_registry.update(x,y,obj)

    def modify_world_state(self, crw):
        self.foliage_registry.reflect(crw)




ANNO_WORLD = AnnotatedWorld()