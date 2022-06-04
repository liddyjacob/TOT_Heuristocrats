from pickle import FALSE
import random
from ai.heuristocrats.buildings import Building, Townhall, Barracks, Range, Stable, House
from ai.heuristocrats.moves import Move, Build, Repair, Attack
from ai.heuristocrats.utils import get_path_a_star, wander_goal
from ai.heuristocrats.resources import Gold, Resource, Tree

"""
def BuildInitialTC(unit, cws):
    if cws.someone_building[]:
        return None
    
    
    tclc = cws.get_tc_location()
    cws.tclc = tclc

    cws.someone_building = True

    # TODO CHECK IF UNIT CAN REACH TCLC WITH ISLANDS!
    if (unit.x - 1, unit.y - 1) in cws.tc_spots:
        return Build(Townhall, [unit.x - 3, unit.y - 3])
    if (unit.x + 3, unit.y - 1) in cws.tc_spots:
        return Build(Townhall, [unit.x + 1, unit.y - 3])
    if (unit.x - 1, unit.y + 3) in cws.tc_spots:
        return Build(Townhall, [unit.x - 3, unit.y + 1])
    if (unit.x + 3, unit.y + 3) in cws.tc_spots:
        return Build(Townhall, [unit.x + 1, unit.y + 1])

    cws.someone_building = False

    if (unit.x, unit.y) != tclc:
        return ExploreFoliage(unit, cws)
"""


def BuildThing(unit, cws, typeof):
    if cws.someone_building[typeof]:
        return None

    # make sure there is no buildings within 3 blocks:
    free_to_build = True
    for x in range(-3, 4):
        for y in range(-3, 4):
            if abs(x) == 3 or abs(y) == 3:
                obj_type = type(cws.get_coord((x, y)))
                if issubclass(obj_type, Building):
                    free_to_build = False
                    break

    if free_to_build:
        cws.someone_building[typeof] = True
        # TODO CHECK IF UNIT CAN REACH ANY TCLC WITH ISLANDS!
        if (unit.x - 1, unit.y - 1) in cws.tc_spots:
            return Build(typeof, [unit.x - typeof.size()[0], unit.y - typeof.size()[1]])
        if (unit.x + 3, unit.y - 1) in cws.tc_spots:
            return Build(typeof, [unit.x + 1, unit.y - typeof.size()[1]])
        if (unit.x - 1, unit.y + 3) in cws.tc_spots:
            return Build(typeof, [unit.x - typeof.size()[0], unit.y + 1])
        if (unit.x + 3, unit.y + 3) in cws.tc_spots:
            return Build(typeof, [unit.x + 1, unit.y + 1])

        cws.someone_building[typeof] = False

    # If no one can build, send 3 guys to explore PER BUILD TYPE
    if cws.num_vils_exploring[typeof] < 3:
        cws.num_vils_exploring[typeof] += 1
        return Wander(unit, cws)

    return None


# todo move these nearby algorithms into 
# cws
def RepairNearby(unit, cws):
    for i in range(-1,2):
        for j in range(-1,2):
            obj = cws.get_coord((unit.x + i, unit.y + j))
            if obj in cws.gatherCity():
                if obj.hp != obj.max_health():
                    return Repair(obj)

    return None

def AttackNearbyResource(unit, cws, typeof=Resource):
    for dx in range(-1,2):
        for dy in range(-1,2):
            obj = cws.get_coord((unit.x + dx, unit.y + dy))
            if issubclass(type(obj), typeof):
                if obj.reserved == False:
                    return Attack(obj)

    return None

def GetNearbyResource(unit, cws, typeof):
    # get lowest resource in kingdom:
    target = cws.get_corner_resource(typeof, unit.island_ids)

    if target is None:
        return None

    # gold is attainable, find it  
    start = (unit.x, unit.y)

    path = get_path_a_star(cws, start, target)

    if len(path) <= 1:
        return None

    if len(path) == 2:
        return Attack(cws.get_coord(target))

    step = path[-2]
    return Move([step[0] - unit.x, step[1] - unit.y])

# Become the bodyguard of a villager. 
def Bodyguard(unit, cws):
    # If we know the id of the current unit, we can find the nearest villager by ID.
    pass

# LOL Archers use trees to keep track of archer locations.
def DataMine(unit, cws):
    pair = cws.get_tree_and_target()
    if pair is None:
        return None

    (target_val, tree) = pair

    #if tree.
    if unit.within_range((tree.x, tree.y)):
        if tree.hp > target_val:
            tree.hp -= unit.power(cws.level[type(unit)])
            return Attack(tree)

    else:
        nearest_tp = cws.get_nearby_travel((tree.x, tree.y))
        if cws.get_island_id(nearest_tp) not in unit.island_ids:
            print("AAA")
            return None
        
        path = get_path_a_star(cws, (unit.x, unit.y), nearest_tp)
        next = path[-2]
        return Move([next[0] - unit.x, next[1] - unit.y])

    return None


# Send archers to clear alleys stored with the trees
def ClearAlleys(unit, cws):
    tree = cws.get_alleyway_trees()

    if tree is None:
        return None

    if unit.within_range((tree.x, tree.y)):
        return Attack(tree)
    
    nearest_tp = cws.get_nearby_travel((tree.x, tree.y))
    if cws.get_island_id(nearest_tp) not in unit.island_ids:
        print("AAA")
        return None
        
    path = get_path_a_star(cws, (unit.x, unit.y), nearest_tp)
    next = path[-2]
    return Move([next[0] - unit.x, next[1] - unit.y])

def FillAlleyWays(unit, cws):
    # T H I C C   A S S   B E H A V I O R.
    # if there are archers to move into the x alley, do it.
    if (cws.num_archers_in_x_alley / cws.x_alley_size) < .8:
        # See if we are already in this alley:
        if unit.in_x_alley:
            # move over if possible.
            direction_to_move = int(abs(cws.x_alley_entrance[0] - cws.x_alley_exit[0]) / (cws.x_alley_entrance[0] - cws.x_alley_exit[0]))

            if direction_to_move * (unit.x - direction_to_move) >= direction_to_move * cws.x_alley_exit[0]:
                if cws.is_traversable((unit.x - direction_to_move, unit.y)):
                    print("moving in x place")
                    return Move([-direction_to_move, 0])

            return GuardInPlace(unit,cws)
            # otherwise guard
        else:
            if cws.get_island_id(cws.x_alley_entrance) in unit.island_ids:
                # we don't want too many archers headed to each alley
                cws.num_archers_in_x_alley += 1
                path = get_path_a_star(cws, (unit.x, unit.y), cws.x_alley_entrance)
                next = path[-2]
                return Move([next[0] - unit.x, next[1] - unit.y])

    if (cws.num_archers_in_y_alley / cws.y_alley_size) < .8:
        if unit.in_y_alley:
            # move over if possible.
            direction_to_move = int(abs(cws.y_alley_entrance[1] - cws.x_alley_exit[1]) / (cws.y_alley_entrance[1] - cws.y_alley_exit[1]))
            
            if direction_to_move * (unit.y - direction_to_move) >= cws.y_alley_location[1] :
                if cws.is_traversable((unit.x, unit.y - direction_to_move)):
                    print("moving in y place")
                    return Move([0, -direction_to_move])
            
            return GuardInPlace(unit,cws)
        else:
            if cws.get_island_id(cws.y_alley_entrance) in unit.island_ids:
                # we don't want too many archers headed to each alley
                cws.num_archers_in_y_alley += 1
                path = get_path_a_star(cws, (unit.x, unit.y), cws.y_alley_entrance)
                next = path[-2]
                return Move([next[0] - unit.x, next[1] - unit.y])

def GuardInPlace(unit, cws):
    return None

def ExploreFoliage(unit, cws):
    # Discover foliage if there is foliage to discover
    start = (unit.x, unit.y)

    for wp in cws.fexplore_waypoints:
        for dx in [-1,0,1]:
            for dy in [-1,0,1]:
                if cws.get_island_id(wp) == cws.get_island_id((unit.x + dx, unit.y + dy)):
                    path = get_path_a_star(cws, start, wp)
                    next = path[-2]
                    return Move([next[0] - start[0], next[1] - start[1]])

    return None

def ExploreGeneral(unit, cws):
    # Discover foliage if there is foliage to discover
    start = (unit.x, unit.y)

    for wp in cws.pois:
        for dx in [-1,0,1]:
            for dy in [-1,0,1]:
                if cws.get_island_id(wp) == cws.get_island_id((unit.x + dx, unit.y + dy)):
                    path = get_path_a_star(cws, start, wp)
                    next = path[-2]
                    return Move([next[0] - start[0], next[1] - start[1]])

    return None

def Wander(unit, cws):
    wgoal = wander_goal(cws)

    if wgoal is None:
        return None

    for dx in [-1,0,1]:
        for dy in [-1,0,1]:
            if cws.get_island_id(wgoal) == cws.get_island_id((unit.x + dx, unit.y + dy)):
                path = get_path_a_star(cws, (unit.x, unit.y), wgoal)
                next = path[-2]
                return Move([next[0] - unit.x, next[1] - unit.y])