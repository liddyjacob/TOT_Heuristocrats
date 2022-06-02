from asyncio.streams import FlowControlMixin
from glob import glob
from pickle import UNICODE
from tkinter.messagebox import NO
from tracemalloc import start
from ai.shitutils import get_tiles, path_to_coord
from enum import Enum
from engine import SKEL_TICKS
from render import TREE, render
from ai.heuristocrats.units import Villager, Archer, Infantry, Calvary, Skeleton, Unit, reset_number_system
from ai.heuristocrats.buildings import Townhall, Barracks, Range, Stable, House, Building
from ai.heuristocrats.resources import MapObj, Resource, Tree, Gold,  Unknown, Unoccupied, MapObj
from ai.heuristocrats.constants import *
from ai.heuristocrats.annotated_world import ANNO_WORLD
from ai.heuristocrats.utils import resource_plinko_board
import time
import statistics
import math


# TODO USE MINUTE NUMBER MOD 3 TO DETERMINE 'WANDERING' LOCATION FOR VILLAGERS!
# NOTE THIS SHOULD ALWAYS BE INSIDE THE KINGDOM.
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
    dp_tree_square = [[(0,0)] * 96 for _ in range(96)]
    max_square = ((0,0),None, None)
    for x in range(cws.length):
        for y in range(cws.height):
            obj = cws.identify_and_associate(x,y)
            cws.process(x,y)

            # update the 'annotated world'
            ANNO_WORLD.update(x,y,obj)

    ANNO_WORLD.modify_world_state(cws)
    print(max_square)
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
        self.empire = None
        self.city = None
        self.someone_building = False

        # sorting is expensive, so we need markers to determine if we have done it
        # 
        self.x_alley_helper = {}
        self.y_alley_helper = {}

        self.x_alley_size = 0
        self.y_alley_size = 0

        self.fort_helper = {}
        self.fort_info = [((0,0), None, None)]

        self.resources_ordered = {}
        # debug
        self.building_helper = {}
        self.tc_spots = set()
        self.tclc = None

        self.reserved_trees = []

        self.wood = players[team_idx]['wood']
        self.gold = players[team_idx]['gold']

        self.level = {}
        self.level[Calvary] = players[team_idx]['cav_level']
        self.level[Archer] = players[team_idx]['arc_level']
        self.level[Infantry] = players[team_idx]['inf_level']


        self.someone_building = {}
        self.num_vils_exploring = {}
        for btype in [Townhall, Barracks, Range, Stable, House]:
            self.someone_building[btype] = False
            self.num_vils_exploring[btype] = 0


        # Associate coords with unique ids
        self.object_coord = {}

    def can_afford(self, pair):
        return ( self.wood >= pair[0] and self.gold >= pair[1] )

    def identify_and_associate(self,x,y):
        obj = self.world_state_raw[x][y]

        if type(obj) == dict:
            obj['x'] = x
            obj['y'] = y

        if self.object_coord.get((x,y)) is not None:
            return self.object_coord[(x,y)]

        self.object_coord[(x,y)] = initializeObject(obj)
        return self.object_coord[(x,y)]

    def get_coord(self, pair):
        x = pair[0]
        y = pair[1]

        return self.object_coord.get((x,y))

    def is_traversable(self, pair):
        x = pair[0]
        y = pair[1]

        obj = self.object_coord.get((x,y))

        # wonky system workout
        return (type(obj) == Unoccupied or type(obj) == Unknown) and not obj.travel_ban

    # block a box from being travelled in: 
    def block_box(self, loc, size):
        for dx in range(size):
            for dy in range(size):
                if dx == 0 and dy ==0:
                    continue
                obj = self.get_coord((loc[0] - dx, loc[1] - dy))
                obj.travel_ban = True

    def get_housing(self):
        housing  = 0
        for c in self.gatherCity():
            housing += c.housing()

        return housing



    # LOCATIONS ARE ALWAYS WHERE VILLAGERS SHOULD GO.
    # ALWAYS BOTTOM RIGHT. BRING THE VILLAGER THERE,
    # THEN BUILD IN THE -1, -1 DIRECTION.
    def get_training_location(self):
        if not self.training_sorted:
            self.training_spots = sorted(self.training_spots, key = lambda pair: max(abs(pair[0] - self.KINGDOM_EXTREME[0]),
                abs(pair[1] - self.KINGDOM_EXTREME[1])), reverse=True)
            self.training_sorted = True

        train_location = self.training_spots[-1]
        self.training_spots.pop()
        return train_location


    # LOCATIONS ARE ALWAYS WHERE VILLAGERS SHOULD GO.
    # ALWAYS BOTTOM RIGHT. BRING THE VILLAGER THERE,
    # THEN BUILD IN THE -1, -1 DIRECTION.
    def get_house_location(self):
        if not self.house_sorted:
            self.house_spots = sorted(self.house_spots, key = lambda pair: max(abs(pair[0] - self.KINGDOM_EXTREME[0]),
                abs(pair[1] - self.KINGDOM_EXTREME[1])), reverse=True)
            self.house_sorted = True

        house_location = self.house_sorted[-1]
        self.house_sorted.pop()
        return house_location

    # for counting:
    def reserve_first_n_trees(self, n):
        all_trees = [obj for obj in self.object_coord.values() if type(obj) == Tree and obj.reserved == False]

        if len(all_trees) < n:
            return 
        
        trees_sorted = sorted(all_trees, key = lambda tob: max(abs(tob.x - self.KINGDOM_EXTREME[0]),
                abs(tob.y - self.KINGDOM_EXTREME[1])), reverse=True)

        for i in range(n):
            trees_sorted[-(i + 1)].reserved=True
            self.reserved_trees.append(trees_sorted[-(i + 1)])

    def get_corner_resource(self, typeof, island_ids):
        # todo rewrite this
        if self.resources_ordered.get(typeof) is None:
            self.resources_ordered[typeof] = {}
            for i in range(self.num_islands):
                self.resources_ordered[typeof][i + 1] = []
                all_x = [(obj.x, obj.y) for obj in self.object_coord.values() 
                    if type(obj) == typeof and (i + 1) in obj.island_ids and obj.reserved == False]
                
                all_x = sorted(all_x, key = lambda pair: max(abs(pair[0] - self.KINGDOM_EXTREME[0]),
                abs(pair[1] - self.KINGDOM_EXTREME[1])), reverse=True)
                
                self.resources_ordered[typeof][i + 1] = all_x

        for id in island_ids:
            if len(self.resources_ordered[typeof][id]):
                rval = self.resources_ordered[typeof][id][-1]

                if len(self.resources_ordered[typeof][id]) > 2:
                    self.resources_ordered[typeof][id].pop()
                    self.resources_ordered[typeof][id].pop()
                if typeof == Tree:
                    if len(self.resources_ordered[typeof][id]) > 2:
                        self.resources_ordered[typeof][id].pop()
                        self.resources_ordered[typeof][id].pop()
                return rval

        print(f'requested but did not exist: {typeof}')
        return None

    # set the coordinate to the new 
    def set_coord(self, pair, wrapped_object):
        x = pair[0]
        y = pair[1]
        
        self.object_coord[(x,y)] = wrapped_object
        # TODO set the wrapped object in registry.
        # id is wrapped_object.id

    def get_island_id(self, pair):
        x = pair[0]
        y = pair[1]
        
        id = self.island_ids.get((x,y))
        if id is None:
            return 0
        else:
            return id

    def process(self, x, y):
        #' New rules, just find the longest set of trees, and funnel archers into those.
        #' The rules for these archers are:
        #' (1) check to see if archer line is full
        #  (2) if not full, move archers to the right/down
        #      when there is an empty spot next to them
        #  (3) shoot anything not on my team. Prioritize villagers, then
        #      calvary, then infantry, then buildings/
        self.building_helper[(x,y)] = 0

        if not self.is_traversable((x,y)):
            self.building_helper[(x,y)] = 0
        else:
            if x == 0 or y == 0:
                # 1x1 square
                self.building_helper[(x,y)] = 1
            else:
                self.building_helper[(x,y)] = (min( 
                    self.building_helper[(x-1,y)], 
                    self.building_helper[(x,y-1)], 
                    self.building_helper[(x-1,y-1)]
                ) + 1)

            # new max square found at x,y
            #if self.building_helper[(x,y)] >= 5:
            if self.building_helper[(x,y)] >= 4:
                self.tc_spots.add((x,y))

        if x == 0:
            self.x_alley_helper[(x, y)] = int(type(self.get_coord((x,y))) == Tree)
            self.y_alley_helper[(y, x)] = int(type(self.identify_and_associate(y,x)) == Tree)
        else:
            if type(self.get_coord((x,y))) == Tree:
                self.x_alley_helper[(x, y)] = self.x_alley_helper[(x - 1, y)] + 1
            else:
                self.x_alley_helper[(x, y)]  = 0
            
            if type(self.identify_and_associate(y,x)) == Tree:
                self.y_alley_helper[(y, x)] = self.y_alley_helper[(y, x - 1)] + 1    
            else:
                self.y_alley_helper[(y, x)] = 0

    def post_processing_steps(self):
        avg_empire_location = self.gatherEmpire() + self.gatherCity()
        x_mean = statistics.mean([obj.x for obj in avg_empire_location])
        y_mean = statistics.mean([obj.y for obj in avg_empire_location])

        KINGDOM_CORNER = (int((x_mean / (self.length / 2))), int(y_mean / (self.length / 2)) )
        self.KINGDOM_XMIN = int(KINGDOM_CORNER[0] * (self.length / 2))
        self.KINGDOM_XMAX = int(self.KINGDOM_XMIN + (self.length / 2))
        self.KINGDOM_YMIN = int(KINGDOM_CORNER[1] * (self.length / 2))
        self.KINGDOM_YMAX = int(self.KINGDOM_YMIN + (self.length / 2))

        self.KINGDOM_EXTREME = (KINGDOM_CORNER[0] * self.length, KINGDOM_CORNER[1] * self.height)

        self.reserve_first_n_trees(7)
        print(f"ext: {self.KINGDOM_EXTREME}")
        self.make_islands()
        self.mark_alleys()
        #self.save_input_trees()
        self.make_pois()


    def is_in_kingdom(self, x,y):
        return ((x < self.KINGDOM_XMAX and x >= self.KINGDOM_XMIN) 
            and (y < self.KINGDOM_YMAX and y >= self.KINGDOM_YMIN))

    def mark_alleys(self):
        y = self.x_alley_location[1]
        xi = self.x_alley_location[0]
        for x in range(self.x_alley_size):
            obj = self.get_coord((xi - x,y))
            obj.alley = True
            # also get nearby:
            obj_low = self.get_coord((xi - x,y - 1))
            if type(obj_low) == Tree:
                obj_low.reserved = True
            
            obj_high = self.get_coord((xi - x,y + 1))
            if type(obj_high) == Tree:
                obj_high.reserved = True

        x = self.y_alley_location[0]
        yi = self.y_alley_location[1]
        for y in range(self.y_alley_size):
            obj = self.get_coord((x,yi - y))
            obj.alley = True

            obj_low = self.get_coord((x - 1,yi - y))
            if type(obj_low) == Tree:
                obj_low.reserved = True
            
            obj_high = self.get_coord((x + 1,yi - y))
            if type(obj_high) == Tree:
                obj_high.reserved = True

    def build_island(self, x, y, island_id = 0):

        # If the land is already visited
        # or there is no land or the
        # coordinates gone out of matrix
        # break function as there
        # will be no islands
        stack = [(x,y)]

        while stack:
            (xn,yn) = stack.pop()

            obj = self.get_coord((xn,yn))
            if obj is not None:
                if type(obj) != Unknown and type(obj) != Unoccupied:
                    obj.island_ids.add(island_id) 
            
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

                if self.is_in_kingdom(i,j):
                    if self.x_alley_helper[(i,j)] > self.x_alley_size:
                        self.x_alley_size = self.x_alley_helper[(i,j)]
                        self.x_alley_location = (i,j)
                    if self.y_alley_helper[(i,j)] > self.y_alley_size:
                        self.y_alley_size = self.y_alley_helper[(i,j)]
                        self.y_alley_location = (i,j)


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
        self.num_islands = result


    def make_forest(self):
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
        self.num_islands = result

#  Driver Code

    def _make_pois_fexplore(self):
        self.fexplore_waypoints = []         

        for x in range(self.KINGDOM_XMIN, self.KINGDOM_XMAX):
            for y in range(self.KINGDOM_YMIN, self.KINGDOM_YMAX):
                if 0 == (x % 8) and 0 == (y % 8):

                    if type(self.get_coord((x,y))) == Unknown:
                        self.fexplore_waypoints.append((x,y))
                        self.pois.add((x,y))


    def percent_uncovered_f(self):

        p =  len([obj for obj in self.object_coord.values() if type(obj) != Unknown]) / (self.length * self.height)
        return(p)

    def _make_pois_empire_corners(self):
        for point in [(5,5), (5,self.height - 6), (self.length - 6,self.height - 6), (self.length - 6,5)]:
            obj = self.get_coord(point)
            if (type(obj) == Unknown):
                self.pois.add(point)
                next
            if issubclass(type(obj), MapObj) and self.get_coord(point).theoretical:
                self.pois.add(point)

    # POINTS OF INTEREST
    def make_pois(self):
            # make a map for every type of point of interest and mask ( messy but a real time saver )
            self.pois = set()
            self._make_pois_fexplore()
            self._make_pois_empire_corners()

    def gatherEmpire(self):
        if self.empire is None:
            all_units = [obj for obj in self.object_coord.values() if issubclass(type(obj), Unit)]
            self.empire = [u for u in all_units if u.team == self.team_id]
            self.empire = sorted(self.empire, key=lambda obj: obj.id, reverse=True)
        return self.empire

    def getPopulation(self, typeof):
        empire = self.gatherEmpire()
        pop = 0
        for e in empire:
            if type(e) == typeof:
                pop+=1

        return pop

    def gatherCity(self):
        if self.city is None:
            all_buildings = [obj for obj in self.object_coord.values() if issubclass(type(obj), Building)]
            self.city = list(set([b for b in all_buildings if b.team == self.team_id]))
        return self.city

    def num_buildings(self, typeof):
        num = 0
        for c in self.gatherCity():
            if type(c) == typeof:
                num+=1

        return num 
    
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
                        if obj.reserved:
                            char = 'R'
                        else:
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
                    if obj.alley:
                        print_string = print_string[:-1] + COL_GOLD + '#' 

                if issubclass(type(obj), Building):
                    color = teamcols[obj.team]
                    print_string += color + obj.rep() + ' '

                if (x,y) in self.pois:
                    print_string = print_string[:-1] + COL_GOLD + 'X'

                if (x,y) == self.tclc:
                    print_string = print_string[:-2] + COL_GOLD + 'TC'


            print_string += (NORM + '\n')
        print(print_string)

def run(world_state, players, team_idx):
    NUMBER_SYSTEM = {}
    start_time = time.time()

    Unit.our_kingdom = team_idx 
    cws = CombinedWorldState(world_state, players, team_idx)
    cws.start_time = start_time

    # Always iterate over the map ONCE at the beginning to update units
    # and stuff.
    iterate_over_map(cws)
    cws.post_processing_steps()
    resource_plinko_board(cws)
    #print(REGISTRY)

    middle_time = time.time()

    print(f"mid: {middle_time - start_time}")

    empire = cws.gatherEmpire()


    # Leave .1 sec for buffer
    # Only give the first n players 
    # Leave .05 seconds for buildings
    unit_commands = []
    for u in empire:
        if time.time() - start_time < .68:
            m = u.execute(cws)
            unit_commands.append(m)
        elif time.time() - start_time < .85:
            m = u.execute_basic(cws)
            unit_commands.append(m)
        else:
            break

    building_commands = []
    for b in cws.gatherCity():
        if time.time() - start_time < .95:
            m = b.execute(cws)
            building_commands.append(m)
        else:
            break


    end_time = time.time()
    print(f"end: {end_time - middle_time}")
    """

    if ((end_time - middle_time) >.7):
        import json
        # create json object from dictionary
        json_world = json.dumps(world_state)

        # open file for writing, "w" 
        f = open("world.json","w")

        # write json object to file
        f.write(json_world)

        # close file
        f.close()

        json_players = json.dumps(players)

        f = open("players.json","w")

        # write json object to file
        f.write(json_players)

        # close file
        f.close()

        print(team_idx)

        quit("Long proc time")
    """
    #print(cws.x_alley_helper)
    cws.render()
    print(cws.wood, cws.gold)
    print(players[team_idx])

    reset_number_system()

    return (unit_commands + building_commands)
    # Determine what the foliage is for unexplored tiles.
