from threading import current_thread
from ai.heuristocrats.moves import Move, Build, Repair
from ai.heuristocrats.utils import get_path, get_path_a_star
from ai.heuristocrats.buildings import Townhall, Barracks, Range, Stable, House


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
        if self.team == self.our_kingdom:
            self.number = NUMBER_SYSTEM[type(self)]
            NUMBER_SYSTEM[type(self)] = NUMBER_SYSTEM[type(self)] + 1
            print(self.number)

    def execute(self, cws):

        self.turn = Move([1,0])
        return(self.turn.apply(self))

    # todo update health and stuff
    def update(self, obj):
        self.x = obj['x']
        self.y = obj['y']

    def __hash__(self):
        return hash(self.id)

class Villager(Unit):
    def __init__(self, obj):
        super().__init__(obj)
    
    def execute(self, cws):
        global NUMBER_SYSTEM
        # debug funny business
        NUMBER_SYSTEM[type(self)] = 1
        
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



        turn = self.executeFolExplore(cws)
        if turn:
            print(turn.apply(self))
            return turn.apply(self)

        self.turn = Move([0,0])
        return(self.turn.apply(self))

        # r
        # only 1 explorer

    def executeBuildTC(self, cws):
        return Build(Townhall, [self.x + 1, self.y - 1])

    def executeRepairNearby(self, cws):
        for i in range(-1,2):
            for j in range(-1,2):
                obj = cws.get_coord((self.x + i, self.y + j))
                if obj in cws.gatherCity():
                    if obj.hp != obj.max_health():
                        return Repair(obj)

        return None

    def executeFolExplore(self, cws):
        # Discover foliage if there is foliage to discover
        start = (self.x, self.y)

        for wp in cws.fexplore_waypoints:
            if cws.island_ids[wp] == cws.island_ids[start]:
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
        global NUMBER_SYSTEM
        NUMBER_SYSTEM[type(self)] = 1

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
            print('a')

            start = (self.x, self.y)

            for wp in cws.fexplore_waypoints:
                if cws.island_ids[wp] == cws.island_ids[start]:
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
