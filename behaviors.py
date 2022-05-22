from ai.heuristocrats.moves import Move

class Behavior:
    def __init__(self):
        pass

# Just 
class BehaviorMoveTest(Behavior):
    def __init__(self):
        self.move_stack = [Move([1,0]), Move([0,1]), Move([-1,0]), Move([0,-1])]

    def execute(self, unit):
        move = self.move_stack[-1]
        self.move_stack.pop()
        return move.apply(unit)

    def is_finished(self, unit):
        return (len(self.move_stack) == 0)



