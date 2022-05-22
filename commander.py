from ai.heuristocrats.behaviors import BehaviorMoveTest

class Commander:
    def __init__(self):
        pass

    def order(self, unit):
        return BehaviorMoveTest()


KING = Commander()