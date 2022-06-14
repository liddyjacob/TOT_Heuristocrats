from pickle import FALSE
import random
from ai.heuristocrats.buildings import Building, Townhall, Barracks, Range, Stable, House
from ai.heuristocrats.moves import Move, Build, Repair, Attack, DoNothing
from ai.heuristocrats.utils import get_path_a_star, wander_goal, get_nearest_enemy, get_nearest_enemy_building, get_step
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

    if cws.villager_can_build[typeof.size()]:
        # If this villager was destin to build, then this would not be none
        if random.random() < .75:
            if unit.build_loc.get(typeof.size()) is not None:
                return Build(typeof, unit.build_loc[typeof.size()])
        else:
            return Wander(unit, cws)

    else:

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
            # no corners!
            if min(abs(i),abs(j)) == 1:
                next
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
def Bodyguard(unit, otherUnit, cws):
    # island intersection - see if the villager is even accessable.
    island_intersect = unit.island_ids.intersection(otherUnit.island_ids)
    if len(island_intersect) == 0:
        return None

    # First, check if we are within 12 units of the villager. If so, we can attack.
    # we can do this by checking to see if the closest enemy to this one is within
    # range.
    distance_to_other = max(abs(unit.x - otherUnit.x), abs(unit.y - otherUnit.y))


    if distance_to_other <= 12:
        if len(cws.gatherEnemyEmpire()) != 0:
            nearest_enemy = get_nearest_enemy(unit, cws)

            if nearest_enemy is not None:
                if unit.within_range((nearest_enemy.x, nearest_enemy.y)):
                    return Attack(nearest_enemy)

                # if they are not within range, but are still within 12 units, attack them.
                if max(abs(otherUnit.x - nearest_enemy.x), abs(otherUnit.y - nearest_enemy.y)):
                    if len(unit.island_ids.intersection(nearest_enemy.island_ids)) != 0:
                        path = get_path_a_star(cws, (unit.x, unit.y), (nearest_enemy.x, nearest_enemy.y))
                        next = path[-2]
                        return Move([next[0] - unit.x, next[1] - unit.y])

    # if we are within 3 units, do nothing.
    if distance_to_other <= 3:
        return DoNothing()

    # If we are not within 12 units, then we should move back to the villager
    path = get_path_a_star(cws, (unit.x, unit.y), (otherUnit.x, otherUnit.y))
    next = path[-2]
    return Move([next[0] - unit.x, next[1] - unit.y])

def BodyguardBasic(unit, otherUnit, cws):
   # island intersection - see if the villager is even accessable.
    island_intersect = unit.island_ids.intersection(otherUnit.island_ids)
    if len(island_intersect) == 0:
        return None

    # First, check if we are within 12 units of the villager. If so, we can attack.
    # we can do this by checking to see if the closest enemy to this one is within
    # range.
    distance_to_other = max(abs(unit.x - otherUnit.x), abs(unit.y - otherUnit.y))


    if distance_to_other <= 12:
        if len(cws.gatherEnemyEmpire()) != 0:
            nearest_enemy = get_nearest_enemy(unit, cws)

            if nearest_enemy is not None:
                if unit.within_range((nearest_enemy.x, nearest_enemy.y)):
                    return Attack(nearest_enemy)

                # if they are not within range, but are still within 12 units, attack them.
                if max(abs(otherUnit.x - nearest_enemy.x), abs(otherUnit.y - nearest_enemy.y)):
                    if len(unit.island_ids.intersection(nearest_enemy.island_ids)) != 0:
                        step = get_step((unit.x, unit.y), (nearest_enemy.x, nearest_enemy.y))
                        return Move([step[0], step[1]])

    # if we are within 3 units, do nothing.
    if distance_to_other <= 3:
        return DoNothing()

    # If we are not within 12 units, then we should move back to the villager
    step = get_step((unit.x, unit.y), (otherUnit.x, otherUnit.y))
    return Move([step[0], step[1]])


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

# archers require non-archers to approach before attacking.
#def ApproachArcher()


def AttackInPlace(unit, cws):
    nearest_enemy = get_nearest_enemy(unit, cws)
    if nearest_enemy is not None:
        if unit.within_range((nearest_enemy.x, nearest_enemy.y)):
            return Attack(nearest_enemy)

    nearest_bld = get_nearest_enemy_building(unit, cws)
    if nearest_bld is not None:
        if unit.within_range((nearest_bld.x, nearest_bld.y)):
                return Attack(nearest_bld)
    
    return None


    

# Send the unit to the boarder, if they are at the boarder
def BoarderPatrol(unit, cws):
    # always try attacking if there is something to attack
    turn = AttackInPlace(unit, cws)
    if turn is not None:
        return turn

    pos = cws.get_guard_position(unit.id)

    if pos is None:
        return None


    nearest_bld = get_nearest_enemy_building(unit, cws)

    if nearest_bld is not None:
        if max(abs(pos[0]-nearest_bld.x), abs(pos[1] - nearest_bld.y)) <= 8:
            path = get_path_a_star(cws, (unit.x, unit.y), (nearest_bld.x, nearest_bld.y))
            next = path[-2]
            return Move([next[0] - unit.x, next[1] - unit.y])

    if max(abs(pos[0]-unit.x), abs(pos[1] - unit.y)) <= 1:
        turn = AttackInPlace(unit, cws)
        if turn is not None:
            return turn

        return DoNothing()

    if pos is not None:
        path = get_path_a_star(cws, (unit.x, unit.y), pos)
        next = path[-2]
        return Move([next[0] - unit.x, next[1] - unit.y])

    return None

def BoarderPatrolBasic(unit, cws):
    # always try attacking if there is something to attack
    turn = AttackInPlace(unit, cws)
    if turn is not None:
        return turn

    pos = cws.get_guard_position(unit.id)

    if pos is None:
        return None

    if max(abs(pos[0]-unit.x), abs(pos[1] - unit.y)) <= 1:
        turn = AttackInPlace(unit, cws)
        if turn is not None:
            return turn

        return DoNothing()

    if pos is not None:
        step = get_step((unit.x, unit.y), pos)
        return Move([step[0], step[1]])

    return None

def ExploreGeneral(unit, cws):
    from ai.heuristocrats.units import Villager

    # Discover foliage if there is foliage to discover
    start = (unit.x, unit.y)

    # We should kill any villagers of the enemy.
    nearest_enemy = get_nearest_enemy(unit, cws, Villager)
    if nearest_enemy is not None:
        if unit.within_range((nearest_enemy.x, nearest_enemy.y)):
            return Attack(nearest_enemy)

        if max(abs(nearest_enemy.x - unit.x), abs(nearest_enemy.y - unit.y)) < 6:
            if len(nearest_enemy.island_ids.intersection(unit.island_ids)) != 0:
                path = get_path_a_star(cws, (unit.x, unit.y), (nearest_enemy.x, nearest_enemy.y))
                next = path[-2]
                return Move([next[0] - unit.x, next[1] - unit.y])

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
                if len(path) >=2:
                    next = path[-2]
                    return Move([next[0] - unit.x, next[1] - unit.y])

    return None

def WanderBasic(unit, cws):
    wgoal = wander_goal(cws)

    if wgoal is None:
        return None

    for dx in [-1,0,1]:
        for dy in [-1,0,1]:
            if cws.get_island_id(wgoal) == cws.get_island_id((unit.x + dx, unit.y + dy)):
                step = get_step((unit.x, unit.y), wgoal)
                return Move([step[0], step[1]])

    return None