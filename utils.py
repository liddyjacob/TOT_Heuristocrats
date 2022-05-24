from copy import deepcopy
from operator import ne
from ai.heuristocrats.constants import *
from ai.shitutils import coord_to_int
from ai.heuristocrats.resources import Unknown
# Given size of Matrix
import heapq as heap
import math
import random
from random import shuffle

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

        moves = []

        shuffled_diff = [-1,0,1]
        shuffle(shuffled_diff)

        for xk in shuffled_diff: 
            for yk in shuffled_diff:
                if xk != 0 or  yk != 0:
                    moves.append((curr[0] + xk, curr[1] + yk))


        for neighbor in moves:
            if neighbor != end and not cws.is_traversable(neighbor):
                tentative_gScore = gScore[curr] + 100000
            else:
                tentative_gScore = gScore[curr] + 1 
            
            if gScore.get(neighbor) is None:
                gScore[neighbor] = math.inf
            if tentative_gScore < gScore[neighbor]:
                cameFrom[neighbor] = curr
                gScore[neighbor] = tentative_gScore
                heur_score = max(abs(neighbor[0] - end[0]), abs(neighbor[1] - end[1]))
                fScore[neighbor] = tentative_gScore + heur_score
                if neighbor not in openSet:
                    openSet.add(neighbor)



def get_path_a_star_any(cws, start, goal_type):
    openSet = set()
    openSet.add(start)

    cameFrom = {}
    gScore = {}
    gScore[start] = 0

    fScore = {}
    fScore[start] = (1)

    while len(openSet) != 0:
        curr = min(openSet, key=fScore.get)
        if type(cws.get_coord(curr)) == goal_type:
            return reconstruct_path(cameFrom, curr)

        openSet.remove(curr)

        moves = []

        shuffled_diff = [-1,0,1]
        shuffle(shuffled_diff)

        for xk in shuffled_diff: 
            for yk in shuffled_diff:
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
                heur_score = max(abs(neighbor[0] - 48), abs(neighbor[1] - 48))
                fScore[neighbor] = tentative_gScore + heur_score
                if neighbor not in openSet:
                    openSet.add(neighbor)


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
