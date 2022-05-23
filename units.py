from threading import current_thread
from ai.heuristocrats.behaviors import *
from ai.heuristocrats.commander import KING

# need a way to assign ids to units
class TeamUnitRegistry:
    def __init__(self):
        self.unit_registry = {}
        self.unit_registry['Villager'] = {}
        self.unit_registry['Archer'] = {}
        self.unit_registry['Infantry'] = {}
        self.unit_registry['Calvary'] = {}

        self.id_stack = {}
        self.id_stack['Villager'] = [1]
        self.id_stack['Archer'] = [1]
        self.id_stack['Infantry'] = [1]
        self.id_stack['Calvary'] = [1]


    def register(self, unit):
        next_id = self.id_stack[unit.type()]
        if len(self.id_stack[unit.type()]) == 0:
            # must have no units to replace, so 
            self.id_stack[unit.type()].push_back(next_id + 1)
        
        self.unit_registry[unit.type()][unit] = next_id

        return next_id

    # deregister a unit if they are dear
    def deregister(self, unit):
        deregister_id = self.unit_registry[unit.type()][unit]

        del self.unit_registry[unit.type()][unit]

        self.id_stack[unit.type()].append(deregister_id)

TUR = TeamUnitRegistry()

class Unit:
    our_kingdom = 0

    def __init__(self, obj):
        self.team = obj["team"]
        self.x = obj['x']
        self.y = obj['y']
        self.move_stack = []
        self.id = obj['id']
        self.team = obj['team']

        if self.team == self.our_kingdom:
            self.unit_number = TUR.register(self)
            self.behavior_stack = []
            self.behavior_stack.append(KING.order(self))

    def execute(self, cws):
        # get an assignment from the king if there is no responibility
        behavior = self.behavior_stack[-1]

        if behavior.is_finished(self):
            self.behavior_stack.pop()

            if len(self.behavior_stack) == 0:
                self.behavior_stack.append(KING.order(self))
                
            behavior = self.behavior_stack[-1]

        # todo add behavior interruptions
        turn = behavior.execute(self, cws)
        return(turn)

    # todo update health and stuff
    def update(self, obj):
        self.x = obj['x']
        self.y = obj['y']

    def kill(self):
        global TUR
        if self.team ==  self.our_kingdom:
            TUR.deregister(self)

    def __hash__(self):
        return hash(self.id)

class Villager(Unit):
    def __init__(self, obj):
        super().__init__(obj)
    
    @staticmethod
    def type():
        return 'Villager'


class Archer(Unit):
    def __init__(self, obj):
        super().__init__(obj)

    @staticmethod
    def type():
        return 'Archer'

class Infantry(Unit):
    def __init__(self, obj):
        super().__init__(obj)

    @staticmethod
    def type():
        return 'Infantry'

class Calvary(Unit):
    def __init__(self, obj):
        super().__init__(obj)

    @staticmethod
    def type():
        return 'Calvary'

class Skeleton(Archer):
    def __init__(self, obj):
        super().__init__(obj)

    @staticmethod
    def type():
        return 'Skeleton'