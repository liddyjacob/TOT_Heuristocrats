from ai.heuristocrats.behaviors import *

class Unit:
    def __init__(self, obj):
        self.team = obj["team"]
        self.move_stack = []

    def execute(self):
        return ({})

class Villager(Unit):
    def __init__(self, obj):
        super().__init__(obj)

class Archer(Unit):
    def __init__(self, obj):
        super().__init__(obj)

class Infantry(Unit):
    def __init__(self, obj):
        super().__init__(obj)

class Calvary(Unit):
    def __init__(self, obj):
        super().__init__(obj)

class Skeleton(Archer):
    def __init__(self, obj):
        super().__init__(obj)