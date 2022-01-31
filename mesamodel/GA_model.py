from mesa import Model
from mesa.datacollection import DataCollector
from mesa.space import SingleGrid, MultiGrid # TODO: do we need multi?
from mesa.time import RandomActivation
from csv import writer, DictWriter
import networkx as nx
import numpy as np
import json
import random
from pkg_resources import EntryPoint
import regex as re
import dill as pkl # weirde aangepaste pickle die pandas dataframe wel oké vindt
import copy
import os

from agent import Person, Obstacle, Objective

class GroceryModel(Model):
    def __init__(self, avg_arrival, speed=7, speed_prob=1.0, log=False, print_bool=False):
        # attributes
        super().__init__()
#         self.config = config
        self.height = 65
        self.width = 65
        self.n_persons = int(10000)
        self.n_items = int(1)
        self.grid_layout = "grids/real_less_65x35.txt"
        self.avg_arrival = avg_arrival
        self.n_steps = int(5)
        
        # self.speed_dist = config["speed_dist"]
        self.speed1 = 1
        self.speed2 = int(round(speed))
        self.speed2_prob = speed_prob
        self.speed1_prob = 1 - self.speed2_prob
        self.speed_dist = [[self.speed1, self.speed2], [self.speed1_prob, self.speed2_prob]]
        
        # self.familiar_dist = config["familiar_dist"]
        self.familiar1 = 1
        self.familiar2 = 0.6
        self.familiar2_prob = speed_prob
        self.familiar1_prob = 1 - self.familiar2_prob
        self.familiar_dist = [[self.familiar1, self.familiar2], [self.familiar1_prob, self.familiar2_prob]]

        # self.vision_dist = config["vision_dist"]
        self.vision1 = int(3)
        self.vision2 = int(6)
        self.vision2_prob = 0.5
        self.vision1_prob = 1 - self.vision2_prob
        self.vision_dist = [[self.vision1, self.vision2], [self.vision1_prob, self.vision2_prob]]

        self.grid_stepsize = 0.5
        self.n_objectives = int(8)
        self.list_subgrids = [[[4, 10], [10, 10], [10, 0], [4, 0]], [[0, 10], [3, 10], [3, 5], [0, 5]]]
        self.obstacles = []
        self.objectives_dict = {}
        self.objectives = []
        self.persons = []
        self.persons_instore = []
        self.n_done = 0
        self.done = []
        self.arrival_times = [0]
        self.current_step = 0
        self.entry_pos = []
        self.exit_pos = []
        self.n_interactions = []    # interactions per person who is done shopping
        self.interactions_per_step = [0]
        self.blocked_moves = {}
        self.standing_still = 0
        self.waiting_to_enter = []
        self.graph = nx.grid_2d_graph(self.height, self.width)
        self.log_bool = log
        self.print_bool = print_bool
        self.shop_open = True
        self.already_done = False

        # scheduling Poisson distribution times of persons arriving
        for i in range(self.n_persons - 1):
            time = int(round(random.expovariate(1/self.avg_arrival)))
            self.arrival_times.append(self.arrival_times[-1] + time) 

        # if self.print_bool:
        #     print(f"arrival times (length {len(self.arrival_times)}): {self.arrival_times}")
        # schedule
        self.schedule = RandomActivation(self)

        # grid and datacollection
        self.grid = MultiGrid(self.width, self.height, torus=False)
        self.datacollector = DataCollector({ #TODO
            "waiting_to_enter": lambda m: len(self.waiting_to_enter),
            "standing_still": lambda m: self.standing_still,
            "n_persons": lambda m: len([agent for agent in self.schedule.agents if isinstance(agent, Person)]),
            "n_done": lambda m: self.n_done,
            "persons": lambda m: [agent for agent in self.schedule.agents if isinstance(agent, Person)], # self.schedule.get_agent_count(),
            "person_locs": lambda m: [person.pos for person in self.persons],
            "mean_steps ": lambda m: [person.steps_instore for person in self.persons],
            "speed": lambda m: [person.speed for person in self.persons],
            "familiar": lambda m: [person.familiar for person in self.persons],
            "densities": lambda m: [self.calculate_density(sub_grid) for sub_grid in self.list_subgrids],
            "mean_interactions_done": lambda m: self.count_mean_interactions(),
            "interactions": lambda m: self.interactions_per_step[-1],
            "total_switches": lambda m: sum([person.n_switches for person in self.persons]),
            "mean_steps_done": lambda m: self.count_mean_steps(),
            "mean_distance_done": lambda m: self.count_mean_distance()
        })

        # placing obstacles, entry and exit
        self.read_grid()

        # datacollector requirements
        self.running = True
        # self.datacollector.collect(self) # doing first collection in step()

    def count_mean_interactions(self):
        interactions = [person.int_rate for person in self.done]
        if interactions:
            return np.mean(interactions)
        else:
            return 0

    def count_mean_steps(self):
        steps = [person.steps_instore for person in self.done]
        if steps:
            return np.mean(steps)
        else:
            return 0
        
    def count_mean_distance(self):
        distances = [person.distance for person in self.done]
        if distances:
            return np.mean(distances)
        else:
            return 0

    def read_grid(self):
        """
        Create grid from grid_layout.txt
        """
        gridsize = re.search(r"_\d+", self.grid_layout)[0]
        
        objective_positions = []
        with open(self.grid_layout, 'r') as f:
            lines = f.readlines()
            for line in lines[1:]:
                line = line.strip("\n").split(",")
                type = line[0]
                startpos = (int(line[1]), int(line[2]))
                orientation = line[3]
                length = int(line[4])
                for i in range(length):
                    if orientation == "h":
                        pos = (startpos[0]+i, startpos[1])
                    elif orientation == "v":
                        pos = (startpos[0], startpos[1]+i)
                    if type == "entry":
                        self.entry_pos.append(pos)
                    elif type == "exit":
                        self.exit_pos.append(pos)
                    
                    if type == "wall":
                        obstacle = Obstacle(self.next_id(), pos, self, obstacle_type=type)
                        self.obstacles.append(obstacle)
                        self.grid.place_agent(obstacle, pos)
                        self.schedule.add(obstacle)
                        for n in list(self.graph.neighbors(pos)):
                            self.graph.remove_edge(pos, n)
                    else:
                        objective = Objective(self.next_id(), pos, self, objective_type=type)
                        self.grid.place_agent(objective, pos)
                        self.schedule.add(objective)
                        # self.graph.nodes[pos]["type"] = "objective"
                        if type not in self.objectives_dict.keys():
                            self.objectives_dict[type] = []
                        self.objectives_dict[type].append(pos)
                        self.objectives.append(type)
                        objective_positions.append(pos)

    def add_person(self, waited):
        entry_posses = copy.copy(self.entry_pos)
        random.shuffle(entry_posses)
        entry_pos = entry_posses.pop(0)
        while any([isinstance(agent, Person) for agent in self.grid.get_cell_list_contents(entry_pos)]):
            if not entry_posses:
                if not waited:
                    person = self.create_person()
                    self.waiting_to_enter.append(person)
                    if self.print_bool:
                        print("added new person to waiting list")
                elif self.print_bool:
                    print("no entry for person from waiting list")
                return False #telling step() there is no entry available
            entry_pos = entry_posses.pop(0)
        
        if waited:
            person = self.waiting_to_enter.pop(0)
        else:
            person = self.create_person()

        self.grid.place_agent(person, entry_pos)
        self.persons.append(person)
        self.schedule.add(person)
        self.persons_instore.append(person)
        if self.print_bool:
            if waited: 
                print("placed new person from waiting list")
            else: 
                print("placed new person from arrival")
        return True


    def create_person(self):
        # obs_to_choose = list(self.objectives_dict.keys())
        obs_to_choose = copy.copy(self.objectives)
        if "exit" in obs_to_choose:
            obs_to_choose.remove("exit")
        if "entry" in obs_to_choose:
            obs_to_choose.remove("entry")
        n_obj = int(round(random.expovariate(1/self.n_objectives)))
        objectives = random.choices((obs_to_choose), k=n_obj) + ["exit"]
        speed = random.choices(self.speed_dist[0], weights=self.speed_dist[1])[0]
        familiar = round(random.choices(self.familiar_dist[0], weights=self.familiar_dist[1])[0], 3)
        vision = random.choices(self.vision_dist[0], weights=self.vision_dist[1])[0]
        person = Person(self.next_id(), random.choice(self.entry_pos), self, objectives=objectives, familiar=familiar, speed=speed, vision=vision)
        # print(f"arriving! chose speed: {speed}, familiar: {familiar} and vision: {vision}")
        return person

    def step(self):
        """
        Calls step method for each person
        """
        if self.current_step == 1:
            print(self.current_step)
        
        
        if self.current_step <= self.n_steps or self.persons_instore:
            if self.print_bool:
                to_arrive = len([a for a in self.arrival_times if a >= self.current_step])
                print(f"{self.current_step} || in store: {len(self.persons_instore)}, done: {self.n_done}, waiting: {len(self.waiting_to_enter)}, closes in: {self.n_steps-self.current_step}")
    
            self.datacollector.collect(self)
            self.interactions_per_step.append(0)
            self.standing_still = 0
            self.schedule.step()
            if self.current_step <= self.n_steps:
                if self.waiting_to_enter:
                    added = self.add_person(waited=True)
                    if not added and self.print_bool:
                        print("no place for new waiting person")
                    while added and self.waiting_to_enter:
                        added = self.add_person(waited=True)
                for i in range(self.arrival_times.count(self.current_step)):
                    self.add_person(waited=False)
        elif not self.already_done:
            self.already_done = True
            self.datacollector.collect(self)
            self.running = False
        else:
            self.running = False

        self.current_step += 1
    
    def calculate_weights(self, pos, vision):
        positions = [person.pos for person in self.persons_instore \
                    if np.sqrt((person.pos[0]-pos[0])**2 + (person.pos[1]-pos[1])**2) <= vision \
                    and pos != person.pos]
        weights = {}
        for edge in self.graph.edges():
            if edge[0] in positions or edge[1] in positions:
                weights[edge] = 5
            else:
                weights[edge] = 1
        nx.set_edge_attributes(self.graph, name="weight", values=weights)


    def run_model(self):
        """
        Runs the model for n_steps
        """
        print("model running...")
        while self.shop_open:
        # for i in range(self.n_steps):
            # if i in self.arrival_times:
            #     self.add_person()
            if self.current_step % 300 == 0:
                print(f"{self.current_step}")
            self.step()
            if not self.persons_instore and self.current_step > self.n_steps:
                if self.print_bool:
                    print("ended simulation as everyone was done and no arrivals were expected")
                self.shop_open = False

            # if not any([isinstance(agent, Person) for agent in self.schedule.agents]) and i > self.arrival_times[-1]:
        
        self.datacollector.collect(self)
        # print("collected last data")
        if self.log_bool:
            self.log()
        print("model done")
        return
    
    def calculate_density(self, subgrid):
        LO = subgrid[0] # Links onder
        RO = subgrid[1] # Rechts onder
        RB = subgrid[2] # Rechts boven
        LB = subgrid[3] # Links boven
        count_agents = 0
        count_obstacles = 0
        for x in range(LO[0], RO[0]+1):
            for y in range(LB[1], LO[1]+1):
                if (x, y) in [person.pos for person in self.persons]:
                    count_agents += 1
                if (x, y) in [obstacle.pos for obstacle in self.obstacles]:
                    count_obstacles += 1
        density = count_agents/abs(((RO[0]-LO[0])*(LB[1]-LO[1])-count_obstacles))
        return density

    def log(self):
        exp_number = 0
        while os.path.isdir(f"experiments/experiment_{exp_number}"):
            exp_number += 1
        os.mkdir(f"experiments/experiment_{exp_number}")
        with open(f"experiments/experiment_{exp_number}/config1.json", 'w') as f:
            json.dump(self.config, f)
        pd_data = copy.copy(self.datacollector.get_model_vars_dataframe())
        with open(f"experiments/experiment_{exp_number}/dataframe.pkl", "wb") as pickle_file:
            pkl.dump(pd_data, pickle_file)


        logdata = {"exp_number": exp_number}
        logdata.update(self.config)

        fieldnames = list(logdata.keys())
        with open("experiments_log.csv", "a") as f:

            writer_file = DictWriter(f, fieldnames=fieldnames)
            writer_file.writerow(logdata)


if __name__ == "__main__":

#     with open('config1.json', 'r') as f:
#         config = json.load(f)
    print("TODO")
    # model = GroceryModel(avg_arrival, speed, speed_prob)
    # model.run_model()