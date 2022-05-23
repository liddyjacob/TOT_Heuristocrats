from ast import Pass
from ai.heuristocrats.foliage_finder import FoliageRegisry
from ai.heuristocrats.constants import HWSIZE

class AnnotatedWorld:
    class FoliageRegisry:
        def __init__(self, size = HWSIZE):
            self.registry = {}
            self.size = size

        # update the registry with an object:
        def update(self, x, y, obj):
            

            pass

        # update crw to include new plants
        def reflect(self, crw):
            pass

    def __init__(self):
        self.foliage_registry = FoliageRegisry()

    def update(self, x,y,obj):
        self.foliage_registry.update(x,y,obj)

    def modify_world_state(self, crw):
        self.foliage_registry.reflect(crw)
