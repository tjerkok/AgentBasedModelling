from mesa import Model
from mesa.datacollection import DataCollector
from mesa.space import MultiGrid 
from mesa.time import RandomActivation
import networkx as nx
import numpy as np
import json
import random
import copy

from agent import Person, Obstacle, Objective

class GroceryModel(Model):
    """
    A class to represent the Grocery Model based on the Mesa Model instance.

    Attributes
    ----------
    all attributes from the Mesa Model instance
    config : dict
        dictionary of the parameters used:
            height : int
                height of the grid
            width : int
                width of the model
            n_persons : int
                amount of persons
            n_items : int
                average amount of items in the objective list
            grid_layout : string
                string of the grid txt file
            avg_arrival : float/int
                average arrival time for the Poisson process
            n_steps : int
                amount of steps at which the store is closed
            speed1 : int
                speed1 of the persons
            speed2 : int
                speed2 of the persons
            speed1_prob : float
                probability of speed1
            speed2_prob : float
                probability of speed2
            speed_dist : tuple of lists
                tuple of lists with speeds and probabilities
            familiar1 : float
                familiar1 of the persons
            familiar2 : float
                familiar2 of the persons
            familiar1_prob : float
                probability of familiar1
            familiar2_prob : float
                probability of familiar2
            familiar_dist : tuple of lists
                tuple of lists with speeds and probabilities
            vision1 : float
                vision1 of the persons
            vision2 : float
                vision2 of the persons
            vision1_prob : float
                probability of vision1
            vision2_prob : float
                probability of vision2
            vision_dist : tuple of lists
                tuple of lists with speeds and probabilities
            grid_stepsize : float
                size of one block in the grid
            n_objectives : int
                average amount of items in the objective list
    obstacles : list
        list of obstacle instances in the model
    objectives_dict : dict
        dictionary with objective types as keys and locations as values
    objectives : list
        list of objective types
    persons : list
        all persons instances in model
    persons_instore : list
        list of persons in the store
    n_done : int
        amount of persons done shopping
    done : list
        list of persons done shopping
    arrival_times : list
        list of arrival times
    current_step : int
        number of current step
    entry_pos : list of tuples
        list with positions (x,y) of entries
    exit_pos : list of tuples
        list with positions (x,y) of exits
    n_interactions : list
        list of amount of interactions of persons done shopping
    interactions_per_step : list
        amount of interactions per step
    blocked_moves : dict
        dictionary of blocked moves as values with person as key
    standing_still : int
        total amount of times people didn't move
    waiting_to_enter : list
        list of people waiting to enter due to occupied entry
    graph : networkx graph
        graph used for calculating astar route
    print_bool : bool
        True to print everything happening in model
    shop_open : bool
        True for current step lower than n_steps, if False, no one can enter
    schedule : Mesa Scheduler
        Mesa Scheduler to use every step
    grid : Mesa Grid
        Mesa Grid used to place agents
    datacollector : Mesa Datacollector
        Mesa Datacollector used to collect data
    running : bool
        True if model is running. Used for Mesa Server.

    Methods
    -------
    count_mean_interactions():
        returns the mean interactions per person done shopping.
    count_mean_steps():
        returns the mean steps per person done shopping.
    count_mean_distance():
        returns the mean distance per person done shopping
    read_grid():
        Fills the Grid, Model, Scheduler and graph from the text file
    add_person(waited : bool):
        Adds person to the grid, checks if person came from waiting list by waited
        bool.
    create_person():
        Creates person, choosing its attributes random.
    step():
        Function for every time step, checks if store is still open and when to 
        add a new person.
    calculate_weights(pos : tuple, vision : int):
        Gives all edges in the graph on a distance of vision from position pos a
        weight.
    run_model():
        Function to run model while store open.

    """
    def __init__(self, config, print_bool=True):
        """
        Constructs all the necessary attributes for the Model object. 

        Reads grid and finds arrival times.

        Parameters
        ----------
            config : dict
                dictonairy with complete configuration
        """

        super().__init__()
        self.config = config
        self.height = config["height"]
        self.width = config["width"]
        self.n_persons = int(config["n_persons"])
        self.n_items = int(config["n_items"])
        self.grid_layout = config["grid_layout"]
        self.avg_arrival = config["avg_arrival"]
        self.n_steps = int(config["n_steps"])
        
        self.speed1 = int(config["speed1"])
        self.speed2 = int(config["speed2"])
        self.speed2_prob = config["speed2_prob"]
        self.speed1_prob = 1 - self.speed2_prob
        self.speed_dist = [
            [self.speed1, self.speed2], 
            [self.speed1_prob, self.speed2_prob]
        ]
        
        self.familiar1 = config["familiar1"]
        self.familiar2 = config["familiar2"]
        self.familiar2_prob = config["familiar2_prob"]
        self.familiar1_prob = 1 - self.familiar2_prob
        self.familiar_dist = [
            [self.familiar1, self.familiar2],
            [self.familiar1_prob, self.familiar2_prob]
        ]

        self.vision1 = int(config["vision1"])
        self.vision2 = int(config["vision2"])
        self.vision2_prob = config["vision2_prob"]
        self.vision1_prob = 1 - self.vision2_prob
        self.vision_dist = [
            [self.vision1, self.vision2], 
            [self.vision1_prob, self.vision2_prob]
        ]

        self.grid_stepsize = config["grid_stepsize"]
        self.n_objectives = int(config["n_objectives"])
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
        self.n_interactions = []
        self.interactions_per_step = [0]
        self.blocked_moves = {}
        self.standing_still = 0
        self.waiting_to_enter = []
        self.graph = nx.grid_2d_graph(self.height, self.width)
        self.print_bool = print_bool
        self.shop_open = True

        # scheduling Poisson distribution times of persons arriving
        for i in range(self.n_persons - 1):
            time = int(round(random.expovariate(1/self.avg_arrival)))
            self.arrival_times.append(self.arrival_times[-1] + time) 

        self.schedule = RandomActivation(self)

        # grid and datacollection
        self.grid = MultiGrid(self.width, self.height, torus=False)
        self.datacollector = DataCollector({ #TODO
            "waiting_to_enter": lambda m: len(self.waiting_to_enter),
            "standing_still": lambda m: self.standing_still,
            "n_persons": lambda m: len([agent for agent in self.schedule.agents 
                                        if isinstance(agent, Person)]),
            "n_done": lambda m: self.n_done,
            "persons": lambda m: [agent for agent in self.schedule.agents 
                                        if isinstance(agent, Person)], 
            "person_locs": lambda m: [person.pos for person in self.persons],
            "mean_steps ": lambda m: [person.steps_instore for person in self.persons],
            "speed": lambda m: [person.speed for person in self.persons],
            "familiar": lambda m: [person.familiar for person in self.persons],
            "mean_interactions_done": lambda m: self.count_mean_interactions(),
            "interactions": lambda m: self.interactions_per_step[-1],
            "total_switches": lambda m: sum([person.n_switches for 
                                             person in self.persons]),
            "mean_steps_done": lambda m: self.count_mean_steps(),
            "mean_distance_done": lambda m: self.count_mean_distance()
        })

        # placing obstacles, entry and exit
        self.read_grid()

        # datacollector requirement
        self.running = True

    def count_mean_interactions(self):
        """
        Counts mean interactions of all persons done shopping.

        Returns
        -------
        mean interactions : float
        """
        interactions = [person.int_rate for person in self.done]
        if interactions:
            return np.mean(interactions)
        else:
            return 0

    def count_mean_steps(self):
        """
        Counts mean steps of all persons done shopping.

        Returns
        -------
        mean steps : float
        """
        steps = [person.steps_instore for person in self.done]
        if steps:
            return np.mean(steps)
        else:
            return 0
        
    def count_mean_distance(self):
        """
        Counts mean distance of all persons done shopping.

        Returns
        -------
        mean distance : float
        """
        distances = [person.distance for person in self.done]
        if distances:
            return np.mean(distances)
        else:
            return 0

    def read_grid(self):
        """
        Reads grid text file and creates agents.

        The grid text file is read line by line, adding all agents to the grid,
        model, schedule and graph.

        Returns
        -------
        None
        """
        
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
                        obstacle = Obstacle(
                            self.next_id(), pos, self, obstacle_type=type
                        )
                        self.obstacles.append(obstacle)
                        self.grid.place_agent(obstacle, pos)
                        self.schedule.add(obstacle)
                        for n in list(self.graph.neighbors(pos)):
                            # isolating the obstacles in the graph
                            self.graph.remove_edge(pos, n)
                    else:
                        objective = Objective(
                            self.next_id(), pos, self, objective_type=type
                        )
                        self.grid.place_agent(objective, pos)
                        self.schedule.add(objective)
                        if type not in self.objectives_dict.keys():
                            self.objectives_dict[type] = []
                        self.objectives_dict[type].append(pos)
                        self.objectives.append(type)
                        objective_positions.append(pos)

    def add_person(self, waited):
        """
        Adds a person to the model, grid, schedule and graph.

        If the person waited, it is popped from the waiting list, otherwise a new
        person is created. If all entry positions are occupied, the person is
        added back to the waiting list. 

        Parameters
        ----------
            waited : bool
                True if the added person is on the waiting list.

        Returns
        -------
        True if person is added
        False if entries are occupied and person is added to waiting list
        """
        entry_posses = copy.copy(self.entry_pos)
        random.shuffle(entry_posses)
        entry_pos = entry_posses.pop(0)
        while any([isinstance(agent, Person) 
                   for agent in self.grid.get_cell_list_contents(entry_pos)]):
            if not entry_posses:
                if not waited:
                    person = self.create_person()
                    self.waiting_to_enter.append(person)
                    if self.print_bool:
                        print("added new person to waiting list")
                elif self.print_bool:
                    print("no entry for person from waiting list")
                return False 

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
        """
        Creates a person with random attributes.

        Returns
        -------
        person : Person instance
        """
        obs_to_choose = copy.copy(self.objectives)
        if "exit" in obs_to_choose:
            obs_to_choose.remove("exit")
        if "entry" in obs_to_choose:
            obs_to_choose.remove("entry")
        n_obj = int(round(random.expovariate(1/self.n_objectives)))
        objectives = random.choices((obs_to_choose), k=n_obj) + ["exit"]
        speed = random.choices(self.speed_dist[0], weights=self.speed_dist[1])[0]
        familiar = round(
            random.choices(self.familiar_dist[0], weights=self.familiar_dist[1])[0],
            3
        )
        vision = random.choices(self.vision_dist[0], weights=self.vision_dist[1])[0]
        person = Person(
            self.next_id(), random.choice(self.entry_pos), self, 
            objectives=objectives, familiar=familiar, speed=speed, vision=vision
        )
        return person

    def step(self):
        """
        Collects data to datacollector, runs a step for every scheduled agent and
        checks if store is still open.

        If someone is on the waiting list, this person is placed first. Then for 
        every arrival time someone is added. 

        Returns
        -------
        None
        """
        if self.print_bool:
            print(f"{self.current_step} || in store: {len(self.persons_instore)}"\
                  f", done: {self.n_done}, waiting: {len(self.waiting_to_enter)}")

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
        self.current_step += 1
    
    def calculate_weights(self, pos, vision):
        """
        Calculates weights of the edges in the graph model for all persons within
        the range of vision from position pos (x,y). 

        Parameters
        ----------
            pos : tuple
                position (x,y) from where to calculate weights
            vision : int
                the range where edges are weighted

        Returns
        -------
        None
        """
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
        Starts running the model while the store is open.

        If the store is empty and the current step is higher than the maximum
        n_steps, the shop is closed.

        Returns
        -------
        None
        """
        print("model running...")
        while self.shop_open:
            if self.current_step % 300 == 0:
                print(f"{self.current_step}")
            self.step()
            if not self.persons_instore and self.current_step > self.n_steps:
                if self.print_bool:
                    print("ended simulation as everyone was done"\
                    "and no arrivals were expected")
                self.shop_open = False
        
        self.datacollector.collect(self)
        print("model done")
        return


if __name__ == "__main__":

    with open('config1.json', 'r') as f:
        config = json.load(f)

    model = GroceryModel(config)
    model.run_model()