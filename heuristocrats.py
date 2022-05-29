from asyncio.streams import FlowControlMixin
from glob import glob
from pickle import UNICODE
from tkinter.messagebox import NO
from tracemalloc import start
from ai.shitutils import get_tiles, path_to_coord
from enum import Enum
from engine import SKEL_TICKS
from render import render
from ai.heuristocrats.units import Villager, Archer, Infantry, Calvary, Skeleton, Unit, reset_number_system
from ai.heuristocrats.buildings import Townhall, Barracks, Range, Stable, House, Building
from ai.heuristocrats.resources import MapObj, Resource, Tree, Gold,  Unknown, Unoccupied, MapObj
from ai.heuristocrats.constants import *
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
        self.building_helper = {}
        self.someone_building = False

        # sorting is expensive, so we need markers to determine if we have done it
        self.tc_sorted=False
        self.tc_spots = []
        self.training_sorted=False
        self.training_spots = []
        self.house_sorted=False
        self.house_spots = []

        self.fort_helper = {}
        self.fort_info = [((0,0), None, None)]

        self.resources_ordered = {}
        # debug
        self.tclc = None


        self.wood = players[team_idx]['wood']
        self.gold = players[team_idx]['gold']

        # Associate coords with unique ids
        self.object_coord = {}

    def can_afford(self, pair):
        return ( self.wood >= pair[0] and self.gold >= pair[1] )

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


    # LOCATIONS ARE ALWAYS WHERE VILLAGERS SHOULD GO.
    # ALWAYS BOTTOM RIGHT. BRING THE VILLAGER THERE,
    # THEN BUILD IN THE -1, -1 DIRECTION.
    def get_tc_location(self):
        if not self.tc_sorted:
            self.tc_spots = sorted(self.tc_spots, key = lambda pair: max(abs(pair[0] - self.KINGDOM_EXTREME[0]),
                abs(pair[1] - self.KINGDOM_EXTREME[1])), reverse=True)
            self.tc_sorted = True

        tc_location = self.tc_spots[-1]
        return tc_location

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

    def get_corner_resource(self, typeof, island_ids):
        # todo rewrite this
        if self.resources_ordered.get(typeof) is None:
            self.resources_ordered[typeof] = {}
            for i in range(self.num_islands):
                self.resources_ordered[typeof][i + 1] = []
                all_x = [(obj.x, obj.y) for obj in self.object_coord.values() 
                    if type(obj) == typeof and (i + 1) in obj.island_ids]
                
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
        #' We need to do a few things:
        #' (1) Find any squares of size 4x4 and 5x5. Any 5x5 spot is great for a town center,
        #' and a 4x4 spot can be used for anything.
        #' Also, 2x2 spots can be used for houses
        #'
        #' (2) Find any forests for size 5x5 or larger. These will become outposts.
        self.building_helper[(x,y)] = 0
        obj_at = self.get_coord((x,y))

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
                self.tc_spots.append((x,y))
                self.training_spots.append((x,y))
                self.house_spots.append((x,y))

            #if self.building_helper[(x,y)] >= 3:

        # TODO CHECK IF WE NEED TO FIND THIS VALUE?

        if type(self.get_coord((x,y))) != Tree:
            self.fort_helper[(x,y)] = (0,0)

        else:
            if x == 0 or y == 0:
                self.fort_helper[(x,y)] = (1,1)
            else:
                # 
                self.fort_helper[(x,y)] = (
                min( 
                    self.fort_helper[(x-1,y)][0], 
                    self.fort_helper[(x,y-1)][0], 
                    self.fort_helper[(x-1,y-1)][0]
                ) + 1,
                min( 
                    self.fort_helper[(x-1,y)][1], 
                    self.fort_helper[(x,y-1)][1], 
                    self.fort_helper[(x-1,y-1)][1]
                ) + 1)

            # new max square found at x,y
            if self.fort_helper[(x,y)][0]*self.fort_helper[(x,y)][1] >= self.fort_info[0][0][0] * self.fort_info[0][0][1]:
                # we only care about forests with 5x5 or larger areas
                if ((self.fort_helper[(x,y)][0] > 5 or self.fort_helper[(x,y)][1] > 4) or 
                    (self.fort_helper[(x,y)][0] > 4 or self.fort_helper[(x,y)][1] > 5)):
                        if self.fort_helper[(x,y)][0]*self.fort_helper[(x,y)][1] == self.fort_info[0][0][0] * self.fort_info[0][0][1]:
                            self.fort_info.append((self.fort_helper[(x,y)], x, y))
                        else:
                            self.fort_info = [(self.fort_helper[(x,y)], x, y)]

    def save_input_trees(self):
        true_corner = (max(0, self.KINGDOM_EXTREME[0]-1), max(0, self.KINGDOM_EXTREME[1]-1))
        starting_id = self.get_island_id(true_corner)
        self.X_TREE = self.get_coord(self.get_corner_resource(Tree, [starting_id]))
        self.Y_TREE = self.get_coord(self.get_corner_resource(Tree, [starting_id]))
        self.LENGTH_TREE = self.get_coord(self.get_corner_resource(Tree, [starting_id]))
        self.HEIGHT_TREE = self.get_coord(self.get_corner_resource(Tree, [starting_id]))

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

        print(f"ext: {self.KINGDOM_EXTREME}")
        self.make_islands()
        #self.save_input_trees()
        self.make_pois()

        self.next_tc_location = self.get_tc_location()
    
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

        self.pois.add((5,5))
        self.pois.add((5,self.height - 6))
        self.pois.add((self.length - 6,self.height - 6))
        self.pois.add((self.length - 6,5))

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

    def gatherCity(self):
        if self.city is None:
            all_buildings = [obj for obj in self.object_coord.values() if issubclass(type(obj), Building)]
            self.city = list(set([b for b in all_buildings if b.team == self.team_id]))
        return self.city
    
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
                    color = teamcols[obj.team]
                    print_string += color + 'b '

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
    cws.render()
    print(cws.wood, cws.gold)

    reset_number_system()

    return (unit_commands + building_commands)
    # Determine what the foliage is for unexplored tiles.
