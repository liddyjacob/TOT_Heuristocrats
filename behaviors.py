from pickle import FALSE
import random
from ai.heuristocrats.buildings import Building, Townhall, Barracks, Range, Stable, House
from ai.heuristocrats.moves import Move, Build, Repair, Attack
from ai.heuristocrats.utils import get_path_a_star
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
        return ExploreFoliage(unit, cws)

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


