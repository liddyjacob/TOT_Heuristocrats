from copy import deepcopy
from ai.heuristocrats.constants import * 
from ai.shitutils import coord_to_int

# Given size of Matrix
 
# This code is contributed by rag2127


def printAsIs(matrix):
    for x in range(len(matrix)):
        for y in range(len(matrix[x])):
            print(matrix[x][y], end='')
            print(' ', end='')
        print('')


from stats import *
# render bs
TREE = '\033[32m'
GOLD = '\033[33m'
NORM = '\033[37m'
# teamcolors
teamcols = {
    -2: NORM,
    0: "\033[31m", # RED
    1: "\033[34m", # BLUE
    2: "\033[35m", # PURPLE
    3: "\033[36m", # CYAN
}




# Tries moving in a direction six units at a time
#def fast_path(cws, start, end, csize = 6):
#    if start == end:
#        return None

#    while MAX_ITER < 

    

from random import shuffle
def get_path(cws, start, end):
    queue = [[start]]
    if start == end:
        return None

    visited = set()
    while len(queue) > 0:
        path = queue.pop()
        if end == path[-1]:
            return path

        if path[-1] not in visited:
            # Not traversable, and not the base unit. Do not 
            if (path[-1] != start and cws.is_traversable(path[-1])):
                continue
            
            # this is a valid path and we have visited it.
            visited.add(path[-1])
            
            # try diagonal moves first:
            d_movements = shuffle([(-1,-1), (-1,1), (1,-1), (1,1)])
            
            # straight
            s_movements = shuffle([(-1,0), (0,1), (1,0), (0,-1)])
            all_movements = d_movements + s_movements

            for m in all_movements:
                if cws.is_traversable(m):

                    new_path = list(path)
                    new_path.append()


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
                exp_weight_map[(x, y)] = exp_weight_map[(x, y)] + base_weights[(xn, yn)]

    return exp_weight_map


def multi_aggregate(exp_weight_map, num_aggregates):
    exp_weight_map = deepcopy(exp_weight_map)

    for i in range(num_aggregates):
        exp_weight_map = aggregate_weight(exp_weight_map)
    
    return exp_weight_map
