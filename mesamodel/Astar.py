from collections import deque


class Astar:
    def __init__(self, lis, height, width):
        self.lis = lis
        self.height = height
        self.width = width

    def get_neighbors(self, v):
        return self.lis[v]

    # Heuristic function making a dictoniary with all coordinates having equal values
    def h(self, n):
        H = {}
        for j in range(self.height):
            for i in range(self.width):
                H[f'{i}.{j}']=1
        return H[n]

    def a_star_algo(self, begin, end):
        open = set([begin])  # list of coordinates which have been visited but whose neighbours have not
        closed = set([])  # list of coordinates which have been visited including neighbours

        # dis_present has present distances from begin coordinate to all other coordinates, default is +inf
        dis_present = {}
        dis_present[begin] = 0

        # map contains an adjac mapping of all nodes
        map = {}
        map[begin] = begin

        while len(open) > 0:
            n = None

            # it will find a node with the lowest value of f()
            for v in open:
                if n == None or dis_present[v] + self.h(v) < dis_present[n] + self.h(n):
                    n = v

            if n == None:
                print('No route possible')
                return None

            # start over when current coordinate is end coordinate
            if n == end:
                route = []  # list of constructed route

                while map[n] != n:
                    route.append(n)
                    n = map[n]

                route.append(begin)

                route.reverse()

                print('Path found: {}'.format(route))
                return route

            # for all the neighbors of the coordinate execute the following:
            for (m, weight) in self.get_neighbors(n):
                # if the current coordinate is not present in both open and closed
                # add it to open and note n as it's map
                if m not in open and m not in closed:
                    open.add(m)
                    map[m] = n
                    dis_present[m] = dis_present[n] + weight

                # otherwise, check if it's quicker to first visit n, then m
                # and if it is, update map data and dis_present data
                # and if the node was in the closed, move it to open
                else:
                    if dis_present[m] > dis_present[n] + weight:
                        dis_present[m] = dis_present[n] + weight
                        map[m] = n

                        if m in closed:
                            closed.remove(m)
                            open.add(m)

            # remove n from the open, and add it to closed
            # because all of his neighbors were inspected
            open.remove(n)
            closed.add(n)

        print('Path does not exist!')
        return None


adjac_lis = {
    '0.0': [('1.0', 1), ('2.0', 1)],
    '1.0': [('3.0', 1)],
    '2.0': [('3.0', 1)]
}

graph1 = Astar(adjac_lis, 1, 4)
graph1.a_star_algo('0.0', '3.0')

