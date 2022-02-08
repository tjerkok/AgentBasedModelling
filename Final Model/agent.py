from mesa import Agent
import numpy as np
import random
import networkx as nx

class Person(Agent):
    """
    A class to represent a Person.

    ...

    Attributes
    ----------
    person_id : int
        unique id of the person
    pos : tuple
        the position (x,y) of the person 
    objectives : list
        list of objectives of the person
    familiar : float
        float representing the familiarity of the person
    objectives_inc_coord : list of tuples
        list with objectives with tuple of objective name and position
    current_objective : tuple
        current objective with tuple of (name, position)
    model : Model instance
        parent modelof the person
    speed : int
        integer representing the speed of the person
    moore : bool
        True if diagonal steps are included for moves and neighbors check
    basket : list
        list of achieved objectives
    route : list
        list of positions the person has had
    steps_instore : int
        amount of steps the person is in the store
    int_rate : int
        list of amount of interactions the person has in the store per step
    people_bumped_into : list
        list of persons the person had interactions with
    tot_cont : int
        list of total interactions the person has in the store
    vision : int
        amount of steps the person can see forward to base route on
    n_switches : int
        amount of switches the person has done
    distance : int
        amount of steps the person has set

    Methods
    -------
    get_objectives_coord():
        Fills objectives_inc_coord with the objective and random chosen tile for 
        that objective.
    sort_objectives():
        Sorts the objectives based on distance from entry.
    next_objective():
        Pops the first objective from the list.
    step():
        Everything a person can do once in a timestep of the model.
    reached_objectives():
        Removes objective and takes next, checks if the person is done.
    check_interactions():
        Checks if a person has interactions in its current position.
    check_move(moves : list, astar=False):
        Returns the legal moves of a list of potential moves. Remembers blocked 
        move if astar.
    switch_places_check(blocking_person : Person, move : tuple, legal : list, astar : bool):
        Checks if the person can switch with a person who's blocked move is 
        remembered, if possible
        the move is added to the legal moves. Remembers blocked move if astar.
    find_route():
        Chooses to do an astar or random move.
    dist(a : tuple, b : tuple):
        Calculates the distance from a to b in a straight line.
    astar_move():
        Calculates the route with the astar algorithm, using vision to calculate 
        weights.
    random_move():
        Returns a route of random moves. 
    """

    def __init__(self, unique_id, pos, model, objectives, familiar, 
                 moore=False, speed=1, vision=1):
        """
        Constructs all the necessary attributes for the Person object and sorts 
        objectives.

        Parameters
        ----------
            unique_id : int
                the unique id of the agent in the model
            pos : tuple
                tuple of the persons starting position (x,y)
            model : Model instance
                model in which the person is added
            objectives : list
                list of objectives names of the person
            familiar : float
                familiarity of the person
            moore : bool
                bool to use for diagonal moves or neighbor checks
            speed : int
                speed of the person
            vision : vision
                vision of the person
        """
        super().__init__(unique_id, model)
        self.person_id = len(self.model.persons) + 1
        self.pos = pos
        self.objectives = objectives
        self.familiar = familiar
        self.objectives_inc_coord = []
        self.get_objectives_coord()
        self.sort_objectives()
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
        self.distance = 0


    def get_objectives_coord(self):
        """
        Fills the objectives_inc_coord with the position of a random chosen tile of
        corresponding objective.
        
        Returns
        -------
        None
        """
        for next_objective in self.objectives:
            self.objectives_inc_coord.append((
                next_objective, random.choice(self.model.objectives_dict[next_objective])
            ))


    def sort_objectives(self):
        """
        Sorts the objectives in objectives_inc_coord by shortest astar path from
        current position.

        Returns
        -------
        None
        """
        self.temp_object = []
        for obj in self.objectives_inc_coord[:-1]:
            self.temp_object.append((
                obj[0], obj[1], 
                len(nx.astar_path(self.model.graph, 
                                  self.pos, obj[1], 
                                  heuristic=self.dist))-1
            ))

        x = lambda index: index[2]
        self.temp_object.sort(key=x)
        self.new_objectives = []
        for obj in self.temp_object:
            self.new_objectives.append((obj[0], obj[1]))
        self.new_objectives.append(('exit', self.model.objectives_dict['exit'][0]))


    def next_objective(self):
        """
        Pops next objective from objectives list and sets it as current.

        Returns
        -------
        None
        """
        self.current_objective = self.new_objectives.pop(0)  # when sorting list

    def step(self):
        """
        Step function used by the model scheduler. 

        The person removes its remembered blocked move. It then searches for its
        next moves and checks which are legal. If no legal moves are found, there
        is a 50% chance of the person doing a random move. If that move fails, it
        waits a turn. The legal moves are done and interactions are checked per 
        move. The person gains familiarity with the store and checks if the 
        objective is reached. The current position is added to route. 

        Returns
        -------
        None
        """
        # finds next steps
        self.model.blocked_moves.pop(self, False)
        next_moves = self.find_route()
        legal_moves = self.check_move(next_moves, astar=True)
        if not legal_moves:
            if random.random() < 0.5:
                next_moves = self.random_move()
                legal_moves = self.check_move([next_moves[0]])
                if legal_moves:
                    legal_moves = legal_moves
            else:
                legal_moves = []

        # makes moves
        if not legal_moves:
            self.model.standing_still += 1
        for move in legal_moves:
            if move != self.pos:
                self.check_interactions(move)
                self.distance += 1
                self.model.grid.move_agent(self, move)
        self.steps_instore += 1

        # adds familiarity
        if self.familiar < 1.0:
            self.familiar = round(self.familiar + 0.01, 2)
        
        # checks if and which objective is reached
        if self.pos == self.current_objective[1]:
            if self.reached_objective():
                return
        
        self.route.append(self.pos)

    
    def reached_objective(self):
        """
        Checks what objective the person has found.

        If the objective is the exit, the person is removed from the grid and 
        scheduler. If the objective is not the exit, the next objective is taken
        from its objectives list.

        Returns
        -------
        True if reached exit
        False else
        """
        if self.current_objective[0] == "exit":
            if self.model.print_bool:
                print(f"{self} is done shopping, removing...")
            self.model.schedule.remove(self)
            self.model.grid.remove_agent(self)
            self.model.n_done += 1
            self.model.n_interactions.append(self.int_rate)
            self.model.persons_instore.remove(self)
            self.model.done.append(self)
            return True

        else:
            self.basket.append(self.current_objective[0])
            self.next_objective()
            return False

    def check_interactions(self,move):
        """
        Checks for interactions on position/move.

        Parameters
        ----------
            move : tuple
                tuple of position (x,y) from which to check

        Returns
        -------
        None
        """
        for agent in self.model.grid.get_neighbors(move, moore=self.moore, radius=2, 
                                                   include_center=False):
            if isinstance(agent,Person) == True and agent != self:
                self.tot_cont =+ 1
                self.model.interactions_per_step[-1] += 1
                if agent.unique_id not in self.people_bumped_into:
                    self.people_bumped_into.append(agent.unique_id)
                    self.int_rate = int(len(self.people_bumped_into))

    def check_move(self, moves, astar=False):
        """
        Checks for all moves which of them are legal.

        If the move is blocked by another person and the move is an astar move, 
        the move is remembered. 

        Parameters
        ----------
            moves : list
                list of positions (x,y) to check
            astar : bool
                True if moves are astar moves

        Returns
        -------
        legal moves : list
        """
        legal = []
        for move in moves:
            if self.model.grid.out_of_bounds(move):
                return legal
            else:
                blocking_person = [agent for agent in self.model.grid.get_cell_list_contents(move) 
                                   if isinstance(agent, Person)]
                dest_obstacles = [agent for agent in self.model.grid.get_cell_list_contents(move) 
                                   if isinstance(agent, Obstacle)]
                if blocking_person or dest_obstacles:
                    if blocking_person:
                        legal = self.switch_places_check(blocking_person, move, legal, astar)    
                    return legal
                else: 
                    legal.append(move)
        return legal

    def switch_places_check(self, blocking_person, move, legal, astar):
        """
        Checks if the blocking person wants to switch.

        If the blocking persons move is to the position of this person instance,
        the persons are switching. If the attempted move is astar, it will be 
        remembered. 

        Parameters
        ----------
            blocking_person : list
                list of blocking person instances
            move : tuple
                tuple of the move (x,y)
            legal : list
                list of legal moves to append switch to if possible
            astar : bool
                True if moves are astar moves

        Returns
        -------
        legal moves : list
        """
        blocking_person = blocking_person[0]
        if blocking_person in self.model.blocked_moves.keys():
            try:
                if self.model.blocked_moves[blocking_person] == legal[-1]:
                    self.model.grid.move_agent(blocking_person, legal[-1])
                    legal.append(move)
                    self.n_switches += 1
            except IndexError:
                if self.model.blocked_moves[blocking_person] == self.pos:
                    self.model.grid.move_agent(blocking_person, self.pos)
                    legal = [move]
                    self.n_switches += 1                    
            self.model.blocked_moves.pop(blocking_person, False)
        elif astar:
            self.model.blocked_moves[self] = move
        return legal

    def find_route(self):
        """
        Finds the next route.

        Astar moves if uniform random number is lower than the familiarity of the
        person. Otherwise random moves.

        Returns
        -------
        found moves : list
        """
        if np.random.uniform(0,1) <= self.familiar: 
            moves = self.astar_move()
        else:
            moves = self.random_move()
        return moves


    def dist(self, a, b):
        """
        Calculates distance in straight line from a to b.

        Parameters
        ----------
            a : tuple
                position a (x,y)
            b : tuple
                position b (x,y)
        
        Returns
        -------
        distance : float
        """
        (x1, y1) = a
        (x2, y2) = b
        return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5


    def astar_move(self):
        """
        Finds astar path to current objective.

        Calculates weights in the network graph dependent of person's vision and
        finds path to current objective.

        Returns
        -------
        route : list
        """
        self.model.calculate_weights(self.pos, self.vision)
        route = nx.astar_path(self.model.graph, self.pos, self.current_objective[1], 
                              heuristic=self.dist, weight="weight")
        return route[1:self.speed+1]


    def random_move(self):
        """
        Finds random moves.

        Returns
        -------
        route : list
        """
        x, y = self.pos
        moves = []
        for i in range(self.speed):
            moves.append(random.choice([(x+1, y), (x-1, y), (x, y+1), (x, y-1)]))
            x, y = moves[-1]
        return moves

    def __repr__(self):
        return f"Person {self.person_id}"
    

class Obstacle(Agent):
    """
    A class to represent an obstacle.


    Attributes
    ----------
    all attributes from Agent object
    obstacle_type : string
        string representing obstacle type
    pos : tuple
        tuple of position of obstacle (x,y)

    Methods
    -------
    step():
        function needed for scheduler.
    """
    def __init__(self, next_id, model, pos, obstacle_type):
        super().__init__(next_id, model)
        self.obstacle_type = obstacle_type
        self.pos = pos
        
    def __repr__(self):
        return f"Obstacle {self.obstacle_type} {self.unique_id} at {self.pos}"

    def step(self):
        pass


class Objective(Agent):
    """
    A class to represent an objective.


    Attributes
    ----------
    all attributes from Agent object
    objective_type : string
        string representing objective type
    pos : tuple
        tuple of position of objective (x,y)

    Methods
    -------
    step():
        function needed for scheduler.
    """
    def __init__(self, next_id, model, pos, objective_type):
        super().__init__(next_id, model)
        self.objective_type = objective_type
        self.pos = pos
        
    def __repr__(self):
        return f"{self.objective_type} {self.unique_id} at {self.pos}"

    def step(self):
        pass