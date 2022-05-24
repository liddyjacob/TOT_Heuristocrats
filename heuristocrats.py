from asyncio.streams import FlowControlMixin
from glob import glob
from pickle import UNICODE
from tkinter.messagebox import NO
from tracemalloc import start
from ai.shitutils import get_tiles, path_to_coord
from enum import Enum
from engine import SKEL_TICKS
from render import render
from ai.heuristocrats.units import Villager, Archer, Infantry, Calvary, Skeleton, Unit
from ai.heuristocrats.buildings import Townhall, Barracks, Range, Stable, House, Building
from ai.heuristocrats.resources import MapObj, Resource, Tree, Gold,  Unknown, Unoccupied, MapObj
from ai.heuristocrats.constants import *
from ai.heuristocrats.utils import multi_aggregate
from ai.heuristocrats.annotated_world import ANNO_WORLD
import time
import statistics
import math

# notes
"""
Upgrade units policy: examine cost / power for one unit, then cost / power to upgrade all units.

"""

# todo make this create an instance of each object
def initializeObject(obj):
    if obj is None:
        return Unoccupied()

    if obj == 'u':
        return Unknown()

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

def name():
    return "Commrads"

# iterate over the map once to avoid redundancy of things that 
# require iteraton.
def iterate_over_map(cws):
    for x in range(cws.length):
        for y in range(cws.height):
            obj = cws.identify_and_associate(x,y)
            # update the 'annotated world'
            ANNO_WORLD.update(x,y,obj)

    ANNO_WORLD.modify_world_state(cws)
            # S

class POI(Enum):
    FOL_EXPLORE = 1,
    UNKNOWN_EXPLORE = 2,
    ENEMY_BUILDINGS = 3,
    ENEMY_VILLAGER_CLUSTERS = 4,
    CORNERS = 5


# Use this to force the world state to use my interfaces
class CombinedWorldState:
    def __init__(self, world_state, players, team_idx):
        self.world_state_raw = world_state
        self.players_raw = players
        self.team_id = team_idx
        self.height = len(self.world_state_raw)
        self.length = len(self.world_state_raw[0])
        
        # Associate coords with unique ids
        self.object_coord = {}

    def identify_and_associate(self,x,y):
        obj = self.world_state_raw[x][y]

        if type(obj) == dict:
            obj['x'] = x
            obj['y'] = y

        self.object_coord[(x,y)] = initializeObject(obj)
        return self.object_coord[(x,y)] 

    def get_coord(self, pair):
        x = pair[0]
        y = pair[1]

        return self.object_coord[(x,y)]

    def is_traversable(self, pair):
        x = pair[0]
        y = pair[1]

        obj = self.object_coord.get((x,y))

        # wonky system workout
        return (type(obj) == Unoccupied or type(obj) == Unknown)


    # set the coordinate to the new 
    def set_coord(self, pair, wrapped_object):
        x = pair[0]
        y = pair[1]
        
        self.object_coord[(x,y)] = wrapped_object
        # TODO set the wrapped object in registry.
        # id is wrapped_object.id

    def post_processing_steps(self):
        self.make_islands()

        avg_empire_location = self.gatherEmpire() + self.gatherCity()
        x_mean = statistics.mean([obj.x for obj in avg_empire_location])
        y_mean = statistics.mean([obj.y for obj in avg_empire_location])


        KINGDOM_CORNER = (int((x_mean / (self.length / 2))), int(y_mean / (self.length / 2)) )
        self.KINGDOM_XMIN = KINGDOM_CORNER[0] * (self.length / 2)
        self.KINGDOM_XMAX = self.KINGDOM_XMIN + (self.length / 2)
        self.KINGDOM_YMIN = KINGDOM_CORNER[1] * (self.length / 2)
        self.KINGDOM_YMAX = self.KINGDOM_YMIN + (self.length / 2)
        print(x_mean, y_mean)

        self.make_pois()
    
    def build_island(self, x, y, island_id = 0):

        # If the land is already visited
        # or there is no land or the
        # coordinates gone out of matrix
        # break function as there
        # will be no islands
        stack = [(x,y)]

        while stack:
            (xn,yn) = stack.pop()
            
            if not self.is_traversable((xn, yn)):
                self.island_ids[(xn,yn)] = 0


            if (xn < 0 or yn < 0 or
                xn >= self.length or yn >= self.height or
                self.island_ids.get((xn, yn)) is not None or
                not self.is_traversable((xn, yn))):
                continue

            
            self.island_ids[(xn,yn)] = island_id
            stack.append((xn, yn + 1))
            stack.append((xn, yn - 1))
            stack.append((xn - 1, yn))
            stack.append((xn + 1, yn))
            stack.append((xn + 1, yn + 1))
            stack.append((xn + 1, yn - 1))
            stack.append((xn - 1, yn + 1))
            stack.append((xn - 1, yn - 1))

    def make_islands(self):
    # unvisited.
        self.island_ids = {}

    
        # To stores number of closed islands
        result = 0
    
        for i in range(self.length):
            for j in range(self.height):
                
                # If the land not visited
                # then there will be atleast
                # one closed island
                if (self.island_ids.get((i,j)) is None):
                    if self.is_traversable((i, j)):

                        result += 1
                    
                        # Mark all lands associated
                        # with island visited.
                        self.build_island(i, j, island_id = result)
                    else:
                        self.island_ids[(i,j)] = 0
              

#  Driver Code

    def _make_pois_fexplore(self):
        point_map = self.point_maps['fexplore']

        self.pois.add(max(point_map, key=point_map.get))
        print(self.pois)

    def _make_pois_empire_corners(self):

        self.pois.add((5,5))
        self.pois.add((5,self.height - 6))
        self.pois.add((self.length - 6,self.height - 6))
        self.pois.add((self.length - 6,5))

    # this is going to be a major slow down
    def _run_point_masks(self):
        self.masked_point_map = {}
        self.masks = {}
        self.point_maps = {}

        for key in self.point_map_types:
            self.masked_point_map[key] = {}
            self.masks[key] = {}
            self.point_maps[key] = {}

            for x in range(self.length):
                for y in range(self.height):
                    m_lamb = self.mask_lambdas[key]

                    obj = self.get_coord((x,y))
                    p_lam = self.point_map_lambdas[key]
                    self.point_maps[key][(x,y)] = p_lam(obj) * m_lamb(x,y)

            num_runs = self.agg_executions[key]
            self.point_maps[key] = multi_aggregate(self.point_maps[key], num_runs)

    # POINTS OF INTEREST
    def make_pois(self):
            # make a map for every type of point of interest and mask ( messy but a real time saver )
            self.point_map_types = ['fexplore']

            self.mask_lambdas = {
                'fexplore': lambda x, y: 
                    math.sin((math.pi * (x) / (self.length)) * (1 - math.sin((math.pi *y) / (self.height)))) if 
                    (self.KINGDOM_XMIN <= x < self.KINGDOM_XMAX) and (self.KINGDOM_YMIN <= y < self.KINGDOM_YMAX) else
                    0,
                'explore': lambda x, y: math.sqrt(math.sqrt(
                    (abs(x - (self.length/2)) + (self.length/2)) * (abs(y - (self.height/2)) + (self.height /2))
                    ) / (self.length + self.height)),
            }

            self.point_map_lambdas = {
                'fexplore': lambda obj: int(type(obj) == Unknown),
                'explore': lambda obj: 0 if not issubclass(type(obj), MapObj) else int(obj.theoretical) 
            }

            self.agg_executions = {
                'fexplore': 4,
                'explore': 6
            }

            self.pois = set()

            self._run_point_masks()
            self._make_pois_fexplore()
            self._make_pois_empire_corners()


    def gatherEmpire(self):
        all_units = [obj for obj in self.object_coord.values() if issubclass(type(obj), Unit)]
        return [u for u in all_units if u.team == self.team_id]

    def gatherCity(self):
        all_buildings = [obj for obj in self.object_coord.values() if issubclass(type(obj), Building)]
        return [b for b in all_buildings if b.team == self.team_id]
    
    def render(self):
        from render import TREE as COL_TREE, GOLD as COL_GOLD, NORM, teamcols

        print_string = ''
        for y in range(self.length):
            for x in range(self.height):
                obj = self.get_coord((x, y))

                if issubclass(type(obj), Unit):
                    t = obj.type()[0]
                    color = teamcols[obj.team]
                    print_string+= color + t + '.'
                if issubclass(type(obj), MapObj):
                    color = ''
                    char = 'g'

                    extra = '.'
                    if obj.theoretical:
                        extra = '*'

                    if type(obj) == Tree:
                        color = COL_TREE
                        char = 't'
                    if type(obj) == Gold:
                        color = COL_GOLD
                        char = 'g'
                    if type(obj) == Unknown:
                        color = NORM
                        char = '?'
                        extra = '?'

                    if type(obj) == Unoccupied:
                        color = NORM
                        char = ' '

                    print_string += color + char + extra

                if issubclass(type(obj), Building):
                    print_string += 'b '

                if (x,y) in self.pois:
                    print_string = print_string[:-1] + COL_GOLD + 'X'
                print_string += str(self.island_ids[(x,y)])


            print_string += (NORM + '\n')
        print(print_string)



def run(world_state, players, team_idx):

    start_time = time.time()

    Unit.our_kingdom = team_idx 
    cws = CombinedWorldState(world_state, players, team_idx)

    # Always iterate over the map ONCE at the beginning to update units
    # and stuff.

    iterate_over_map(cws)
    cws.post_processing_steps()
    #print(REGISTRY)

    middle_time = time.time()

    print(middle_time - start_time)

    empire = cws.gatherEmpire()

    commands = [unit.execute(cws) for unit in empire]


    cws.render()
    return (commands)
    # Determine what the foliage is for unexplored tiles.
