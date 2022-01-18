from mesa import Agent
import numpy as np
import random
import networkx as nx

class Person(Agent):
    def __init__(self, unique_id, pos, model, objectives,familiar, moore=False, speed=1):
        super().__init__(unique_id, model)
        
        self.pos = pos
        self.objectives = objectives
        self.familiar = familiar
        print(f"Originally Person {self.unique_id} has objs {self.objectives}")
        self.objectives_inc_coord = []
        self.get_objectives_coord()
        self.sort_objectives()
        print(f"After sorting person {self.unique_id} has objs {self.new_objectives}")
        self.next_objective()
        self.model = model
        self.speed = speed
        self.moore = moore
        self.basket = []
        self.route = [self.pos]
        self.steps_instore = 0


    def get_objectives_coord(self):
        for next_objective in self.objectives:
            self.objectives_inc_coord.append((next_objective, random.choice(self.model.objectives[next_objective])))


    def sort_objectives(self):
        self.temp_object = []
        for obj in self.objectives_inc_coord[:-1]:  # get all objects except for exit
            self.temp_object.append((obj[0], obj[1], len(nx.astar_path(self.model.graph, self.pos, obj[1], heuristic=self.dist))-1))

        x = lambda index: index[2]
        self.temp_object.sort(key=x)
        self.new_objectives = []
        for obj in self.temp_object:
            self.new_objectives.append((obj[0], obj[1]))
        self.new_objectives.append(('exit', self.model.objectives['exit'][0]))  # [0] because of [(1,9)], list being returned


    def next_objective(self):
        #next_objective = self.objectives.pop(0)
        #self.current_objective = (next_objective, random.choice(self.model.objectives[next_objective]))
        self.current_objective = self.new_objectives.pop(0)  # when sorting list

    def step(self):
        # Find next step
        next_moves = self.find_route()
        print(f"planned move: {next_moves}")
        legal_moves = self.check_move(next_moves)
        while not legal_moves:
            print("illegal move")
            #next_move = self.find_route()
            if random.random() < 0.5:
                legal_moves = [self.pos]
                print("wait one time step")
                break
            else:
                # TODO: only one step or self.speed steps?
                next_moves = self.random_move()
                legal_moves = self.check_move(next_moves)
                print(f"try random step(s): {legal_moves}")
        if len(legal_moves) != len(next_moves):
            print(f"not all moves are legal, not using full speed, new pos: {legal_moves[-1]}")
            next_moves = legal_moves
        for move in next_moves:
            self.model.grid.move_agent(self, move)
        
        if self.pos == self.current_objective[1]:
            if self.reached_objective():
                print("agent is removed")
                return

        # Make move
        for move in next_moves:
            self.model.grid.move_agent(self, move)
        if self.pos == self.current_objective[1]:
            self.reached_objective()
        if self.familiar < 1.0:
            self.familiar = round(self.familiar + 0.01, 2)
        self.steps_instore += 1
        self.route.append(self.pos)

    
    def reached_objective(self):
        """
        Returns True if agent is at exit, else False
        """
        if self.current_objective[0] == "exit":
            print(f"{self} is done shopping, removing...")
            self.model.schedule.remove(self)
            self.model.grid.remove_agent(self)
            return True

        else:
            print(f"{self} got {self.current_objective[0]}!\n")
            self.basket.append(self.current_objective[0])
            self.next_objective()
            print(f"getting next objective: {self.current_objective}")
            return False

    def check_move(self, moves):
        legal = []
        for move in moves:
            if self.model.grid.out_of_bounds(move) or not self.model.grid.is_cell_empty(move):
                return legal
            else: 
                legal.append(move)
        return legal

    def find_route(self):
        # TODO: True is voor eigen positie meenemen, willen we dat?
        # possible_moves = self.model.grid.get_neighborhood(self.pos, self.moore, True, self.speed) 
        print(f"{self} has current obj {self.current_objective[0]} at {self.current_objective[1]}")
        
        # implementing directed route with A*
        # # Check if at objective
        # if self.current_objective[1] in possible_moves:
        #     self.current_objective = self.objectives.pop() # not sure wat we hier willen doen nu

        # TODO: Better algorithm
        # Check if he gets closer and not in obstacles, otherwise go up
        # obstacles = [obstacle.pos for obstacle in self.model.obstacles]
        # for move in possible_moves:
        #     if np.abs(move[0] - self.current_objective[1][0]) < np.abs(self.pos[0] - self.current_objective[1][0]) and move not in obstacles:
        #         return move

        # If the agent is familiar, it will make a A* move, if it isnt it will take a random step
        if np.random.uniform(0,1) <= self.familiar: 
            moves = self.astar_move()
        else:
            print(f"not familiar, random moves")
            moves = self.random_move()
        return moves


    def dist(self, a, b):
        (x1, y1) = a
        (x2, y2) = b
        return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5


    def astar_move(self):
        route = nx.astar_path(self.model.graph, self.pos, self.current_objective[1], heuristic=self.dist)
        return route[1:self.speed+1]


    def random_move(self):
        x, y = self.pos
        moves = []
        for i in range(self.speed):
            moves.append(random.choice([(x+1, y), (x-1, y), (x, y+1), (x, y-1)]))
            x, y = moves[-1]
        return moves

    def __repr__(self):
        return f"Person {self.unique_id} at {self.pos}"
    

class Obstacle(Agent):
    def __init__(self, next_id, model, pos, obstacle_type):
        super().__init__(next_id, model)
        self.obstacle_type = obstacle_type
        self.pos = pos
        
    def __repr__(self):
        return f"{self.obstacle_type} {self.unique_id} at {self.pos}"