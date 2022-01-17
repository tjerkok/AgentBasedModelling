from mesa import Model
from mesa.datacollection import DataCollector
from mesa.space import SingleGrid
from mesa.time import RandomActivation
import networkx as nx
import json
import random

from agent import Person, Obstacle

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
        self.obstacles = []
        self.objectives = {}
        self.persons = []
        self.arrival_times = [0]
        self.entry_pos = (0,0)
        self.exit_pos = (0,0)
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
            "steps_in_stores": lambda m: [person.steps_instore for person in self.persons]
        })

        # placing obstacles, entry and exit
        self.read_grid()

        # datacollector requirements
        self.running = True
        self.datacollector.collect(self)

    def read_grid(self):
        """
        Create grid from grid_layout.txt
        """
        objective_positions = []
        with open(self.grid_layout, 'r') as f:
            lines = f.readlines()
            for line in lines[1:]:
                line = line.strip("\n").split(",")
                obs_type = line[0]
                pos = (int(line[1]), int(line[2]))
                
                if obs_type == "entry":
                    self.entry_pos = pos
                elif obs_type == "exit":
                    self.exit_pos = pos

                if obs_type == "wall":
                    obstacle = Obstacle(self.next_id(), pos, self, obstacle_type=obs_type)
                    self.obstacles.append(obstacle)
                    self.grid.place_agent(obstacle, pos)
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
        person = Person(self.next_id(), self.entry_pos, self, objectives=["bread", "chicken", "drinks", "exit"])
        if self.grid.is_cell_empty(self.entry_pos):
            self.grid.place_agent(person, self.entry_pos)
            self.persons.append(person)
            self.schedule.add(person)
        else:
            print("Could not enter!")

    def step(self):
        """
        Calls step method for each person
        """
        self.schedule.step()
        self.datacollector.collect(self)

    def run_model(self, n_steps=100):
        """
        Runs the model for n_steps
        """
        for i in range(self.n_steps):
            print(f"{i} | arrival_times: {self.arrival_times}")
            if i in self.arrival_times:
                print(f"arriving!")
                self.add_person()
            self.step()
            if self.schedule.get_agent_count() == 0 and i > self.arrival_times[-1]:
                return
    

if __name__ == "__main__":

    with open('config.json', 'r') as f:
        config = json.load(f)

    model = GroceryModel(config)
    model.run_model()