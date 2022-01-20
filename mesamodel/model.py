from multiprocessing.sharedctypes import Value
from tkinter.font import families
from mesa import Model
from mesa.datacollection import DataCollector
from mesa.space import SingleGrid, MultiGrid # TODO: do we need multi?
from mesa.time import RandomActivation
import networkx as nx
import json
import random
import regex as re

from .agent import Person, Obstacle

class GroceryModel(Model):
    def __init__(self, config):
        # attributes
        super().__init__()
        self.height = config["height"]
        self.width = config["width"]
        self.n_persons = config["n_persons"]
        self.n_items = config["n_items"]
        self.grid_layout = config["grid_layout"]
        self.avg_arrival = config["avg_arrival"]
        self.n_steps = config["n_steps"]
        self.speed_dist = config["speed_dist"]
        self.familiar_dist = config["familiar_dist"]
        self.grid_stepsize = config["grid_stepsize"]
        self.n_objectives = config["n_objectives"]
        self.list_subgrids = config["list_subgrids"]
        self.obstacles = []
        self.objectives = {}
        self.persons = []
        self.arrival_times = [0]
        self.current_step = 0
        self.entry_pos = []
        self.exit_pos = []
        self.graph = nx.grid_2d_graph(self.height, self.width)

        # scheduling Poisson distribution times of persons arriving
        for i in range(self.n_persons - 1):
            time = int(round(random.expovariate(1/self.avg_arrival)))
            self.arrival_times.append(self.arrival_times[-1] + time)

        # schedule
        self.schedule = RandomActivation(self)

        # grid and datacollection
        self.grid = SingleGrid(self.width, self.height, torus=False)
        self.datacollector = DataCollector({ #TODO
            "persons": lambda m: self.schedule.get_agent_count(),
            "person_locs": lambda m: [person.pos for person in self.persons],
            "steps_in_stores": lambda m: [person.steps_instore for person in self.persons],
            "speed": lambda m: [person.speed for person in self.persons],
            "familiar": lambda m: [person.familiar for person in self.persons],
            "densities": lambda m: [self.calculate_density(sub_grid) for sub_grid in self.list_subgrids]
        })

        # placing obstacles, entry and exit
        self.read_grid()

        # datacollector requirements
        self.running = True
        # self.datacollector.collect(self) # doing first collection in step()

    def read_grid(self):
        """
        Create grid from grid_layout.txt
        """
        gridsize = re.search(r"_\d+x\d+", self.grid_layout)[0]
        if int(gridsize[1:3]) != self.height or int(gridsize[1:3]) != self.width:
            print("width and height are not the same as layout.txt suggests!")
            raise ValueError
        objective_positions = []
        with open(self.grid_layout, 'r') as f:
            lines = f.readlines()
            for line in lines[1:]:
                line = line.strip("\n").split(",")
                obs_type = line[0]
                pos = (int(line[1]), int(line[2]))
                
                if obs_type == "entry":
                    self.entry_pos.append(pos)
                elif obs_type == "exit":
                    self.exit_pos.append(pos)

                if obs_type == "wall":
                    obstacle = Obstacle(self.next_id(), pos, self, obstacle_type=obs_type)
                    self.obstacles.append(obstacle)
                    self.grid.place_agent(obstacle, pos)
                    self.schedule.add(obstacle)
                    for n in list(self.graph.neighbors(pos)):
                        self.graph.remove_edge(pos, n)
                else:
                    # for n in list(self.graph.neighbors(pos)):
                    #     if n in objective_positions:
                    #         self.graph.remove_edge(n, pos)
                    
                    # TODO: Niet "objective" maar het soort objective?
                    self.graph.nodes[pos]["type"] = "objective"
                    if obs_type not in self.objectives.keys():
                        self.objectives[obs_type] = []
                    self.objectives[obs_type].append(pos)
                    objective_positions.append(pos)


    def add_person(self):
        # specify speed? Moore? pos?
        objectives = random.choices(list(self.objectives.keys()), k=self.n_objectives)+ ["exit"]
        speed = random.choices(self.speed_dist[0], weights=self.speed_dist[1])[0]
        familiar = round(random.choices(self.familiar_dist[0], weights=self.familiar_dist[1])[0], 3)
        entry_pos = random.choice(self.entry_pos)
        print(f"chose speed: {speed} and familiar: {familiar}")
        person = Person(self.next_id(), entry_pos, self, objectives=objectives, familiar=familiar, speed=speed)
        if self.grid.is_cell_empty(entry_pos):
            self.grid.place_agent(person, entry_pos)
            self.persons.append(person)
            self.schedule.add(person)
        else:
            print("Could not enter!")

    def step(self):
        """
        Calls step method for each person
        """

        self.current_step += 1
        if self.current_step in self.arrival_times:
            print(f"arriving!")
            self.add_person()

        self.datacollector.collect(self)
        self.schedule.step()
        # self.datacollector.collect(self)

    def run_model(self, n_steps=100):
        """
        Runs the model for n_steps
        """
        for i in range(self.n_steps):
            # if i in self.arrival_times:
            #     self.add_person()
            self.step()
            if self.schedule.get_agent_count() == 0 and i > self.arrival_times[-1]:
                self.datacollector.collect(self)
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





if __name__ == "__main__":

    with open('config.json', 'r') as f:
        config = json.load(f)

    model = GroceryModel(config)
    model.run_model()