from tkinter import Y
from ai.heuristocrats.constants import *
from copy import deepcopy
import math

from engine import MAP_SIZE

EXP_MASK = None

def initialize_exp_weight_map(mapdata):
    return ([[1 if piece == 'u' else 0 for piece in row] for row in mapdata])

def initialize_exp_mask():
    global EXP_MASK
    EXP_MASK = []
    for x in range(WSIZE):
        xl = []
        for y in range(WSIZE):
            this_weight = math.sqrt(
                (abs(x - HWSIZE) + HWSIZE) * (abs(y - HWSIZE) + HWSIZE)
            ) / (2 * WSIZE)
            xl.append(this_weight)
        EXP_MASK.append(xl)

initialize_exp_mask()


def valid_coordinate(x,y):
    return ((x >= 0) and x < WSIZE) and ((y >= 0) and y < WSIZE)

# get the nearby coordinates of x and y, and enforce them to 
# pass valid_coordinates(x,y)
# 
def get_nearby_coords(x,y):
    nearby_coords = [(x-1,y), (x, y-1), (x+1, y), (x, y+1)] 
    valid_coords = [(x,y) for (x,y) in nearby_coords if valid_coordinate(x,y)]
    
    return (valid_coords)

def aggregate_weight(exp_weight_map):
    base_weights = deepcopy(exp_weight_map)

    for x in range(WSIZE):
        for y in range(WSIZE):
            # add up nearby coordinatrs
            neighbors = get_nearby_coords(x,y)
            for (xn, yn) in neighbors:
                exp_weight_map[x][y] += base_weights[xn][yn]

    return exp_weight_map


def multi_aggregate(exp_weight_map, num_aggregates):
    exp_weight_map = deepcopy(exp_weight_map)

    for i in range(num_aggregates):
        exp_weight_map = aggregate_weight(exp_weight_map)
    
    apply_mask(exp_weight_map)
    return exp_weight_map


def exp_render(exp_weight_map):
    # render the world
    for x in range(len(exp_weight_map)):
        for y in range(len(exp_weight_map[x])):
            print(int(exp_weight_map[x][y]/1000), end='')
            print(' ', end='')
        print('')

def apply_mask(exp_weight_map):
    for x in range(len(exp_weight_map)):
        for y in range(len(exp_weight_map[x])):
            exp_weight_map[x][y] = exp_weight_map[x][y] * EXP_MASK[x][y]


# run aggregate_weight multiple times to get choices of exploration.

def find_target_on_heatmap(exp_heatmap, islands, island_no):
    max_value, max_index = max((x, (i, j))
                           for i, row in enumerate(exp_heatmap)
                           for j, x in enumerate(row) if islands[i][j] == island_no)

    return max_index
