from asyncio.streams import FlowControlMixin
from glob import glob
from pickle import UNICODE
from tkinter.messagebox import NO
from ai.shitutils import get_tiles, path_to_coord
from enum import Enum
from render import render
from ai.heuristocrats.units import Villager, Archer, Infantry, Calvary, Skeleton, Unit
from ai.heuristocrats.buildings import Townhall, Barracks, Range, Stable, House, Building
from ai.heuristocrats.resources import Resource, Tree, Gold, Other
from ai.heuristocrats.constants import *
from ai.heuristocrats.foliage_finder import initialize_foliage_state, reflect
from ai.heuristocrats.exploration import initialize_exp_weight_map, multi_aggregate, exp_render, find_target_on_heatmap
from ai.heuristocrats.utils import generate_exploration_map, getClosedIslands, printAsIs, cust_render
from ai.heuristocrats.annotated_world import ANNO_WORLD

# notes
"""
Upgrade units policy: examine cost / power for one unit, then cost / power to upgrade all units.

"""

# todo make this create an instance of each object
def initializeObject(obj):
    if obj is None:
        return 

    if obj == 'u':
        return Other.UNKNOWN

    if obj["type"] == 't':
        return Tree(obj)
    
    if obj["type"] == 'g':
        return Gold(obj)

    if obj["type"] == 'v':
        return Villager(obj)

    if obj["type"] == 'a':
        return Archer(obj)

    if obj["type"] == 'i':
        return Infantry(obj)

    if obj["type"] == 'c':
        return Calvary(obj)

    if obj["type"] == 'w':
        return Townhall(obj)

    if obj["type"] == 'b':
        return Barracks(obj)

    if obj["type"] == 'r':
        return Range(obj)

    if obj["type"] == 's':
        return Stable(obj)

    if obj["type"] == 'h':
        return House(obj)

    if obj["type"] == 'p':
        return Skeleton(obj)

    quit(f"ERROR REGISTERING OBJECT. UNKNOWN TYPE: {obj['type']}")

class objRegistry:
    def __init__(self):
        self.registry = {}
        self.not_lookup = set()

    def clearLookupHistory(self):
        self.not_lookup = set(self.registry.keys())

    def registerLookup(self, id):
        if id in self.not_lookup:
            self.not_lookup.remove(id)

    def lookup(self, id, register_lookup = False):
        # used to determine if an object has died.
        if register_lookup:
            self.registerLookup(id)
        return self.registry.get(id)

    # Deregester all the unnaccounted members
    def deregisterUnaccounted(self):
        for key in self.not_lookup:
            obj = self.registry[key]
            if issubclass(type(obj), Unit):
                obj.kill()

        [self.registry.pop(key) for key in self.not_lookup]

        if len(self.not_lookup) !=0:
            print("Deregistered Something!") 
        self.not_lookup = set()

    # Register an object and wrap it in my systems
    def register(self, object):
        self.registry[object["id"]] = initializeObject(object)
        return self.registry[object["id"]]

    def dumpObjects(self):
        return self.registry.values()

    def __str__(self):
        rval = ""
        for key, val in self.registry.items():
            rval += f"  {key}: {val}\n"

        return rval

REGISTRY = objRegistry()

def name():
    return "Commrads"

# iterate over the map once to avoid redundancy of things that 
# require iteraton.
def iterate_over_map(cws):
    global REGISTRY
    REGISTRY.clearLookupHistory()

    for x in range(cws.length):
        for y in range(cws.height):
            obj = cws.identify_and_associate(x,y)
            # update the 'annotated world'
            ANNO_WORLD.update(x,y,obj)

    REGISTRY.deregisterUnaccounted()
    ANNO_WORLD.modify_world_state(cws)
            # S

# Use this to force the world state to use my interfaces
class CombinedWorldState:
    def __init__(self, world_state, players, team_idx):
        self.world_state_raw = world_state
        self.players_raw = players
        self.team_id = team_idx
        self.height = len(self.world_state_raw)
        self.length = len(self.world_state_raw[0])
        
        # Associate coords with unique ids
        self.object_id_coord = {}

    def identify_and_associate(self,x,y):
        global REGISTRY

        # WARNING THIS REMOVES INFORMATION FROM THE MAP
        if self.world_state_raw[x][y] is None:
            self.object_id_coord[(x,y)] = Other.UNOCCUPIED
            return Other.UNOCCUPIED

        # I NEED TO DIFFERENTIATE BETWEEN UNVISITED AND UNOCCUPIED.
        if self.world_state_raw[x][y] == 'u':
            self.object_id_coord[(x,y)] = Other.UNKNOWN
            return Other.UNKNOWN

        obj = self.world_state_raw[x][y]
        obj_id = obj["id"]

        obj['x'] = x
        obj['y'] = y

        wrapped_obj = None
        if REGISTRY.lookup(obj_id, register_lookup=True) is None:
            wrapped_obj = REGISTRY.register(obj)
            self.object_id_coord[(x,y)] = obj_id
        else:
            wrapped_obj = REGISTRY.lookup(obj_id)
            self.object_id_coord[(x,y)] = obj_id

        objt = type(wrapped_obj)
        if issubclass(objt, Unit) or issubclass(objt, Building):
            wrapped_obj.update(obj)

        return wrapped_obj

    def get_coord(self, pair):
        x = pair[0]
        y = pair[1]

        obj_id = self.object_id_coord[(x,y)]

        # wonky system workout
        if obj_id == Other.UNOCCUPIED or obj_id == Other.UNKNOWN:
            return obj_id 

        if obj_id is not None:
            return REGISTRY.lookup(obj_id)
        
        return None

    def is_traversable(self, pair):
        x = pair[0]
        y = pair[1]

        obj_id = self.object_id_coord[(x,y)]

        # wonky system workout
        return (obj_id == Other.UNOCCUPIED or obj_id == Other.UNKNOWN or obj_id is None)


    # set the coordinate to the new 
    def set_coord(self, pair, wrapped_object):
        x = pair[0]
        y = pair[1]


        if wrapped_object == Other.UNKNOWN or wrapped_object == Other.UNOCCUPIED:
            self.object_id_coord[(x,y)] = wrapped_object
            return
        
        self.object_id_coord[(x,y)] = wrapped_object.id
        REGISTRY.registry[wrapped_object.id] = wrapped_object
        # TODO set the wrapped object in registry.
        # id is wrapped_object.id

    def gatherEmpire(self):
        all_units = [obj for obj in REGISTRY.dumpObjects() if issubclass(type(obj), Unit)]
        return [u for u in all_units if u.team == self.team_id]

    def gatherCity(self):
        all_buildings = [obj for obj in REGISTRY.dumpObjects() if issubclass(type(obj), Building)]
        return [b for b in all_buildings if b.team == self.team_id]
    
    def render(self):
        from render import TREE as COL_TREE, GOLD as COL_GOLD, NORM, teamcols

        print_string = ''
        for y in range(self.length):
            for x in range(self.height):
                obj = self.get_coord((x, y))

                if obj == Other.UNKNOWN:
                    print_string += NORM + "?."
                if obj == Other.UNOCCUPIED:
                    print_string += NORM + " ."
                if issubclass(type(obj), Unit):
                    t = obj.type()[0]
                    color = teamcols[obj.team]
                    print_string+= color + t + '.'
                if issubclass(type(obj), Resource):
                    color = ''
                    char = 'g'
                    if type(obj) == Tree:
                        color = COL_TREE
                        char = 't'
                    if type(obj) == Gold:
                        color = COL_GOLD
                        char = 'g'

                    extra = '.'
                    if obj.theoretical:
                        extra = '*'

                    print_string += color + char + extra

                if issubclass(type(obj), Building):
                    print_string += 'b '

            print_string += (NORM + '\n')
        print(print_string)



def run(world_state, players, team_idx):

    Unit.our_kingdom = team_idx 
    cws = CombinedWorldState(world_state, players, team_idx)

    # Always iterate over the map ONCE at the beginning to update units
    # and stuff.

    iterate_over_map(cws)
    #print(REGISTRY)

    empire = cws.gatherEmpire()

    commands = [unit.execute(cws) for unit in empire]

    cws.render()
    return (commands)
    # Determine what the foliage is for unexplored tiles.
