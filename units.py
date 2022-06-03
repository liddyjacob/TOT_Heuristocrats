from pickle import GLOBAL
from socket import timeout
from threading import current_thread
from ai.heuristocrats.moves import Move, Build, Repair, Attack
from ai.heuristocrats.utils import gold_per_turn_needed, handler, get_resource_from_id, get_next_building
from ai.heuristocrats.buildings import Townhall, Barracks, Range, Stable, House
from ai.heuristocrats.resources import Gold, Resource, Tree
from ai.heuristocrats.behaviors import *
import math
import signal
import threading
import time
#

class Unit:
    our_kingdom = 0

    def __init__(self, obj):
        global NUMBER_SYSTEM
        self.team = obj["team"]
        self.x = obj['x']
        self.y = obj['y']
        self.move_stack = []
        self.id = obj['id']
        self.team = obj['team']
        self.island_ids = set()
        self.turn = {}
        self.travel_ban = True

    def execute(self, cws):
        self.number = NUMBER_SYSTEM[type(self)]
        NUMBER_SYSTEM[type(self)] = NUMBER_SYSTEM[type(self)] + 1

        self.follow_behaviors(cws)

        if self.turn == {}:
            self.follow_basic_behaviors(cws)
            
        #self.follow_behaviors(cws)
        return(self.turn)

    def execute_basic(self,cws):
        self.follow_basic_behaviors(cws)
        return(self.turn)

    #  default behavior: just check if it is within one coord
    def within_range(self, pair):
        return max(abs(pair[0] - self.x), abs(pair[1] - self.y)) == 1

    # todo update health and stuff
    def update(self, obj):
        self.x = obj['x']
        self.y = obj['y']

    def __hash__(self):
        return hash(self.id)

class Villager(Unit):
    def __init__(self, obj):
        super().__init__(obj)

    @staticmethod
    def power(level):
        return 1
    
    def follow_behaviors(self, cws):
        if len(cws.gatherCity()) == 0:
            # no purpose in building so early without gold:
            if cws.gold <= 10:
                turn = AttackNearbyResource(self, cws, Gold)
                if turn:
                    self.turn = turn.apply(self)
                    return

                turn = GetNearbyResource(self, cws, Gold)
                if turn:
                    self.turn = turn.apply(self)
                    return

            turn = BuildThing(self, cws, Townhall)
            if turn:
                self.turn = turn.apply(self)
                return

        # see if there are any buildings nearby to repair:
        turn = RepairNearby(self,cws)
        if turn:
            self.turn = turn.apply(self)
            return
        
        # build houses if a house is needed
        if cws.get_housing() < len(cws.gatherEmpire()) + 1.25 * len(cws.gatherCity()) - cws.num_buildings(House) :
            turn = BuildThing(self, cws, House)
            if turn:
                self.turn = turn.apply(self)
                return

        # lol build town halls everywhere
        buildingtype = get_next_building(cws)

        if buildingtype is not None:
            if cws.can_afford(buildingtype.buildcost()):
                turn = BuildThing(self, cws, buildingtype)
                if turn:
                    self.turn = turn.apply(self)
                    return

        #if high enough population, ignore villager shuffling when possible:
        if cws.getPopulation(Villager) > 8:
            turn = AttackNearbyResource(self, cws, Resource)
            if turn:
                self.turn = turn.apply(self)
                return

        # also once we have 12 villagers, we should assign jobs by modulating id
        if cws.getPopulation(Villager) >= 13:
            rtype = get_resource_from_id(self.id)
            turn = GetNearbyResource(self, cws, rtype)
            if turn:
                self.turn = turn.apply(self)
                return
        
        else:
            gold_req = gold_per_turn_needed(cws)

            if self.number <= math.ceil(gold_req):
                # first, see if there is any gold nearvy
                turn = AttackNearbyResource(self, cws, Gold)
                if turn:
                    self.turn = turn.apply(self)
                    return

                turn = GetNearbyResource(self, cws, Gold)
                if turn:
                    self.turn = turn.apply(self)
                    return

            # get trees from now on
            turn = AttackNearbyResource(self, cws, Tree)
            if turn:
                self.turn = turn.apply(self)
                return

            turn = GetNearbyResource(self, cws, Tree)
            if turn:
                self.turn = turn.apply(self)
                return


    # Time ran out, see if we can get a basic behavior in:
    def follow_basic_behaviors(self, cws):
        # Get Anything
        turn = AttackNearbyResource(self, cws, Resource)
        if turn:
            self.turn = turn.apply(self)
            return

        # if that fails, attack an enemy


        # if that fails, move a random direction
        turn = Move([random.randint(-1,1), random.randint(-1,1)])
        self.turn = turn.apply(self)
        

    @staticmethod
    def type():
        return 'Villager'


class Archer(Unit):
    def __init__(self, obj):
        super().__init__(obj)

    def follow_behaviors(self, cws):
        turn = DataMine(self, cws)
        if turn:
            self.turn = turn.apply(self)
            return

        return None

    def follow_basic_behaviors(self, cws):
        return None

    @staticmethod
    def type():
        return 'Archer'

    @staticmethod
    def power(i):
        if i == 1:
            return 1
        if i == 2:
            return 2
        if i == 3:
            return 3

    @staticmethod
    def cost():
        return((10,10))

    #  default behavior: just check if it is within one coord
    def within_range(self, pair):
        return abs(pair[0] - self.x) + abs(pair[1] - self.y) <= 8

class Infantry(Unit):
    def __init__(self, obj):
        super().__init__(obj)

    def follow_behaviors(self, cws):
        if cws.percent_uncovered_f() < .7:
            turn = ExploreFoliage(self, cws)
            if turn:
                self.turn = turn.apply(self)
                return

        turn = ExploreGeneral(self, cws)
        if turn:
            self.turn = turn.apply(self)
            return        

        turn = GetNearbyResource(self, cws, Tree)
        if turn:
            self.turn = turn.apply(self)
            return

        self.turn = Move([0,0]).apply(self)
        return
        # r
        # only 1 explorer

    # Time ran out, see if we can get a basic behavior in:
    def follow_basic_behaviors(self, cws):
        # Attack any nearby villager

        # then check enemies

        # if that fails, move a random direction
        turn = Move([random.randint(-1,1), random.randint(-1,1)])
        self.turn = turn.apply(self)
        

    @staticmethod
    def power(i):
        if i == 1:
            return 2
        if i == 2:
            return 3
        if i == 3:
            return 4

    @staticmethod
    def type():
        return 'Infantry'

    @staticmethod
    def cost():
        return((0,20))


class Calvary(Unit):
    def __init__(self, obj):
        super().__init__(obj)

    def follow_behaviors(self, cws):
        return None

    def follow_basic_behaviors(self, cws):
        return None
    
    @staticmethod
    def type():
        return 'Calvary'

    @staticmethod
    def power(i):
        if i == 1:
            return 3
        if i == 2:
            return 4
        if i == 3:
            return 5

    @staticmethod
    def cost():
        return((0,40))


class Skeleton(Archer):
    def __init__(self, obj):
        super().__init__(obj)

    @staticmethod
    def type():
        return 'Skeleton'


NUMBER_SYSTEM = {}
NUMBER_SYSTEM[Infantry] = 1
NUMBER_SYSTEM[Villager] = 1
NUMBER_SYSTEM[Calvary] = 1
NUMBER_SYSTEM[Archer] = 1

def reset_number_system():
    global NUMBER_SYSTEM
    global WOOD_TAKEN_CARE_OF
    global GOLD_TAKEN_CARE_OF
    NUMBER_SYSTEM = {}
    NUMBER_SYSTEM[Infantry] = 1
    NUMBER_SYSTEM[Villager] = 1
    NUMBER_SYSTEM[Calvary] = 1
    NUMBER_SYSTEM[Archer] = 1

    GOLD_TAKEN_CARE_OF = 0
    WOOD_TAKEN_CARE_OF = 0