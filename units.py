from pickle import GLOBAL
from socket import timeout
from threading import current_thread
from ai.heuristocrats.moves import Move, Build, Repair, Attack
from ai.heuristocrats.utils import gold_per_turn_needed, handler
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


    # todo update health and stuff
    def update(self, obj):
        self.x = obj['x']
        self.y = obj['y']

    def __hash__(self):
        return hash(self.id)

class Villager(Unit):
    def __init__(self, obj):
        super().__init__(obj)
    
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


            turn = BuildInitialTC(self, cws)
            if turn:
                self.turn = turn.apply(self)
                return

        # see if there are any buildings nearby to repair:
        turn = RepairNearby(self,cws)
        if turn:
            self.turn = turn.apply(self)
            return
        
        # lol build town halls everywhere
        if cws.can_afford(Townhall.buildcost()):
            turn = BuildInitialTC(self, cws)
            if turn:
                self.turn = turn.apply(self)
                return

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
        global NUMBER_SYSTEM
        # debug funny business
        NUMBER_SYSTEM[type(self)] = 1

    @staticmethod
    def type():
        return 'Archer'

class Infantry(Unit):
    def __init__(self, obj):
        super().__init__(obj)

    def follow_behaviors(self, cws):
        if cws.percent_uncovered_f() < .55:
            turn = ExploreFoliage(self, cws)
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
    def type():
        return 'Infantry'

class Calvary(Unit):
    def __init__(self, obj):
        super().__init__(obj)

    def follow_behaviors(self, cws):
        global NUMBER_SYSTEM
        # debug funny business
        NUMBER_SYSTEM[type(self)] = 1

    @staticmethod
    def type():
        return 'Calvary'

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