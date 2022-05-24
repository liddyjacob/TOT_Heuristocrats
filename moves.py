from ai.heuristocrats.buildings import Townhall, Barracks, Range, Stable, House

class Move:
    def __init__(self, direction):
        self.direction = direction

    def apply(self, unit):
        return {"id": unit.id, "command":"m", "arg":self.direction}

    def __str__(self):
        return f"move: {self.direction}"

class Build:
    def __init__(self, type, direction):
        self.direction = direction
        self.type = type
        self.rep = type.rep()

    def apply(self, unit):
        return {"id": unit.id, "command":self.rep, "arg":self.direction}

    def __str__(self):
        return f"build:{self.rep} - {self.direction}"    


class Repair:
    def __init__(self, bld):
        self.bld_id = bld.id
        self.bld = bld
    
    def apply(self, unit):
        return {"id": unit.id, "command":'f', "arg":self.bld_id}

    def __str__(self):
        return f"repair: {self.bld_id} at {self.bld.x}, {self.bld.y}"    
