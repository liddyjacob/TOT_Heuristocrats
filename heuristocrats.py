from asyncio.streams import FlowControlMixin
from glob import glob
from tkinter.messagebox import NO
from ai.shitutils import get_tiles, path_to_coord
from enum import Enum
from render import render
from ai.heuristocrats.units import Villager, Archer, Infantry, Calvary, Skeleton, Unit
from ai.heuristocrats.buildings import Townhall, Barracks, Range, Stable, House, Building
from ai.heuristocrats.resources import Tree, Gold, Other
from ai.heuristocrats.constants import *
from ai.heuristocrats.foliage_finder import initialize_foliage_state, reflect
from ai.heuristocrats.exploration import initialize_exp_weight_map, multi_aggregate, exp_render, find_target_on_heatmap
from ai.heuristocrats.utils import generate_exploration_map, getClosedIslands, printAsIs, cust_render


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

    def lookup(self, id):
        # used to determine if an object has died.
        self.registerLookup(id)
        return self.registry.get(id)

    # Deregester all the unnaccounted members
    def deregisterUnaccounted(self):
        [self.registry.pop(key) for key in self.not_lookup]
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

    for x in range(WSIZE):
        for y in range(WSIZE):
            cws.identify_and_associate(x,y)

    REGISTRY.deregisterUnaccounted()
            # S

# Use this to force the world state to use my interfaces
class CombinedWorldState:
    def __init__(self, world_state, players, team_idx):
        self.world_state_raw = world_state
        self.players_raw = players
        self.team_id = team_idx
        
        # Associate coords with unique ids
        self.object_id_coord = {}

    def identify_and_associate(self,x,y):
        global REGISTRY

        # WARNING THIS REMOVES INFORMATION FROM THE MAP
        if self.world_state_raw[x][y] is None:
            self.object_id_coord[(x,y)] = Other.UNOCCUPIED
            return

        # I NEED TO DIFFERENTIATE BETWEEN UNVISITED AND UNOCCUPIED.
        if self.world_state_raw[x][y] == 'u':
            self.object_id_coord[(x,y)] = Other.UNKNOWN
            return

        obj = self.world_state_raw[x][y]
        obj_id = obj["id"]

        if REGISTRY.lookup(obj_id) is None:
            wrapped_obj = REGISTRY.register(obj)
            self.object_id_coord[(x,y)] = wrapped_obj         

    def get_coord(self, pair):
        x = pair[0]
        y = pair[1]

        obj_id = self.object_id_coord[(x,y)]
        if obj_id is not None:
            return REGISTRY.lookup(obj_id)
        
        return None

    def gatherEmpire(self):
        all_units = [obj for obj in REGISTRY.dumpObjects() if issubclass(type(obj), Unit)]
        return [u for u in all_units if u.team == self.team_id]

    def gatherCity(self):
        all_buildings = [obj for obj in REGISTRY.dumpObjects() if issubclass(type(obj), Building)]
        return [b for b in all_buildings if b.team == self.team_id]
    
    
def run(world_state, players, team_idx):

    cws = CombinedWorldState(world_state, players, team_idx)

    # Always iterate over the map ONCE at the beginning to update units
    # and stuff.

    iterate_over_map(cws)
    print(REGISTRY)

    empire = cws.gatherEmpire()
    
    commands = [unit.execute() for unit in empire]

    return ({})
    # Determine what the foliage is for unexplored tiles.
