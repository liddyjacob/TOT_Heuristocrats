from asyncio.streams import FlowControlMixin
from glob import glob
from locale import normalize
from pickle import UNICODE
from tkinter.messagebox import NO
from tracemalloc import start
from turtle import pos
from ai.shitutils import get_tiles, path_to_coord
from enum import Enum
from engine import SKEL_TICKS, ID_MAX
from render import TREE, render
from ai.heuristocrats.units import Villager, Archer, Infantry, Calvary, Skeleton, Unit, reset_number_system
from ai.heuristocrats.buildings import Townhall, Barracks, Range, Stable, House, Building
from ai.heuristocrats.resources import MapObj, Resource, Tree, Gold,  Unknown, Unoccupied, MapObj
from ai.heuristocrats.constants import *
from ai.heuristocrats.annotated_world import ANNO_WORLD
from ai.heuristocrats.utils import get_vect_length, project_onto, resource_plinko_board, \
    scalar_times_vector, upgrade_over_build, get_path_a_star, vector_add, scalar_times_vector, \
    project_onto
from ai.heuristocrats.profiling import PROFILER
import time
import statistics
import math
import random
from copy import deepcopy

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
            obj.x = x
            obj.y = y
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
        self.enemyEmpire = None
        self.city = None
        self.enemyCity = None
        self.someone_building = False
        self.villager_can_build = {}
        self.villager_can_build[(2,2)] = False
        self.villager_can_build[(3,3)] = False
        self.archer_id = 0
        self.villager_index = 0

        # sorting is expensive, so we need markers to determine if we have done it
        # 

        self.fort_helper = {}
        self.fort_info = [((0,0), None, None)]

        self.resources_ordered = {}
        # debug
        self.building_helper = {}
        self.bld_spots = {}
        self.bld_spots[(3,3)] = set()
        self.bld_spots[(2,2)] = set()
        self.tclc = None

        self.reserved_trees = []

        self.wood = players[team_idx]['wood']
        self.gold = players[team_idx]['gold']

        self.level = {}
        self.level[Calvary] = players[team_idx]['cav_level']
        self.level[Archer] = players[team_idx]['arc_level']
        self.level[Infantry] = players[team_idx]['inf_level']
        self.level[Villager] = 1


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

    # Find a point near x, y
    def get_nearby_travel(self, pair, dist=4, rand=True, island=None):
        neighbors = []
        for dx in range(-dist,dist + 1):
            for dy in range(-dist, dist + 1):
                neighbors.append((pair[0] + dx, pair[1] + dy))
        
        if rand:
            neighbors = sorted(neighbors, key = lambda npair: max(abs(npair[0] - pair[0]),
                abs(npair[1] - pair[1])) + random.random())
        else:
            neighbors = sorted(neighbors, key = lambda npair: max(abs(npair[0] - pair[0]),
                abs(npair[1] - pair[1])))

        for n in neighbors:
            if self.is_traversable(n):
                if island is None:
                    return n
                
                if self.get_island_id(n) == island:
                    return n

        return None




    # Build the 'frontier' of the map. This is where we will station units
    def build_frontier(self):
        if len(self.gatherCity()) == 0:
            self.border_path = [(self.length/2 ,self.height/2)]
            self.frontier_points = []
            self.ecl = []
            return

        frontier_outline = []

        city_vectors = [(c.x - self.KINGDOM_EXTREME[0], c.y - self.KINGDOM_EXTREME[1]) for c in self.gatherCity()]
        boarder_vectors = []


        if self.KINGDOM_EXTREME[0] == self.length:
            if self.KINGDOM_EXTREME[1] == self.height:
                boarder_vectors.append((-1, 0))
                boarder_vectors.append((-1, -math.tan(math.pi/8)))
                boarder_vectors.append((-1, -1))
                boarder_vectors.append((-1, -math.tan(3*math.pi/8)))
                boarder_vectors.append((0, -1))
            else:
                boarder_vectors.append((0, 1))
                boarder_vectors.append((-math.tan(math.pi/8), 1))
                boarder_vectors.append((-1, 1))
                boarder_vectors.append((-math.tan(3*math.pi/8), 1))
                boarder_vectors.append((-1, 0))                
        else:
            if self.KINGDOM_EXTREME[1] == self.height:
                boarder_vectors.append((0, -1))
                boarder_vectors.append((math.tan(math.pi/8), -1))
                boarder_vectors.append((1, -1))
                boarder_vectors.append((math.tan(3*math.pi/8), -1))
                boarder_vectors.append((1, 0))
            else:
                boarder_vectors.append((1, 0))
                boarder_vectors.append((1, math.tan(math.pi/8)))
                boarder_vectors.append((1, 1))
                boarder_vectors.append((1, math.tan(3*math.pi/8)))
                boarder_vectors.append((0, 1))
        
        normalized_vectors = []
        # next we normalize the vectors
        for b in boarder_vectors:
            dist = math.sqrt(b[0]**2 + b[1]**2)
            normalized_vectors.append(tuple(bt/dist for bt in b))

        self.ecl = []
        # Then, for each vector, find the projection with the maximum size
        for nb in normalized_vectors:
            extreme_city_location = max(city_vectors,
                key=lambda cv: get_vect_length(project_onto(cv, nb)))
            self.ecl.append((int(self.KINGDOM_EXTREME[0] + extreme_city_location[0]),int(self.KINGDOM_EXTREME[1] + extreme_city_location[1])))
            
            # Need to extreme_city_location
            border_extension = scalar_times_vector(
                BORDER_DISTANCE + get_vect_length(project_onto(extreme_city_location, nb)), nb)
            frontier_point_float = vector_add(border_extension, self.KINGDOM_EXTREME)
            frontier_point_int = (int(frontier_point_float[0]), int(frontier_point_float[1]))
            frontier_outline.append(frontier_point_int)

        self.frontier_points = frontier_outline

        print(self.frontier_points)
        # Add kingdom_extreme to this vector and BORDER_SIZE* the original vector
        # to get the boarder point
        frontier_outline_neighbors = []


        biggest_island = max(self.island_length, key=self.island_length.get)
        # Join these boarder points in a path.
        for point in frontier_outline:
            # TODO only add points that are in the most common island.
            np = self.get_nearby_travel(point, dist=8, rand=False, island=biggest_island)
            if np is not None:
                frontier_outline_neighbors.append(np)

        # See what the common "island" is:

        
        self.border_path = []
        # 
        for i in range(len(frontier_outline_neighbors) - 1):
            sub_path = get_path_a_star(self, frontier_outline_neighbors[i], 
                frontier_outline_neighbors[i + 1], 
                rand=False, time_limit=.1, passthrough_units = True)
            sub_path.reverse()
            self.border_path += sub_path[1:-1]

    def get_guard_position(self, id):
        position_number = int((((id * 129) % ID_MAX) * (len(self.border_path)) ) / ID_MAX)
        if position_number == len(self.border_path):
            position_number = len(self.border_path) - 1
        print(position_number)
        if position_number < 0:
            return None
        return self.border_path[position_number]

    def get_wander_locations(self):
        self.wander_locations = []

        if len(self.gatherCity()) == 0:
            self.wander_locations.append((self.length/2, self.height/2))
            return
        
        # set wander locations to look like the following
        """
        . . . . . . . . . .
        . . . . . . . . . .
        . . . . . . . . . .
        . . . . . . . . w1 .
        . . . . . . . . . .
        . . . . . . . . h .
        . . . . . . w2 . . .
        . . . . . . . . h .
        . . . . . . . h . .
        . . . . . w3. . . h
        """
        mean_x_city = int(statistics.mean([c.x for c in self.gatherCity()]))
        mean_y_city = int(statistics.mean([c.y for c in self.gatherCity()]))
        print(f"citylocation: {mean_x_city}, {mean_y_city}")
        # Situation 1: kingdom extreme bottom right corner
        if self.KINGDOM_EXTREME[0] == self.length:
            x_extreme = min([c.x for c in self.gatherCity()])
            if self.KINGDOM_EXTREME[1] == self.height:
                # Above and to the right:
                y_extreme = min([c.y for c in self.gatherCity()])
                self.wander_locations.append((self.length - 6, y_extreme - WANDER_DIST))
                self.wander_locations.append((x_extreme - WANDER_DIST/2, y_extreme - WANDER_DIST/2))
                self.wander_locations.append((x_extreme - WANDER_DIST, self.height - 6))
            else:
                y_extreme = max([c.y for c in self.gatherCity()])
                # To the right and below
                self.wander_locations.append((self.length - 6, y_extreme + WANDER_DIST))
                self.wander_locations.append((x_extreme - WANDER_DIST/2, y_extreme + WANDER_DIST/2))
                self.wander_locations.append((x_extreme - WANDER_DIST, 5))
        else:
            x_extreme = max([c.x for c in self.gatherCity()])
            if self.KINGDOM_EXTREME[1] == self.height:
                # Above and to the right:
                y_extreme = min([c.y for c in self.gatherCity()])
                self.wander_locations.append((5, y_extreme - WANDER_DIST))
                self.wander_locations.append((x_extreme + WANDER_DIST/2, y_extreme - WANDER_DIST/2))
                self.wander_locations.append((x_extreme - WANDER_DIST, self.height - 6))
            else:
                y_extreme = max([c.y for c in self.gatherCity()])
                # To the right and below
                self.wander_locations.append((5, y_extreme + WANDER_DIST))
                self.wander_locations.append((x_extreme + WANDER_DIST/2, y_extreme + WANDER_DIST/2))
                self.wander_locations.append((x_extreme + WANDER_DIST, 5))

        # in this case, wander locations should be located torward the bottom of the map

    
    
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
        all_trees = [obj for obj in self.object_coord.values() if type(obj) == Tree and obj.reserved == False and obj.theoretical == False]

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
            if self.building_helper[(x,y)] >= 3:
                self.bld_spots[(3,3)].add((x,y))

            if self.building_helper[(x,y)] >= 2:
                self.bld_spots[(2,2)].add((x,y))

    def xy_to_hk(self, xy):
        hk = [xy[0], xy[1]]

        if self.KINGDOM_CORNER[0] == 1:
            hk[0] = self.length - xy[0]

        if self.KINGDOM_CORNER[1] == 1:
            hk[1] = self.height - xy[1]

        return (hk[0], hk[1])

    def hk_to_xy(self, hk):
        xy = [hk[0], hk[1]]

        if self.KINGDOM_CORNER[0] == 1:
            xy[0] = self.length - xy[0]

        if self.KINGDOM_CORNER[1] == 1:
            xy[1] = self.height - hk[1]

        return (xy[0], xy[1])

    def translate_buildings_down(self):
        new_bld_spots = {}
        new_bld_spots[(2,2)] = set()
        new_bld_spots[(3,3)] = set()
        for x in range(self.length):
            for y in range(self.height):
                spot = (x,y)
                for bld_size in self.bld_spots.keys():
                    if spot in self.bld_spots[bld_size]:
                        new_bld_spots[bld_size].add((spot[0] - (bld_size[0] - 1), spot[1] - (bld_size[1] - 1)))

        self.bld_spots = new_bld_spots

    def eliminate_bordering_buildings(self):
        # Stop vils from building too close to other buildings.
        copy_start = time.time()

        copy_end = time.time()

        print(f"Copy time: {copy_end - copy_start}")

        for x in range(self.length):
            for y in range(self.height):
                spot = (x,y)
                # eliminate building near other things
                for bld_size in self.bld_spots.keys():
                    if spot in self.bld_spots[bld_size]:
                        # Let us list all possible locations to check:
                        locations_to_check = []
                        for dy in range(bld_size[1]):
                            # all buildings are larger than dy
                            dx = 2
                            locations_to_check.append(
                                (spot[0] + bld_size[0] + dx, 
                                spot[1] + dy)
                            )
                            locations_to_check.append(
                                (spot[0] - dx, 
                                spot[1] + dy)
                            )
                        
                        for dx in range(bld_size[0]):
                            # all buildings are larger than dy
                            dy = 2
                            locations_to_check.append(
                                (spot[0] + dx, 
                                spot[1] + bld_size[1] + dy)
                            )
                            locations_to_check.append(
                                (spot[0] + dx, 
                                spot[1] - dy)
                            )
                        # Then add the corners:
                        locations_to_check.append((spot[0] - 1, spot[1] - 1))
                        locations_to_check.append((spot[0] - 1, spot[1] + bld_size[1] + 1))
                        locations_to_check.append((spot[0] + bld_size[0] + 1, spot[1] - 1))
                        locations_to_check.append((spot[0] + bld_size[0] + 1, spot[1] + bld_size[1] + 1))

                        for loc in locations_to_check:
                            if issubclass(type(self.get_coord(loc)), Building):
                                self.bld_spots[bld_size].remove(spot)
                                break

    def post_processing_steps(self):
        self.translate_buildings_down()
        self.eliminate_bordering_buildings()

        avg_empire_location = self.gatherEmpire() + self.gatherCity()
        x_mean = statistics.mean([obj.x for obj in avg_empire_location])
        y_mean = statistics.mean([obj.y for obj in avg_empire_location])

        self.KINGDOM_CORNER = (int((x_mean / (self.length / 2))), int(y_mean / (self.length / 2)) )
        self.KINGDOM_XMIN = int(self.KINGDOM_CORNER[0] * (self.length / 2))
        self.KINGDOM_XMAX = int(self.KINGDOM_XMIN + (self.length / 2))
        self.KINGDOM_YMIN = int(self.KINGDOM_CORNER[1] * (self.length / 2))
        self.KINGDOM_YMAX = int(self.KINGDOM_YMIN + (self.length / 2))


        self.KINGDOM_EXTREME = (self.KINGDOM_CORNER[0] * self.length, self.KINGDOM_CORNER[1] * self.height)
        
        self.make_islands()
        self.make_pois()
        self.build_frontier()
        # Force buildings to be spaced out from one another.


        self.get_wander_locations()

    def is_in_kingdom(self, x,y):
        return ((x < self.KINGDOM_XMAX and x >= self.KINGDOM_XMIN) 
            and (y < self.KINGDOM_YMAX and y >= self.KINGDOM_YMIN))
            
    def build_island(self, x, y, island_id = 0):
        # If the land is already visited
        # or there is no land or the
        # coordinates gone out of matrix
        # break function as there
        # will be no islands
        stack = [(x,y)]
        self.island_length[island_id] = 0

        while stack:
            (xn,yn) = stack.pop()

            obj = self.get_coord((xn,yn))
            if obj is not None:
                if type(obj) != Unknown and type(obj) != Unoccupied:
                    obj.island_ids.add(island_id) 
                    self.island_length[island_id] += 1
            
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
        self.island_length = {}
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

    # See if this villager can build
    def processVillager(self, vil):
        vil.vil_index = self.villager_index
        self.villager_index+=1
        for bld_size in self.bld_spots.keys():
            if self.villager_can_build[bld_size]:
                next
            for dx in range(1, bld_size[0] + 1):
                if (vil.x - (dx - 1), vil.y + 1) in self.bld_spots[bld_size]:
                    vil.build_loc[bld_size] = (vil.x - (dx - 1), vil.y + 1)
                    self.villager_can_build[bld_size] = True

                if (vil.x - (dx - 1), vil.y - bld_size[1]) in self.bld_spots[bld_size]:
                    vil.build_loc[bld_size] = (vil.x - (dx - 1), vil.y - bld_size[1])
                    self.villager_can_build[bld_size] = True

            for dy in range(1, bld_size[1] + 1):
                if (vil.x + 1, vil.y - (dy - 1)) in self.bld_spots[bld_size]:
                    vil.build_loc[bld_size] = (vil.x + 1, vil.y - (dy - 1))
                    self.villager_can_build[bld_size] = True

                if (vil.x - bld_size[0], vil.y - (dy - 1)) in self.bld_spots[bld_size]:
                    vil.build_loc[bld_size] = (vil.x - bld_size[0], vil.y - (dy - 1))
                    self.villager_can_build[bld_size] = True


    def gatherEmpire(self):
        if self.empire is None:
            all_units = [obj for obj in self.object_coord.values() if issubclass(type(obj), Unit)]
            self.empire = [u for u in all_units if u.team == self.team_id]
            self.empire = sorted(self.empire, key=lambda obj: obj.id, reverse=True)
            for gi in range(len(self.empire)):
                # useful for pairing units.
                # we can cluster units that are nearby each other, id-wise.
                self.empire[gi].citizen_no = gi
                if type(self.empire[gi]) == Villager:
                    self.processVillager(self.empire[gi])

        return self.empire

    def gatherEnemyEmpire(self):
        if self.enemyEmpire is None:
            all_units = [obj for obj in self.object_coord.values() if issubclass(type(obj), Unit)]
            self.enemyEmpire = [u for u in all_units if u.team != self.team_id]
        
        return self.enemyEmpire

    def gatherEnemyCity(self):
        if self.enemyCity is None:
            all_buildings = [obj for obj in self.object_coord.values() if issubclass(type(obj), Building)]
            self.enemyCity = [b for b in all_buildings if b.team != self.team_id]
        return self.enemyCity

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


                if issubclass(type(obj), Building):
                    color = teamcols[obj.team]
                    print_string += color + obj.rep() + ' '

                if (x,y) in self.pois:
                    print_string = print_string[:-1] + COL_GOLD + 'X'

                if (x,y) in self.wander_locations:
                    print_string = print_string[:-2] + COL_GOLD + 'WL'

                if (x,y) in self.ecl:
                    #print(ecl)
                    print_string = print_string[:-2] + COL_GOLD + 'EC'

                #if (x,y) in self.frontier_points:
                #    #print(ecl)
                #    print_string = print_string[:-2] + COL_GOLD + 'FP'

                if (x,y) in self.border_path:
                    print_string = print_string[:-1] + COL_GOLD + 'P'
                """
                if (x,y) in self.bld_spots[(3,3)]:
                    print_string = print_string[:-1] + '&'
                elif (x,y) in self.bld_spots[(2,2)]:
                    print_string = print_string[:-1] + '^'

                for v in self.gatherEmpire():
                    if type(v)==Villager:
                        if v.build_loc.get((3,3)) is not None:
                            if (x,y) == v.build_loc.get((3,3)):
                                print_string = print_string[:-1] + 'B'
                """



            print_string += (NORM + '\n')
        print(print_string)

TURN = 0

def run(world_state, players, team_idx):
    global TURN
    TURN += 1
    if TURN % 10 == 0:
        PROFILER.on()
    else:
        PROFILER.off()
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
    random.shuffle(empire)

    # Leave .1 sec for buffer
    # Only give the first n players 
    # Leave .05 seconds for buildings
    unit_commands = []
    for u in empire:
        if time.time() - start_time - PROFILER.time_spent < .75:
            m = u.execute(cws)
            unit_commands.append(m)
        elif time.time() - start_time - PROFILER.time_spent < .85:
            print("running out of time...")
            m = u.execute_basic(cws)
            unit_commands.append(m)
        else:
            break

    building_commands = []
    for b in cws.gatherCity():
        if time.time() - start_time -  PROFILER.time_spent < .95:
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
    print(players[team_idx])
    print(f"Population: {len(cws.gatherEmpire())} / {cws.get_housing()}")

    if len(cws.reserved_trees) == 7:
        for i in range(7):
            print(cws.reserved_trees[i].hp)

    reset_number_system()

    PROFILER.profilePrint()
    PROFILER.profileReset()

    return (unit_commands + building_commands)
    # Determine what the foliage is for unexplored tiles.
