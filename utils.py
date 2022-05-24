from copy import deepcopy
from operator import ne
from ai.heuristocrats.constants import *
from ai.shitutils import coord_to_int
from ai.heuristocrats.resources import Unknown
# Given size of Matrix
import heapq as heap
import math

def sign(x):
    if x == 0: 
        return 0
    return int((abs(x) / x))

def reconstruct_path(cameFrom, current):
    total_path = [current]
    while current in cameFrom.keys():
        current = cameFrom[current]
        total_path.append(current)
    return total_path


def get_path_a_star(cws, start, end):
    openSet = set()
    openSet.add(start)

    cameFrom = {}
    gScore = {}
    gScore[start] = 0

    fScore = {}
    fScore[start] = (1)

    while len(openSet) != 0:
        curr = min(openSet, key=fScore.get)
        if curr == end:
            return reconstruct_path(cameFrom, curr)

        openSet.remove(curr)

        xsign = sign(end[0] - curr[0])
        ysign = sign(end[1] - curr[1])

        moves = [(curr[0] + xsign, curr[1] + ysign)]

        shuffled_diff = [-1,0,1]
        shuffle(shuffled_diff)

        for yk in shuffled_diff:
            if yk != ysign:
                moves.append((curr[0] + xsign, curr[1] + yk))

        for xk in shuffled_diff:
            if xk != xsign:
                moves.append((curr[0] + xk,curr[1] +  ysign))   

        for xk in shuffled_diff: 
            for yk in shuffled_diff:
                if xk != xsign and yk != ysign:
                    if xk != 0 or  yk != 0:
                        moves.append((curr[0] + xk, curr[1] + yk))


        for neighbor in moves:
            if not cws.is_traversable(neighbor):
                tentative_gScore = gScore[curr] + 100000
            else:
                tentative_gScore = gScore[curr] + 1 
            
            if gScore.get(neighbor) is None:
                gScore[neighbor] = math.inf
            if tentative_gScore < gScore[neighbor]:
                cameFrom[neighbor] = curr
                gScore[neighbor] = tentative_gScore
                heur_score = min(abs(neighbor[0] - end[0]), abs(neighbor[1] - end[1]))
                fScore[neighbor] = tentative_gScore + heur_score
                if neighbor not in openSet:
                    openSet.add(neighbor)





from random import shuffle
def get_path(cws, start, end):

    queue = [[start]]
    if start == end:
        return None

    visited = set()
    while len(queue) > 0:
        #print(queue)
        path = queue.pop()
        if end == path[-1]:
            return path

        if path[-1] not in visited:
            curr = path[-1]
            # Not traversable, and not the base unit. Do not 
            if (not cws.is_traversable(curr)):
                continue

            if curr in visited:
                continue
            
            # this is a valid path and we have visited it.
            visited.add(curr)

            xsign = sign(end[0] - curr[0])
            ysign = sign(end[1] - curr[1])

            moves = [(xsign, ysign)]


            shuffled_diff = [-1,0,1]
            shuffle(shuffled_diff)

            for yk in shuffled_diff:
                if yk != ysign:
                    moves.append((xsign, yk))

            for xk in shuffled_diff:
                if xk != xsign:
                    moves.append((xk, ysign))   

            for xk in shuffled_diff: 
                for yk in shuffled_diff:
                    if xk != xsign and yk != ysign:
                        if xk != 0 or  yk != 0:
                            moves.append((xk, yk))

            for m in moves:
                if cws.is_traversable((curr[0]+m[0],curr[1]+m[1])):
                    new_path = list(path)
                    new_path.append((curr[0]+m[0],curr[1]+m[1]))
                    queue.append(new_path)

    return None



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
