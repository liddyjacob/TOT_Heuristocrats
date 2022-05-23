from copy import deepcopy
from ai.heuristocrats.constants import * 
from ai.shitutils import coord_to_int

def generate_exploration_map(mapdata):
    exploration_map = [[0 for r in row] for row in mapdata]
    for x in range(WSIZE):
        for y in range(WSIZE):
            if mapdata[x][y] is None:
                exploration_map[x][y] = 1

            if mapdata[x][y] == 'u':
                exploration_map[x][y] = 1

    return exploration_map


# Python3 program for the above approach
 
# DFS Traversal to find the count of
# island surrounded by water
def dfs(matrix, visited, x, y, n, m, island_id = 0):
    
    # If the land is already visited
    # or there is no land or the
    # coordinates gone out of matrix
    # break function as there
    # will be no islands
    stack = [(x,y)]

    while stack:
        (xn,yn) = stack.pop()
        if (xn < 0 or yn < 0 or
            xn >= n or yn >= m or
            visited[xn][yn] != 0 or
            matrix[xn][yn] == 0):
            continue
        
        visited[xn][yn] = island_id
        stack.append((xn, yn + 1))
        stack.append((xn, yn - 1))
        stack.append((xn - 1, yn))
        stack.append((xn + 1, yn))
        stack.append((xn + 1, yn + 1))
        stack.append((xn + 1, yn - 1))
        stack.append((xn - 1, yn + 1))
        stack.append((xn - 1, yn - 1))

 
# Function that counts the closed island
def getClosedIslands(matrix, n, m):
     
    # Create boolean 2D visited matrix
    # to keep track of visited cell
  
    # Initially all elements are
    # unvisited.
    visited = [[0 for i in range(m)]
                      for j in range(n)]
 
    # To stores number of closed islands
    result = 0
 
    for i in range(n):
        for j in range(m):
             
            # If the land not visited
            # then there will be atleast
            # one closed island
            if (visited[i][j] == 0 and
                 matrix[i][j] == 1):
                result += 1
                
                # Mark all lands associated
                # with island visited.
                dfs(matrix, visited, i, j, n, m, island_id = result)
 
    # Return the final count
    return visited
 
#  Driver Code
 
# Given size of Matrix
 
# This code is contributed by rag2127


def printAsIs(matrix):
    for x in range(len(matrix)):
        for y in range(len(matrix[x])):
            print(matrix[x][y], end='')
            print(' ', end='')
        print('')


from stats import *
# render bs
TREE = '\033[32m'
GOLD = '\033[33m'
NORM = '\033[37m'
# teamcolors
teamcols = {
    -2: NORM,
    0: "\033[31m", # RED
    1: "\033[34m", # BLUE
    2: "\033[35m", # PURPLE
    3: "\033[36m", # CYAN
}


def cust_render(world_state):
    # render the world
    for y in range(len(world_state)):
        for x in range(len(world_state[y])):
            if world_state[x][y] is not None:
                if(world_state[x][y] == "u"):
                    print(" ", end="")
                elif type(world_state[x][y]) == str:
                    print(world_state[x][y], end="")
                elif(world_state[x][y]["type"] == "t"):
                    print(TREE + world_state[x][y]["type"], end="")
                elif(world_state[x][y]["type"] == "g"):
                    print(GOLD + world_state[x][y]["type"], end="")
                elif(is_building(world_state[x][y]["type"]) and world_state[x][y]["constructed"]):
                    print(teamcols[world_state[x][y]["team"]] + world_state[x][y]["type"].upper(), end="")
                else:
                    print(teamcols[world_state[x][y]["team"]] + world_state[x][y]["type"], end="")
            else:
                print(NORM + " ", end="")
            #print('  ', end='')
        print(NORM)
