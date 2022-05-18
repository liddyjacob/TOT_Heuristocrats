from copy import deepcopy
from ai.heuristocrats.constants import *

FOLIAGE_STATE = None

def initialize_foliage_state():
    global FOLIAGE_STATE

    if FOLIAGE_STATE is not None:
        return

    FOLIAGE_STATE = []
    # first, we begin by generating NONEs for the whole world.
    for x in range(HWSIZE):
        xl = []
        for y in range(HWSIZE):
            xl.append(False)
        FOLIAGE_STATE.append(xl)

def set_all_foliage(coords, mapdata):
    global FOLIAGE_STATE

    (base_x, base_y) = coords[0]

    # never change once foliage is set
    if (FOLIAGE_STATE[base_x][base_y] != False):
        return

    for (x,y) in coords:
        md = mapdata[x][y]

        if md is None:
            FOLIAGE_STATE[base_x][base_y] = None
            return

        if md != 'u':
            mdt = md['type']
            if mdt == 't' or mdt == 'g':
                FOLIAGE_STATE[base_x][base_y] = md
            else: # for units and infantry with nothing below them
                FOLIAGE_STATE[base_x][base_y] = None


def  redefine_if_unknown(all_coords, mapdata):
    (base_x, base_y) = all_coords[0]
    fstate = FOLIAGE_STATE[base_x][base_y]

    # no foliage state to use.
    if fstate == False:
        return mapdata

    for (x,y) in all_coords:
        mapdata[x][y]

        if mapdata[x][y] == 'u':
            mapdata[x][y] = FOLIAGE_STATE[base_x][base_y]

    return mapdata



TEST_DATA = [['u','u','u',{'type':'t'}, None, {'type':'v', 'team':1}],
             ['u','u','u',{'type':'g'}, None, {'type':'t'}],
             ['u','u',{'type':'t'},'u', {'type':'g'}, 'u'],
             ['u','u','u', 'u', 'u', {'type':'t'}],
             ['u','u','u', 'u', 'u', 'u'],
             ['u','u','u', 'u', 'u', 'u']
    ]

TEST_DATA_TWO = [['u','u','u',{'type':'t'}, None, {'type':'v', 'team':1}],
             ['u','u','u',None, None, {'type':'t'}],
             ['u','u',{'type':'t'},'u', None, 'u'],
             ['u','u','u', 'u', 'u', {'type':'t'}],
             ['u','u','u', 'u', 'u', 'u'],
             ['u','u','u', 'u', 'u', 'u']
    ]

def get_reflected_coords(x,y):
    return [(x,y), (WSIZE - x - 1, y), (WSIZE - x - 1, WSIZE - y - 1), (x, WSIZE - y - 1)]

def reflect(mapdata):
    reflected_data = deepcopy(mapdata)
    for x in range(HWSIZE):
        for y in range(HWSIZE):
            all_coords = get_reflected_coords(x,y)
            set_all_foliage(all_coords, mapdata)

            reflected_data = redefine_if_unknown(all_coords, reflected_data)

    return reflected_data
            

initialize_foliage_state()

