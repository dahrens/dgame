# coding=utf-8
import random, logging

SMALL_ROOM = [(5, 5), (9, 9)]
MEDIUM_ROOM = [(10, 10), (15, 15)]
LARGE_ROOM = [(16, 16), (20, 20)]

class MapGenerator(object):

    def __init__(self, seed = None):
        if seed:
            random.seed(seed)

    def create(self, m):
        self.map = m
        logging.debug('generated maps tiles len: {}/{}'.format(len(self.map.tiles), len(self.map.tiles[0])))
        self.open_pos = self._get_pos_set((1, 1), (self.map.size_in_tiles[0] - 2, self.map.size_in_tiles[1] - 2))
        self.close_pos = set()
        logging.debug('open_pos/close_pos: {}/{} {}/{}'.format(len(self.open_pos), len(self.close_pos), self.open_pos, self.close_pos))
        self.rooms = []
        for _ in range(10):
            room_positions = self.gen_room(MEDIUM_ROOM)
            if room_positions:
                self.rooms.append(room_positions)
            else:
                logging.warning('can not find suitable place for another room.')
        self.map.update()
        return self.map

    def gen_room(self, size_template = MEDIUM_ROOM):
        size = (random.randrange(size_template[0][0], size_template[1][0]),
                random.randrange(size_template[0][1], size_template[1][1]))
        logging.debug('generate room with size: {}'.format(size))
        for i in range(1000):
            start_pos = self._get_free_pos()
            logging.debug('generate room at : {}'.format(start_pos))
            room_pos = self._get_pos_set(start_pos, size)
            if room_pos <= self.open_pos:
                self._close_position(room_pos)
                break
            if i == 999:
                return False
        logging.debug('generate room at {} with size {}'.format(start_pos, size))
        for x, y in room_pos:
            logging.debug('writing tile {}/{}'.format(x, y))
            if x == start_pos[0] or y == start_pos[1] or x == start_pos[0] + size[0] - 1 or y == start_pos[1] + size[1] - 1:
                self.map.tiles[x][y].image = self.map.biome.wall
            else:
                self.map.tiles[x][y].image = self.map.biome.passable
            self.map.tiles[x][y].dirty = 1
        return room_pos


    def _get_pos_set(self, start_pos, size):
        s = set()
        logging.debug('get_pos_set at {} with size {}'.format(start_pos, size))
        for x in range(start_pos[0], start_pos[0] + size[0]):
            for y in range(start_pos[1], start_pos[1] + size[1]):
                s.add((x, y))
        return s

    def _close_position(self, pos_set):
        logging.debug('mark them close: {} {}'.format(len(pos_set), pos_set))
        self.open_pos -= pos_set
        self.close_pos = self.close_pos | pos_set
        logging.debug('open_pos/close_pos: {}/{} {}/{}'.format(len(self.open_pos), len(self.close_pos), self.open_pos, self.close_pos))

    def _get_free_pos(self):
        return random.sample(self.open_pos, 1)[0]
