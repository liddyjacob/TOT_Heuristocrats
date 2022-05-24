from pickle import GLOBAL
from threading import current_thread
from ai.heuristocrats.moves import Move, Build, Repair, Attack
from ai.heuristocrats.utils import get_path_a_star
from ai.heuristocrats.buildings import Townhall, Barracks, Range, Stable, House
from ai.heuristocrats.resources import Gold, Tree

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
        if self.team == self.our_kingdom:
            self.number = NUMBER_SYSTEM[type(self)]
            NUMBER_SYSTEM[type(self)] = NUMBER_SYSTEM[type(self)] + 1

    def execute(self, cws):

        self.turn = Move([1,0])
        return(self.turn.apply(self))

    # todo update health and stuff
    def update(self, obj):
        self.x = obj['x']
        self.y = obj['y']

    def __hash__(self):
        return hash(self.id)

GOLD_TAKEN_CARE_OF = 0
WOOD_TAKEN_CARE_OF = 0
class Villager(Unit):
    def __init__(self, obj):
        super().__init__(obj)
    
    def execute(self, cws):
        global GOLD_TAKEN_CARE_OF, WOOD_TAKEN_CARE_OF
        self.island_ids = set()

        # debug funny business
        for i in range(-1,2):
            for j in range(-1,2):
                id_name = cws.get_island_id((self.x + i, self.y + j))
                if id_name > 0:
                    self.island_ids.add(id_name)

        print(self.island_ids)
        
        if len(cws.gatherCity()) == 0:
            turn = self.executeBuildTC(cws)
            if turn:
                print(turn.apply(self))
                return turn.apply(self)

        # see if there are any buildings nearby to repair:
        turn = self.executeRepairNearby(cws)
        if turn:
            print(turn.apply(self))
            return turn.apply(self)

        if cws.can_afford(Townhall.buildcost()):
            turn = self.executeBuildTC(cws)
            if turn:
                print(turn.apply(self))
                return turn.apply(self)


        # solo behavior: get gold!
        if GOLD_TAKEN_CARE_OF == 0:
            turn = self.executeGetNearby(cws, Gold)
            if turn:
                print(turn.apply(self))
                GOLD_TAKEN_CARE_OF = 1
                return turn.apply(self)

        # Get Wood!   
        elif WOOD_TAKEN_CARE_OF == 0:
            turn = self.executeGetNearby(cws, Tree)
            if turn:
                print(turn.apply(self))
                WOOD_TAKEN_CARE_OF = 1
                return turn.apply(self)     


        # Odd ones shoud get gold?
        # Even ones should get wood?
        if (self.id % 3) == 0:
            turn = self.executeGetNearby(cws, Gold)
            if turn:
                print(turn.apply(self))
                return turn.apply(self)
        else:
            turn = self.executeGetNearby(cws, Tree)
            if turn:
                print(turn.apply(self))
                return turn.apply(self)

        turn = self.executeFolExplore(cws)
        if turn:
            print(turn.apply(self))
            return turn.apply(self)

        self.turn = Move([0,0])
        return(self.turn.apply(self))


        # r
        # only 1 explorer

    def executeBuildTC(self, cws):
        import random
        if (random.random() < .75):
            return Build(Townhall, [self.x + random.randint(-1,1), self.y + random.randint(-1,1)])
        else:
            return Move([random.randint(-1,1), random.randint(-1,1)])

    def executeRepairNearby(self, cws):
        for i in range(-1,2):
            for j in range(-1,2):
                obj = cws.get_coord((self.x + i, self.y + j))
                if obj in cws.gatherCity():
                    if obj.hp != obj.max_health():
                        return Repair(obj)

        return None

    # see if there is gold nearby, then get it
    def executeGetNearby(self,cws, giventype):
        import time
        # get lowest resource in kingdom:
        target = cws.get_corner_resource(giventype, next(iter(self.island_ids)))
        print(target)

        if target is None:
            print('target was nonte')
            return None

        # gold is attainable, find it  
        start = (self.x, self.y)

        path = get_path_a_star(cws, start, target)
        if len(path) == 2:
            return Attack(cws.get_coord(target))

        step = path[-2]
        return Move([step[0] - self.x, step[1] - self.y])




    def executeFolExplore(self, cws):
        # Discover foliage if there is foliage to discover
        start = (self.x, self.y)

        for wp in cws.fexplore_waypoints:
            for dx in [-1,0,1]:
                for dy in [-1,0,1]:
                    if cws.get_island_id(wp) == cws.get_island_id((self.x + dx, self.y + dy)):
                        path = get_path_a_star(cws, start, wp)
                        next = path[-2]
                        return Move([next[0] - start[0], next[1] - start[1]])

        return None


    @staticmethod
    def type():
        return 'Villager'


class Archer(Unit):
    def __init__(self, obj):
        super().__init__(obj)

    def execute(self, cws):
        global NUMBER_SYSTEM
        # debug funny business
        NUMBER_SYSTEM[type(self)] = 1

    @staticmethod
    def type():
        return 'Archer'

class Infantry(Unit):
    def __init__(self, obj):
        super().__init__(obj)

    def execute(self, cws):

        if self.number == 1:
            turn = self.executeFolExplore(cws)
            if turn:
                return turn.apply(self)


        self.turn = Move([0,0])
        return(self.turn.apply(self))

        # r
        # only 1 explorer

    
    def executeFolExplore(self, cws):
        # Discover foliage if there is foliage to discover
        if cws.percent_uncovered_f() < .8:
            start = (self.x, self.y)


            for wp in cws.fexplore_waypoints:
                for dx in [-1,0,1]:
                    for dy in [-1,0,1]:
                        if cws.get_island_id(wp) == cws.get_island_id((self.x + dx, self.y + dy)):
                            path = get_path_a_star(cws, start, wp)
                            next = path[-2]
                            return Move([next[0] - start[0], next[1] - start[1]])

        return None

    @staticmethod
    def type():
        return 'Infantry'

class Calvary(Unit):
    def __init__(self, obj):
        super().__init__(obj)

    def execute(self, cws):
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