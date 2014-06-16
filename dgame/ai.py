# coding=utf-8
'''
The AI module will handle artificial intelligence needed for the game.

The a* part is copy from
http://www.pygame.org/project-AStar-195-.html
http://arainyday.se/projects/python/AStar/AStar_v1.1.tar.gz

Thanks for sharing!
'''

class Path:
    def __init__(self, nodes, totalCost):
        self.nodes = nodes;
        self.totalCost = totalCost;

    def get_nodes(self):
        return self.nodes

    def get_total_move_cost(self):
        return self.totalCost

class Node:
    def __init__(self, location, m_cost, lid, parent = None):
        self.location = location  # where is this node located
        self.m_cost = m_cost  # total move cost to reach this node
        self.parent = parent  # parent node
        self.score = 0  # calculated score for this node
        self.lid = lid  # set the location id - unique for each location in the map

    def __eq__(self, n):
        if n.lid == self.lid:
            return 1
        else:
            return 0

class AStar:

    def __init__(self, maphandler):
        self.mh = maphandler

    def _get_best_open_node(self):
        best_node = None
        for n in self.on:
            if not best_node:
                best_node = n
            else:
                if n.score <= best_node.score:
                    best_node = n
        return best_node

    def _trace_path(self, n):
        nodes = [];
        total_cost = n.m_cost;
        p = n.parent;
        nodes.insert(0, n);

        while 1:
            if p.parent is None:
                break

            nodes.insert(0, p)
            p = p.parent

        return Path(nodes, total_cost)

    def _handle_node(self, node, end):
        i = self.o.index(node.lid)
        self.on.pop(i)
        self.o.pop(i)
        self.c.append(node.lid)

        nodes = self.mh.get_adjacent_nodes(node, end)

        for n in nodes:
            if n.location == end:
                # reached the destination
                return n
            elif n.lid in self.c:
                # already in close, skip this
                continue
            elif n.lid in self.o:
                # already in open, check if better score
                i = self.o.index(n.lid)
                on = self.on[i];
                if n.m_cost < on.m_cost:
                    self.on.pop(i);
                    self.o.pop(i);
                    self.on.append(n);
                    self.o.append(n.lid);
            else:
                # new node, append to open list
                self.on.append(n);
                self.o.append(n.lid);

        return None

    def find_path(self, from_location, to_location):
        self.o = []
        self.on = []
        self.c = []

        end = to_location
        fnode = self.mh.get_node(from_location, True)
        self.on.append(fnode)
        self.o.append(fnode.lid)
        next_node = fnode

        while next_node is not None:
            finish = self._handle_node(next_node, end)
            if finish:
                return self._trace_path(finish)
            next_node = self._get_best_open_node()

        return None
