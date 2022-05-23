from ai.heuristocrats.behaviors import BehaviorExplore, BehaviorMoveTest, BehaviorExploreFoliage

class Commander:
    def __init__(self):
        pass

    def order(self, unit):
        # dumbass python thing to avoid circular dependancy
        from ai.heuristocrats.units import Villager, Infantry

        if type(unit) == Villager:
            # todo make sure behaviors use annotated
            # maps so that they can follow a plan
            print(unit.unit_number)

            return BehaviorMoveTest()

        if type(unit) == Infantry:
            # todo make soldires follow batallion commands in groups
            # some soldires should be independant, but not all.

            # TODO check if foliage needs explored
            # starts at 1 cause I am dum
            if (unit.unit_number == 1):
                return BehaviorExploreFoliage()

            return BehaviorExplore()

KING = Commander()