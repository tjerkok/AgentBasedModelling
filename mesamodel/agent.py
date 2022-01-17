from mesa import Agent
import numpy as np
import random
import networkx as nx

class Person(Agent):
    def __init__(self, unique_id, pos, model, objectives, moore=False, speed=1):
        super().__init__(unique_id, model)
        
        self.pos = pos
        self.objectives = objectives
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
        self.route = []
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
        self.steps_instore += 1
        self.route.append(self.pos)
        next_move = self.find_route()
        print(f"planned move: {next_move}")
        while self.model.grid.out_of_bounds(next_move) or not self.model.grid.is_cell_empty(next_move):
            print("illegal move")
            #next_move = self.find_route()
            if random.random() < 0.5:
                next_move = self.pos
                print("illegal move planned, wait one time step")
                break
            else:
                next_move = self.random_move()
                print("try random step")
        # Make move
        self.model.grid.move_agent(self, next_move)
        if self.pos == self.current_objective[1]:
            self.reached_objective()
            
    
    def reached_objective(self):
        if self.current_objective[0] == "exit":
            print(f"{self} is done shopping, removing...")
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
        else:
            print(f"{self} got {self.current_objective[0]}!\n\n")
            self.basket.append(self.current_objective[0])
            self.next_objective()
            print(f"getting next objective: {self.current_objective}")

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
        obstacles = [obstacle.pos for obstacle in self.model.obstacles]
        # for move in possible_moves:
        #     if np.abs(move[0] - self.current_objective[1][0]) < np.abs(self.pos[0] - self.current_objective[1][0]) and move not in obstacles:
        #         return move

        # Uncomment according to chosen move
        move = self.astar_move()
        #move = self.random.choice([self.astar_move(),self.astar_move(),self.random_move()])
        #move = self.random_move()
        return move


    def dist(self, a, b):
        (x1, y1) = a
        (x2, y2) = b
        return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5


    def astar_move(self):
        route = nx.astar_path(self.model.graph, self.pos, self.current_objective[1], heuristic=self.dist)
        return route[1]


    def random_move(self):
        x, y = self.pos
        move = random.choice([(x+1, y), (x-1, y), (x, y+1), (x, y-1)])
        return move

    def __repr__(self):
        return f"Person {self.unique_id} at {self.pos}"
    

class Obstacle(Agent):
    def __init__(self, next_id, model, pos, obstacle_type):
        super().__init__(next_id, model)
        self.obstacle_type = obstacle_type
        self.pos = pos
        
    def __repr__(self):
        return f"{self.obstacle_type} {self.unique_id} at {self.pos}"