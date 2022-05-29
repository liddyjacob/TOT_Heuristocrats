from pickle import FALSE
import random
from ai.heuristocrats.buildings import Townhall, Barracks, Range, Stable, House
from ai.heuristocrats.moves import Move, Build, Repair, Attack
from ai.heuristocrats.utils import get_path_a_star
from ai.heuristocrats.resources import Gold, Resource, Tree

def BuildInitialTC(unit, cws):
    if cws.someone_building:
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
