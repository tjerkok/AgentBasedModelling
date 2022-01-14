from mesa import Agent
import numpy as np
import random
import networkx as nx

class Person(Agent):
    def __init__(self, unique_id, pos, model, objectives, moore=False, speed=1):
        super().__init__(unique_id, model)
        
        self.pos = pos
        self.objectives = objectives
        print(f"Person {self.unique_id} has objs {self.objectives}")
        self.next_objective()
        self.model = model
        self.speed = speed
        self.moore = moore
        self.basket = []
        self.route = []

    def next_objective(self):
        next_objective = self.objectives.pop(0)
        self.current_objective = (next_objective, random.choice(self.model.objectives[next_objective]))

    def step(self):
        # Find next step
        self.route.append(self.pos)
        next_move = self.find_route()
        print(f"planned move: {next_move}")
        while self.model.grid.out_of_bounds(next_move) or not self.model.grid.is_cell_empty(next_move):
            print("illegal move, try again")
            next_move = self.find_route()
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