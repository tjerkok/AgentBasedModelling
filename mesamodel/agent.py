from mesa import Agent
import numpy as np

class Person(Agent):
    def __init__(self, unique_id, pos, model, objectives, moore=False, speed=1):
        super().__init__(unique_id, model)
        
        self.pos = pos
        self.objectives = objectives
        self.current_objective = self.objectives.pop()
        self.model = model
        # Use?
        # self.speed = speed
        # self.moore = moore
    
    def step(self):
        # Find next step
        next_move = self.find_route()
        
        # Make move
        self.model.grid.move_agent(self, next_move)
        
    def find_route(self):
        # TODO: True is voor eigen positie meenemen, willen we dat?
        possibel_moves = self.model.grid.get_neighborhood(self.pos, self.moore, True, self.speed)
        
        # Check if at objective
        if self.current_objective in possibel_moves:
            self.current_objective = self.objectives.pop()
        
        # TODO: Better algorithm
        # Check if he gets closer and not in obstacles, otherwise go up
        obstacles = [x.pos for x in self.model.obstacles]
        for move in possibel_moves:
            if np.abs(move[0] - self.current_objective[0]) < np.abs(self.pos[0] - self.current_objective[0]) and move not in obstacles:
                return move
        x, y = self.pos
        return (x + 1, y)
    

class Obstacle(Agent):
    def __init__(self, next_id, model, pos, obstacle_type):
        super().__init__(next_id, model)
        self.obstacle_type = obstacle_type
        self.pos = pos
        