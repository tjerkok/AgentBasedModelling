from xml.etree.ElementInclude import include
from mesa import Agent
import numpy as np
import random
import networkx as nx

class Person(Agent):
    def __init__(self, unique_id, pos, model, objectives,familiar, moore=False, speed=1, vision=1):
        super().__init__(unique_id, model)
        self.person_id = len(self.model.persons) + 1
        self.pos = pos
        self.objectives = objectives
        self.familiar = familiar
        # print(f"Originally Person {self.unique_id} has objs {self.objectives}")
        self.objectives_inc_coord = []
        self.get_objectives_coord()
        self.sort_objectives()
        # print(f"{self} has objs {self.new_objectives}")
        self.next_objective()
        self.model = model
        self.speed = speed
        self.moore = moore
        self.basket = []
        self.route = [self.pos]
        self.steps_instore = 0
        self.int_rate = 0
        self.people_bumped_into = []
        self.tot_cont = 0
        self.vision = vision
        self.n_switches = 0


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
        self.model.blocked_moves.pop(self, False)
        # print(f"turn for {self} at {self.pos}")
        next_moves = self.find_route()
        # print(f"planned move: {next_moves}")
        legal_moves = self.check_move(next_moves, astar=True)
        while not legal_moves:
            # print("illegal move")
            if random.random() < 0.5:
                next_moves = self.random_move()
                legal_moves = self.check_move([next_moves[0]])
                if legal_moves:
                    legal_moves = legal_moves
                # print(f"doing none one random move: {legal_moves}")
            else:
                legal_moves = []
                # print("waiting one time step and see if someone wants to switch")
                break

        # Make move
        if not legal_moves:
            self.model.standing_still += 1
        for move in legal_moves:
            if move != self.pos:
                self.check_interactions(move)
                self.model.grid.move_agent(self, move)
        # if self.pos == self.current_objective[1]:
        #     self.reached_objective()
        if self.familiar < 1.0:
            self.familiar = round(self.familiar + 0.01, 2)
        if self.pos == self.current_objective[1]:
            if self.reached_objective():
                # print("agent is removed")
                return
        # if self.pos != self.route[-1]:
        #     print(f"moved to {self.pos}")
        self.steps_instore += 1
        self.route.append(self.pos)

    
    def reached_objective(self):
        """
        Returns True if agent is at exit, else False
        """
        if self.current_objective[0] == "exit":
            if self.model.print_bool:
                print(f"{self} is done shopping, removing...")
            self.model.schedule.remove(self)
            self.model.grid.remove_agent(self)
            self.model.n_done += 1
            self.model.n_interactions.append(self.int_rate)
            self.model.persons_instore.remove(self)
            return True

        else:
            # print(f"{self} got {self.current_objective[0]}!")
            self.basket.append(self.current_objective[0])
            self.next_objective()
            # print(f"getting next objective: {self.current_objective}")
            return False

    def check_interactions(self,move):
        for agent in self.model.grid.get_neighbors(move, moore=self.moore, radius=1, include_center=False):
            if isinstance(agent,Person) == True and agent != self:
                self.tot_cont =+ 1
                self.model.interactions_per_step[-1] += 1
                if agent.unique_id not in self.people_bumped_into:
                    self.people_bumped_into.append(agent.unique_id)
                    self.int_rate = int(len(self.people_bumped_into))

    def check_move(self, moves, astar=False):
        legal = []
        for move in moves:
            if self.model.grid.out_of_bounds(move):
                # print("out of bounds move")
                return legal
            else:
                blocking_person = [agent for agent in self.model.grid.get_cell_list_contents(move) if isinstance(agent, Person)]
                dest_obstacles = [agent for agent in self.model.grid.get_cell_list_contents(move) if isinstance(agent, Obstacle)]
                if blocking_person or dest_obstacles:
                    if blocking_person:
                        legal = self.switch_places_check(blocking_person, move, legal, astar)    
                    return legal
                else: 
                    legal.append(move)
        return legal

    def switch_places_check(self, blocking_person, move, legal, astar):
        blocking_person = blocking_person[0]
        if blocking_person in self.model.blocked_moves.keys():
            try:
                if self.model.blocked_moves[blocking_person] == legal[-1]:
                    # print(f"Switching {self} at {legal[-1]} with {blocking_person} at {move}")
                    self.model.grid.move_agent(blocking_person, legal[-1])
                    legal.append(move)
                    self.n_switches += 1
            except IndexError:
                if self.model.blocked_moves[blocking_person] == self.pos:
                    # print(f"Switching {self} at {self.pos} with {blocking_person} at {move}")
                    self.model.grid.move_agent(blocking_person, self.pos)
                    legal = [move]
                    self.n_switches += 1                    
            self.model.blocked_moves.pop(blocking_person, False)
        elif astar:
            self.model.blocked_moves[self] = move
        return legal

    def find_route(self):
        # TODO: True is voor eigen positie meenemen, willen we dat?
        # possible_moves = self.model.grid.get_neighborhood(self.pos, self.moore, True, self.speed) 
        # print(f"{self} at {self.pos} has current obj {self.current_objective[0]} at {self.current_objective[1]}")
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
            # print(f"not familiar, random moves")
            moves = self.random_move()
        return moves


    def dist(self, a, b):
        (x1, y1) = a
        (x2, y2) = b
        return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5


    def astar_move(self):
        self.model.calculate_weights(self.pos, self.vision)
        route = nx.astar_path(self.model.graph, self.pos, self.current_objective[1], heuristic=self.dist, weight="weight")
        return route[1:self.speed+1]


    def random_move(self):
        x, y = self.pos
        moves = []
        for i in range(self.speed):
            moves.append(random.choice([(x+1, y), (x-1, y), (x, y+1), (x, y-1)]))
            x, y = moves[-1]
        return moves

    def __repr__(self):
        return f"Person {self.person_id}" # at {self.pos}"
    

class Obstacle(Agent):
    def __init__(self, next_id, model, pos, obstacle_type):
        super().__init__(next_id, model)
        self.obstacle_type = obstacle_type
        self.pos = pos
        
    def __repr__(self):
        return f"Obstacle {self.obstacle_type} {self.unique_id} at {self.pos}"

    def step(self):
        pass


class Objective(Agent):
    def __init__(self, next_id, model, pos, objective_type):
        super().__init__(next_id, model)
        self.objective_type = objective_type
        self.pos = pos
        
    def __repr__(self):
        return f"{self.objective_type} {self.unique_id} at {self.pos}"

    def step(self):
        pass