from mesa import Model
from mesa.datacollection import DataCollector
from mesa.space import Grid
from mesa.time import RandomActivation
import random

from .agent import Person, Obstacle

class OurModel(Model):
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
        self.persons = []
        self.arrival_times = [0]
        self.entry_pos = (0,0)
        self.exit_pos = (0,0)

        # scheduling Poisson distribution times of persons arriving
        for i in range(self.n_persons - 1):
            time = random.expovariate(1/self.avg_arrival)
            self.arrival_times.append(self.arrival_times[-1] + time)

        # schedule
        self.schedule = RandomActivation(self)

        # grid and datacollection
        self.grid = Grid(self.width, self.height, torus=False)
        self.datacollector = DataCollector({
            #TODO
        })

        # # creating persons
        # self.init_population(self.n_persons)

        # datacollector requirements
        self.running = True
        self.datacollector.collect(self)

    def read_grid(self):
        """
        Create grid from grid_layout.txt
        """
        with open(self.grid_layout, 'r') as f:
            lines = f.readlines()
            for line in lines[1:]:
                line = line.strip("\n").split(",")
                obs_type = line[0]
                pos = (int(line[1]), int(line[2]))
                obstacle = Obstacle(self.next_id(), pos, self, type=obs_type)
                self.grid.place_agent(obstacle, pos)
                self.obstacles.append(obstacle)
                if obs_type == "entry":
                    self.entry_pos = pos
                elif obs_type == "exit":
                    self.exit_pos = pos

    def init_population(self, n):
        """
        Creates population and places all on specific/random spot (not in use now)
        """
        for i in range(n):
            pos = (random.randrange(self.width), random.randrange(self.height))
            # specify speed? Moore? pos?
            person = Person(self.next_id(), pos, self, infected=False)
            self.grid.place_agent(person, pos)
            self.persons.append(person)
            self.schedule.add(person)

    def add_person(self):
        pos = (random.randrange(self.width), random.randrange(self.height))
        # specify speed? Moore? pos?
        person = Person(self.next_id(), pos, self, infected=False)
        self.grid.place_agent(person, pos)
        self.persons.append(person)
        self.schedule.add(person)

    def step(self):
        """
        Calls steph method for each person
        """
        self.schedule.step()

    def run_model(self, n_steps=100):
        """
        Runs the model for n_steps
        """
        for i in range(n_steps):
            if i in self.arrival_times:
                self.add_person()
            self.step()
    

if __name__ == "__main__":
    print("not ready")
