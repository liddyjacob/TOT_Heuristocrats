from threading import current_thread
from ai.heuristocrats.behaviors import *
from ai.heuristocrats.commander import KING
from abc import ABC

class Unit(ABC):
    def __init__(self, obj):
        self.team = obj["team"]
        self.x = obj['x']
        self.y = obj['y']
        self.move_stack = []
        self.id = obj['id']
        self.behavior_stack = []
        self.behavior_stack.append(KING.order(self))


    def execute(self, cws):
        # get an assignment from the king if there is no responibility
        behavior = self.behavior_stack[-1]

        if behavior.is_finished(self):
            self.behavior_stack.pop()

            if len(self.behavior_stack) == 0:
                self.behavior_stack.append(KING.order(self))
                
            behavior = self.behavior_stack[-1]

        # todo add behavior interruptions
        turn = behavior.execute(self)
        return(turn)

    # todo update health and stuff
    def update(self, obj):
        self.x = obj['x']
        self.y = obj['y']

class Villager(Unit):
    def __init__(self, obj):
        super().__init__(obj)


class Archer(Unit):
    def __init__(self, obj):
        super().__init__(obj)


from ai.heuristocrats.foliage_finder import initialize_foliage_state, reflect
from ai.heuristocrats.exploration import initialize_exp_weight_map, multi_aggregate, exp_render, find_target_on_heatmap
from ai.heuristocrats.utils import generate_exploration_map, getClosedIslands, printAsIs, cust_render
from ai.heuristocrats.constants import *
from ai.shitutils import get_tiles, path_to_coord



class Infantry(Unit):
    def __init__(self, obj):
        super().__init__(obj)

class Calvary(Unit):
    def __init__(self, obj):
        super().__init__(obj)


class Skeleton(Archer):
    def __init__(self, obj):
        super().__init__(obj)
