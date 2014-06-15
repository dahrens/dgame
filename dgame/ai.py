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

    def getNodes(self):
        return self.nodes

    def getTotalMoveCost(self):
        return self.totalCost

class Node:
    def __init__(self, location, mCost, lid, parent = None):
        self.location = location  # where is this node located
        self.mCost = mCost  # total move cost to reach this node
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

    def _getBestOpenNode(self):
        bestNode = None
        for n in self.on:
            if not bestNode:
                bestNode = n
            else:
                if n.score <= bestNode.score:
                    bestNode = n
        return bestNode

    def _tracePath(self, n):
        nodes = [];
        totalCost = n.mCost;
        p = n.parent;
        nodes.insert(0, n);

        while 1:
            if p.parent is None:
                break

            nodes.insert(0, p)
            p = p.parent

        return Path(nodes, totalCost)

    def _handleNode(self, node, end):
        i = self.o.index(node.lid)
        self.on.pop(i)
        self.o.pop(i)
        self.c.append(node.lid)

        nodes = self.mh.getAdjacentNodes(node, end)

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
                if n.mCost < on.mCost:
                    self.on.pop(i);
                    self.o.pop(i);
                    self.on.append(n);
                    self.o.append(n.lid);
            else:
                # new node, append to open list
                self.on.append(n);
                self.o.append(n.lid);

        return None

    def findPath(self, fromlocation, tolocation):
        self.o = []
        self.on = []
        self.c = []

        end = tolocation
        fnode = self.mh.getNode(fromlocation, True)
        self.on.append(fnode)
        self.o.append(fnode.lid)
        nextNode = fnode

        while nextNode is not None:
            finish = self._handleNode(nextNode, end)
            if finish:
                return self._tracePath(finish)
            nextNode = self._getBestOpenNode()

        return None
