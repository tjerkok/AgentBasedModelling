from mesa import Agent

class Person(Agent):
    def __init__(self, unique_id, pos, model, objectives, moore=False, speed=1):
        super().__init__(unique_id, model)
        
        self.pos = pos
        self.objectives = objectives
        self.current_objective = self.objectives.pop()
        #?
        self.model = model
        self.speed = speed
        self.moore = moore
    
    def step(self):
        # TODO: True is voor eigen positie meenemen, willen we dat?
        # TODO: Check if move is valid
        possibel_moves = self.model.grid.get_neighborhood(self.pos, self.moore, True, self.speed) 
        
        # TODO: Choose move
        next_move = self.random.choice(possibel_moves)
        
        self.model.grid.move_agent(self, next_move)
        
        # TODO: If current is objective, get next objective
        # self.current_objective = self.objective.pop()
        
    def find_route(self, objective):
        
        raise NotImplementedError
        

class Obstacle(Agent):
    def __init__(self, next_id, model, pos, obstacle_type):
        super().__init__(next_id, model)
        self.obstacle_type = obstacle_type
        self.pos = pos
        