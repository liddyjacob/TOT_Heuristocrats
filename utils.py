from copy import deepcopy
from operator import ne
from turtle import up
from ai.heuristocrats.buildings import Barracks, Range, Townhall, Stable
from ai.heuristocrats.constants import *
from ai.heuristocrats.resources import Unknown
# Given size of Matrix
import heapq as heap
import math
import random
from random import shuffle
import time

def reconstruct_path(cameFrom, current):
    total_path = [current]
    while current in cameFrom.keys():
        current = cameFrom[current]
        total_path.append(current)
    return total_path

ASTART_LIMIT = .025
def get_path_a_star(cws, start, end):
    # Only allow a select period of time for a* algorithm.
    openSet = set()
    openSet.add(start)

    cameFrom = {}
    gScore = {}
    gScore[start] = 0

    fScore = {}
    fScore[start] = (1)

    start = time.time()

    while len(openSet) != 0:
        curr = min(openSet, key=fScore.get)
        if curr == end:
            return reconstruct_path(cameFrom, curr)
        
        if time.time() - start > ASTART_LIMIT:
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
                heur_score = max(abs(neighbor[0] - end[0]), abs(neighbor[1] - end[1])) + random.random()/4
                fScore[neighbor] = tentative_gScore + heur_score
                if neighbor not in openSet:
                    openSet.add(neighbor)




# only allow .025 seconds before returning
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


# Get the gold per turn required to build units from 
# every building as fast as possible.
# Once we have villagers achiving the gold per turn amount,
# we can build villagers as fast as possible
def gold_per_turn_needed(cws):
    # Build up extra gold:
    gold_per_turn_needed = 1
    for building in cws.gatherCity():
        gold_per_turn_needed += building.producecost()[1] / building.turnsToProduce()

    return gold_per_turn_needed

def wood_per_turn_needed(cws):
    wood_per_turn_needed = 0
    for building in cws.gatherCity():
        wood_per_turn_needed += building.producecost()[0] / building.turnsToProduce()

    return wood_per_turn_needed

def handler(signum, frame):
   print('Did not finish in time: signum, frame')
   raise Exception("end of time")


# resource plinko: determine how much gold is needed, and how much wood is needed.
#
WOOD_LEVEL = 0 
def resource_plinko_board(cws):
    global WOOD_LEVEL
    from ai.heuristocrats.units import Villager
    needed_gold = gold_per_turn_needed(cws)
    needed_wood = wood_per_turn_needed(cws)
    other = cws.getPopulation(Villager) - (needed_gold + needed_wood)

    if other > 0:
        needed_wood = needed_gold + other
    
    # Now we need to split into how many parts of 13 are needed for each resource.

    WOOD_LEVEL = math.floor(13 * (needed_wood / (needed_wood + needed_gold)))

def get_resource_from_id(id):
    from ai.heuristocrats.resources import Tree, Gold

    hash = (17 * id) % 13

    if hash < WOOD_LEVEL:
        print("getting tree")
        return Tree
    else:
        print("getting gold")
        return Gold
    
# determine if it is more economical to upgrade a set of units or build a new one:
def upgrade_over_build(cws, typeof):
    if typeof is None:
        return False
    
    if cws.level[typeof] == 3:
        return False

    # if we are rich, upgrade.
    if cws.wood > 400 and cws.gold > 500:
        cws.wood -= (typeof.cost()[0] * 10) 
        cws.gold -= (typeof.cost()[1] * 10) 
        return True

    pop = cws.getPopulation(typeof)

    power_per_gold = typeof.power(cws.level[typeof]) / typeof.cost()[1]
    upgrade_per_gold = pop / (typeof.cost()[1] * 10) 

    # upgrade if power per gold is comparable(health benefits make up the rest)
    return power_per_gold < (upgrade_per_gold * 2)

def wander_goal(cws):
    mod_time = int(time.time()/10) % 12
    # return the corners of the empire, cycling on the mod_time value m
    if mod_time <= 5:
        return cws.wander_locations[0]
    if mod_time <= 7:
        return cws.wander_locations[1]
    
    return cws.wander_locations[1]


def get_next_building(cws):
    from ai.heuristocrats.units import Archer
    # Always need 1 townhall
    if cws.num_buildings(Townhall) < 1:
        return Townhall

    # Then build a barracks, for guards:
    if cws.num_buildings(Barracks) < 1:
        return Barracks

    # Then another townhall
    if cws.num_buildings(Townhall) < 2:
        return Townhall

    # Then 2 archery ranges:
    if cws.num_buildings(Range) < 2:
        return Range

    # check if we need to reserve money for archery ranges:
    if upgrade_over_build(cws, Archer):
        return None

    if cws.num_buildings(Stable) < 2:
        return Stable

    # Then another townhall
    if (cws.num_buildings(Stable) + cws.num_buildings(Archer)) % 2:
        return Range
    else:
        return Stable

def get_nearest_enemy(unit, cws, subclass = None):
    from ai.heuristocrats.units import Unit
    if subclass is None:
        subclass = Unit

    relevant_enemies = [eu for eu in cws.gatherEnemyEmpire() if issubclass(type(eu), subclass)]
    if len(relevant_enemies) == 0:
        return None
    
    nearest_enemy = min(relevant_enemies, key=lambda eu: max(
        abs(eu.x - unit.x), 
        abs(eu.y - unit.y)))
    return nearest_enemy