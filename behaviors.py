from re import U
from ai.heuristocrats.moves import Move

# TODO Make Dumb behavior that just builds a damn town center. 
# that way I can move on and build more programs

class Behavior:
    def __init__(self):
        pass

# Just 
class BehaviorMoveTest(Behavior):
    def __init__(self):
        self.move_stack = [Move([1,0]), Move([0,1]), Move([-1,0]), Move([0,-1])]

    def execute(self, unit, cws):
        move = self.move_stack[-1]
        self.move_stack.pop()
        return move.apply(unit)

    def is_finished(self, unit):
        return (len(self.move_stack) == 0)

from ai.shitutils import find_good_buildsite
class BehaviorBuildTownTest(Behavior):
    def __init__(self, type):
        self.target_location = None

    # Need to determine where strategically.
    def execute(self, unit, cws):
        if self.target_location is None:
            self.target_location = find_good_buildsite(cws.world_state_raw, unit.x, unit.y, 3)
            

    def is_finished(self, unit):
        return False

class BehaviorBuild(Behavior):
    def __init__(self, type):
        self.goal = type

    # Need to determine where strategically.
    def execute(self, unit, cws):
        pass

    def is_finished(self, unit):
        return False

from ai.heuristocrats.exploration import initialize_exp_weight_map, multi_aggregate, exp_render, find_target_on_heatmap
from ai.heuristocrats.foliage_finder import initialize_foliage_state, reflect
from ai.heuristocrats.utils import generate_exploration_map, getClosedIslands, printAsIs, cust_render
from ai.heuristocrats.constants import *
from ai.shitutils import *

class BehaviorExploreFoliage(Behavior):
    def __init__(self):
        pass

    def execute(self, unit, cws):
        reflected_map = reflect(cws.world_state_raw)

        exp_weights = initialize_exp_weight_map(cws.world_state_raw)
        exploration_heatmap = multi_aggregate(exp_weights, 9)

        exp_map = generate_exploration_map(reflected_map)
        islands = getClosedIslands(exp_map, WSIZE, WSIZE)

        current_island = islands[unit.x][unit.y]
        target = find_target_on_heatmap(exploration_heatmap, islands, current_island)

        path = path_to_coord([unit.x, unit.y], reflected_map , [target[0], target[1]])
        direction = [path[0] - unit.x, path[1] - unit.y]

        move = Move(direction)
        return move.apply(unit)


    def is_finished(self, unit):
        return False



class BehaviorExplore(Behavior):
    def __init__(self):
        pass

    def execute(self, unit, cws):
        reflected_map = reflect(cws.world_state_raw)

        exp_weights = initialize_exp_weight_map(cws.world_state_raw)
        exploration_heatmap = multi_aggregate(exp_weights, 9)

        exp_map = generate_exploration_map(reflected_map)
        islands = getClosedIslands(exp_map, WSIZE, WSIZE)

        current_island = islands[unit.x][unit.y]
        target = find_target_on_heatmap(exploration_heatmap, islands, current_island)

        path = path_to_coord([unit.x, unit.y], reflected_map , [target[0], target[1]])
        direction = [path[0] - unit.x, path[1] - unit.y]

        move = Move(direction)
        return move.apply(unit)


    def is_finished(self, unit):
        return False

