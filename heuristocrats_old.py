from asyncio.streams import FlowControlMixin
from glob import glob
from tkinter.messagebox import NO
from ai.shitutils import get_tiles, path_to_coord
from enum import Enum
from render import render
from ai.heuristocrats.constants import *
from ai.heuristocrats.foliage_finder import initialize_foliage_state, reflect
from ai.heuristocrats.exploration import initialize_exp_weight_map, multi_aggregate, exp_render, find_target_on_heatmap
from ai.heuristocrats.utils import generate_exploration_map, getClosedIslands, printAsIs, cust_render
# notes
"""
Upgrade units policy: examine cost / power for one unit, then cost / power to upgrade all units.

"""


# iterate over the map once to avoid redundancy of things that 
# require iteraton.
def iterate_over_map(mapdata):
    for x in range(WSIZE):
        for y in range(WSIZE):
            pass



def name():
    return "h-crats"

# Associate units BY ID with their corresponding class.
unit_id_map = {}

class Move:
    def __init__(self):
        pass


class Unit:
    def __init__(self, state):
        self._set_possible_moves()

    def _set_possible_moves(self):
        if (self.type == 'v'):
            self._set_villager_moves()

    def _set_villager_moves(self):
        pass

    def update_state(self, state):
        self.state = state

    def move(self, direction):
        pass


class VillagerBehaviors:
    def get_wood():
        pass



def run(world_state, players, team_idx):
    # Determine what the foliage is for unexplored tiles.

    initialize_foliage_state()
    # JUST FIND WOOD AND MINE IT!
    # dont get too complicated
    global unit_id_map
    global LOGFILE

    vils = get_tiles(world_state, lambda x: x["team"] == team_idx )


    #LOGFILE.write(str(vils) + '\n\n')
    LOGFILE.write(str(players[team_idx])+ '\n\n')
    LOGFILE.write(str(vils))

    test_unit = vils[0]
    test_u_x = test_unit['x']
    test_u_y = test_unit['y']

    reflected_map = reflect(world_state)

    iterate_over_map(iterate_over_map)

    exp_weights = initialize_exp_weight_map(world_state)
    exploration_heatmap = multi_aggregate(exp_weights, 9)

    exp_map = generate_exploration_map(reflected_map)
    islands = getClosedIslands(exp_map, WSIZE, WSIZE)

    current_island = islands[test_u_x][test_u_y]
    target = find_target_on_heatmap(exploration_heatmap, islands, current_island)

    reflected_map[target[0]][target[1]] = 'X'

    path = path_to_coord([test_u_x, test_u_y], reflected_map , [target[0], target[1]])
    direction = [path[0] - test_u_x, path[1] - test_u_y]
    commands = [{"id":test_unit["id"],"command":"m","arg":direction}]

    print(path)
    #printAsIs(islands)
    #path = path_to_coord((test_unit['x'], test_unit['y']), reflected_map, (target[0], target[1]))
    #print(path)

    #print(exploration_map)
    cust_render(reflected_map)

    return(commands)
    #vils = sorted(vils,key=lambda x: x["id"])
    #arcs = get_tiles(world_state,lambda x: x["team"] == team_idx and x["type"] == "a")
    #infs = get_tiles(world_state,lambda x: x["team"] == team_idx and x["type"] == "i")
    #hous = get_tiles(world_state,lam
    # bda x: x["team"] == team_idx and x["type"] == "h")
    #rans = get_tiles(world_state,lambda x: x["team"] == team_idx and x["type"] == "r")
    #tows = get_tiles(world_state,lambda x: x["team"] == team_idx and x["type"] == "w")