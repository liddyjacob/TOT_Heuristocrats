
class Move:
    def __init__(self, direction):
        self.direction = direction

    def apply(self, unit):
        return {"id": unit.id, "command":"m", "arg":self.direction}
